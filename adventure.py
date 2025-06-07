from typing import Annotated, TypedDict, Dict

from langgraph.graph import StateGraph
from langgraph.graph.message import add_messages
from langgraph.prebuilt import ToolNode, InjectedState, tools_condition
from langgraph.checkpoint.memory import MemorySaver
from langgraph.types import Command, interrupt
from langchain.tools import tool
from langchain_core.tools import InjectedToolCallId
from langchain_core.messages import ToolMessage, RemoveMessage
from langgraph.graph.message import REMOVE_ALL_MESSAGES

import core

# Simple room "database"
ROOMS: Dict[str, Dict] = {
    "hall": {
        "description": (
            "A dimly lit hallway with rough stone walls. Faintly glowing torches "
            "cast long shadows across the cracked floor, and cobwebs hang in the "
            "corners. Ancient portraits, nearly faded to nothing, line the walls "
            "with ghostly faces. A heavy oak door, its iron handle worn smooth, "
            "leads east."
        ),
        "exits": {"east": "kitchen"},
    },
    "kitchen": {
        "description": (
            "Dusty pots hang from the ceiling above a scarred wooden table. "
            "A large stone hearth dominates one side, still carrying the faint "
            "smell of old herbs and smoke. Rusty utensils litter the counters, "
            "and a grimy window barely lets in any light. An archway to the "
            "west returns to the hallway."
        ),
        "exits": {"west": "hall"},
    },
}


class GameState(TypedDict):
    messages: Annotated[list, add_messages]
    current_room: str
    need_summary: bool


graph_builder = StateGraph(GameState)


# ----------------------------- nodes -----------------------------


def summarize_room(state: GameState):
    """Return a short narration of the current room."""
    room = ROOMS[state["current_room"]]
    prompt = [
        {
            "role": "system",
            "content": (
                "You are a text adventure narrator. Briefly summarize the room."
            ),
        },
        {"role": "user", "content": room["description"]},
    ]
    resp = core.llm.invoke(prompt)
    return {"messages": [resp], "need_summary": False}


def ask_for_action(state: GameState):
    """Prompt the player for their next action using a human interrupt."""
    action = interrupt("> ")
    # The terminal already displays the prompt, so the LLM doesn't need to ask
    # a question. Simply return the player's response to continue the
    # conversation.
    return {"messages": [{"role": "user", "content": action}]}


@tool
def move_room(
    direction: str,
    state: Annotated[GameState, InjectedState],
    tool_call_id: Annotated[str, InjectedToolCallId],
) -> Command:
    """Move to an adjacent room in the given direction."""
    exits = ROOMS[state["current_room"]]["exits"]

    # Normalize the direction to handle case variations like "East" vs "east"
    norm_direction = direction.lower()

    if norm_direction not in exits:
        return ToolMessage(
            "INVALID_DIRECTION",
            tool_call_id=tool_call_id,
            name="move_room",
        )

    new_room = exits[norm_direction]
    state["current_room"] = new_room
    # Inform the LLM of success without directly narrating
    msg = ToolMessage(
        "MOVED",
        tool_call_id=tool_call_id,
        name="move_room",
    )
    # Clear previous messages so the model doesn't see old context
    clear = RemoveMessage(id=REMOVE_ALL_MESSAGES)
    return Command(
        update={
            "current_room": new_room,
            "messages": [clear, msg],
            "need_summary": True,
        }
    )


llm_with_tools = core.llm.bind_tools([move_room])


def interpret_action(state: GameState):
    """Use the LLM to respond to the player and call tools if needed."""
    # The conversation history already captures the prior context, so we
    # simply pass the stored messages directly to the model. Adding a
    # system prompt on every invocation causes the model to echo the user
    # input, so it has been removed.
    resp = llm_with_tools.invoke(state["messages"])
    return {"messages": [resp]}


# ---------------------------- edges ------------------------------

graph_builder.add_node("summarize", summarize_room)

graph_builder.add_node("ask", ask_for_action)

graph_builder.add_node("interpret", interpret_action)
graph_builder.add_node("tools", ToolNode([move_room]))

graph_builder.add_edge("summarize", "ask")
graph_builder.add_edge("ask", "interpret")

graph_builder.add_conditional_edges(
    "tools",
    lambda state: "summarize" if state.get("need_summary") else "interpret",
    {"summarize": "summarize", "interpret": "interpret"},
)


def router(state: GameState):
    """Route after interpretation based on tool calls and narration flag."""
    if tools_condition(state) == "tools":
        return "tools"
    return "summarize" if state.get("need_summary") else "ask"


graph_builder.add_conditional_edges(
    "interpret",
    router,
    {"tools": "tools", "summarize": "summarize", "ask": "ask"},
)

graph_builder.set_entry_point("summarize")

graph = graph_builder.compile(checkpointer=MemorySaver())


# import pathlib
#
# # Save the graph image to a file
# try:
#     output_path = pathlib.Path("graph.png")
#     png_bytes = graph.get_graph().draw_mermaid_png()
#     output_path.write_bytes(png_bytes)
#     print(f"Graph image saved to {output_path.resolve()}")
# except Exception as e:
#     print(f"❌ Failed to generate graph image: {e}")


# Simple helper to play the game from a script


def play(start_room: str = "hall"):
    """Simple interactive loop for the adventure game."""
    import uuid

    state: GameState = {
        "current_room": start_room,
        "messages": [],
        "need_summary": False,
    }
    config = {"configurable": {"thread_id": str(uuid.uuid4())}}
    command: Command | dict = state
    prev_len = 0
    prev_first_message = None

    while True:
        stream = graph.stream(command, config, stream_mode="values")
        for event in stream:
            if "messages" in event:
                if len(event["messages"]) > 0 and event["messages"][0] != prev_first_message:
                    prev_first_message = event["messages"][0]
                    prev_len = 0
                if len(event["messages"]) > prev_len:
                    for msg in event["messages"][prev_len:]:
                        # Skip tool messages so the LLM can narrate the result
                        if not getattr(msg, "tool_calls", []) and not isinstance(
                            msg, ToolMessage
                        ):
                            print(msg.content)
                            print()
                    prev_len = len(event["messages"])
            if "__interrupt__" in event:
                prompt = event["__interrupt__"][0].value
                user_input = input(prompt)
                if user_input.lower() in {"quit", "exit", "q"}:
                    print("Goodbye!")
                    return
                command = Command(resume=user_input)
                prev_len += 1
                break
        else:
            break


if __name__ == "__main__":
    play()
