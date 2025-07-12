from typing_extensions import Annotated, TypedDict, Dict

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
            "There is a very dusty floor to ceiling mirror on one side which will allow someone to see a reflection of themselves."
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

player_description = ("You are a short Man about 50 years old. Have a long green beard with liken growing in it." ""
"Your eys are blue eyes and short black hair. You are wearing a battered brown leather jacket "
"torn blue jeans and boots. You bave a backpack with six pairs of socks and nothing else. "
"Have a bow with six arrows one of which is broken. You are wearing a comical hat made of red "
"felt that has little bells on it. "
"You have bulging pockets, bulging with something that may be important some day.")

class GameState(TypedDict):
    messages: Annotated[list, add_messages]
    current_room: str
    need_summary: bool
    player_description: str

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
        {
            "role": "user",
            "content": (
                f"{room['description']}\n\n"
                f"The player is described as: {state['player_description']}"
            ),
        },
    ]
    resp = core.core_llm.invoke(prompt)
    return {"messages": [resp], "need_summary": False}


def ask_for_action(state: GameState):
    """Prompt the player for their next action using a human interrupt."""
    action = interrupt("> ")
    # The terminal already displays the prompt, so the LLM doesn't need to ask
    # a question. Simply return the player's response to continue the
    # conversation.
    return {"messages": [{"role": "user", "content": action}]}

@tool
def send_to_player(
    text: str,
    state: Annotated[GameState, InjectedState],
    tool_call_id: Annotated[str, InjectedToolCallId],
) -> Command:
    """Send text to the player as narration or description."""
    return Command(
        update={
            "messages": [
                ToolMessage(
                    content=text,
                    name="send_to_player",
                    tool_call_id=tool_call_id,
                )
            ]
        }
    )

@tool
def modify_room_description(
    new_description: str,
    state: Annotated[GameState, InjectedState],
    tool_call_id: Annotated[str, InjectedToolCallId], ) -> Command:
    """Replace the current room's description with a new one reflecting any changes in the environment.

        Use this when the player changes something about the room (e.g., breaks an object, adds markings, takes or leaves items).
        The new description should describe the room's current state completely and consistently.
        """
    room = state["current_room"]
    ROOMS[room]["description"] = new_description
    return Command(
        update={
            "messages": [
                ToolMessage(
                    content="Room description updated.",
                    name="modify_room_description",
                    tool_call_id=tool_call_id,
                )
            ],
            "need_summary": True
        }
    )

@tool
def modify_player_description(
    new_description: str,
    state: Annotated[GameState, InjectedState],
    tool_call_id: Annotated[str, InjectedToolCallId],) -> Command:
    """Replace the current description of the player with a new one reflecting any changes to their appearance, health, or possessions.

        Use this when the player's state changes (e.g., puts on clothing, is injured, picks up or loses an item that affects their appearance).
        The description should be complete and consistent.
        """
    return Command(
        update={
            "player_description": new_description,
            "messages": [
                ToolMessage(
                    content="Player description updated.",
                    name="modify_player_description",
                    tool_call_id=tool_call_id,
                )
            ]
        }
    )


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
            "messages": [msg, clear],
            "need_summary": True,
        }
    )

TOOLS = [move_room, send_to_player, modify_room_description, modify_player_description]
llm_with_tools = core.core_llm.bind_tools(TOOLS)

def interpret_action(state: GameState):
    """Use the LLM to respond to the player and call tools if needed."""
    # The conversation history already captures the prior context, so we
    # simply pass the stored messages directly to the model. Adding a
    # system prompt on every invocation causes the model to echo the user
    # input, so it has been removed.
    room = ROOMS[state["current_room"]]
    system_prompt = {
        "role": "system",
        "content": (
            "You are a text adventure narrator.\n\n"
            f"The player is described as: {state['player_description']}\n"
            f"The current room is: {state['current_room']}\n"
            f"Room description: {room['description']}\n\n"
            "When the player does something that affects themselves (e.g. gets injured, puts on a hat), "
            "call modify_player_description or send_to_player as appropriate.\n"
            "When the player does something that changes the environment, call modify_room_description.\n"
            "If asked about an unspecified detail, choose one, update the state, and narrate the result."
            ),
    }
    full_prompt = [system_prompt] + state["messages"]
    resp = llm_with_tools.invoke(full_prompt)
    return {"messages": [resp]}


# ---------------------------- edges ------------------------------

graph_builder.add_node("summarize", summarize_room)

graph_builder.add_node("ask", ask_for_action)

graph_builder.add_node("interpret", interpret_action)
#graph_builder.add_node("tools", ToolNode([move_room]))
graph_builder.add_node("tools", ToolNode(TOOLS))

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
        "player_description": player_description
    }
    config = {"configurable": {"thread_id": str(uuid.uuid4())}}
    command: Command | dict = state
    prev_len = 0
    prev_first_message = None

    while True:
        stream = graph.stream(command, config, stream_mode="values", debug=False)
        for event in stream:
            if "messages" in event:
                if len(event["messages"]) > 0 and event["messages"][0] != prev_first_message:
                    prev_first_message = event["messages"][0]
                    prev_len = 0
                if len(event["messages"]) > prev_len:
                    for msg in event["messages"][prev_len:]:
                        # Skip tool messages so the LLM can narrate the result
                        if isinstance(msg, ToolMessage) and msg.name == "send_to_player":
                            print(msg.content)
                            print()
                        elif not getattr(msg, "tool_calls", []):
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
