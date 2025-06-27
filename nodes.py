# ----------------------------- nodes -----------------------------
from core import llm
from tools import TOOLS
from state import GameState
from data import ROOMS
from langgraph.types import Command, interrupt

llm_with_tools = llm.bind_tools(TOOLS)

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
    resp = llm.invoke(prompt)
    return {"messages": [resp], "need_summary": False}

def ask_for_action(state: GameState):
    """Prompt the player for their next action using a human interrupt."""
    action = interrupt("> ")
    # The terminal already displays the prompt, so the LLM doesn't need to ask
    # a question. Simply return the player's response to continue the
    # conversation.
    return {"messages": [{"role": "user", "content": action}]}

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