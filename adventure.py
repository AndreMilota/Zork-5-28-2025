from typing import Annotated, TypedDict, Dict

from langgraph.graph import StateGraph, START
from langgraph.graph.message import add_messages
from langgraph.prebuilt import ToolNode, InjectedState, tools_condition
from langgraph.checkpoint.memory import MemorySaver
from langgraph.types import Command, interrupt
from langchain.tools import tool
from langchain_core.tools import InjectedToolCallId
from langchain_core.messages import ToolMessage

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
    return {"messages": [resp]}


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
    if direction not in exits:
        return ToolMessage(
            "You can't go that way.",
            tool_call_id=tool_call_id,
            name="move_room",
        )
    new_room = exits[direction]
    state["current_room"] = new_room
    msg = ToolMessage(
        f"You go {direction}.",
        tool_call_id=tool_call_id,
        name="move_room",
    )
    return Command(update={"current_room": new_room, "messages": [msg]})


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
    "interpret", tools_condition, {"tools": "tools", "__end__": "ask"}
)

graph_builder.add_edge("tools", "summarize")

graph_builder.set_entry_point("summarize")

graph = graph_builder.compile(checkpointer=MemorySaver())


# Simple helper to play the game from a script

def play(start_room: str = "hall"):
    """Simple interactive loop for the adventure game."""
    import uuid

    state: GameState = {"current_room": start_room, "messages": []}
    config = {"configurable": {"thread_id": str(uuid.uuid4())}}
    command: Command | dict = state
    prev_len = 0

    while True:
        for event in graph.stream(command, config, stream_mode="values"):
            state = event  # capture latest state
            if "messages" in event:
                if len(event["messages"]) > prev_len:
                    for msg in event["messages"][prev_len:]:
                        print(msg.content)
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
