from typing import Annotated, TypedDict, Dict

from langgraph.graph import StateGraph, START
from langgraph.graph.message import add_messages
from langgraph.prebuilt import ToolNode, InjectedState, tools_condition
from langgraph.checkpoint.memory import MemorySaver
from langgraph.types import Command, interrupt
from langchain.tools import tool

import core

# Simple room "database"
ROOMS: Dict[str, Dict] = {
    "hall": {
        "text": "A dimly lit hallway with stone walls. A door leads east.",
        "exits": {"east": "kitchen"},
    },
    "kitchen": {
        "text": "Dusty pots hang from the ceiling. A hallway lies to the west.",
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
                "You are a text adventure narrator. Describe the room in one "
                "short sentence without any extra commentary."
            ),
        },
        {"role": "user", "content": room["text"]},
    ]
    resp = core.llm.invoke(prompt)
    return {"messages": [resp]}


def ask_for_action(state: GameState):
    """Prompt the player for their next action using a human interrupt."""
    action = interrupt("What do you do?")
    return {
        "messages": [
            {"role": "assistant", "content": "What do you do?"},
            {"role": "user", "content": action},
        ]
    }


@tool
def move_room(direction: str, state: Annotated[GameState, InjectedState]) -> str:
    """Move to an adjacent room in the given direction."""
    exits = ROOMS[state["current_room"]]["exits"]
    if direction not in exits:
        return "You can't go that way."
    state["current_room"] = exits[direction]
    return f"You go {direction}."


llm_with_tools = core.llm.bind_tools([move_room])


def interpret_action(state: GameState):
    """Use the LLM to respond to the player and call tools if needed."""
    messages = [
        {"role": "system", "content": "You control the world. Respond concisely."},
        *state["messages"],
    ]
    resp = llm_with_tools.invoke(messages)
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
                for msg in event["messages"][prev_len:]:
                    print(msg.content)
                prev_len = len(event["messages"])
            if "__interrupt__" in event:
                prompt = event["__interrupt__"][0].value
                user_input = input(f"{prompt}\n> ")
                if user_input.lower() in {"quit", "exit", "q"}:
                    print("Goodbye!")
                    return
                command = Command(resume=user_input)
                break
        else:
            break



if __name__ == "__main__":
    play()
