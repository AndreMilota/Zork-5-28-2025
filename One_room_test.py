from langgraph.graph import StateGraph, END
from langgraph.prebuilt import ToolNode
from core import llm
from langchain_core.tools import tool
from langchain_core.messages import HumanMessage

from graph.Zork_graph import get_room  # assumes graph/ is a package (has __init__.py)

# --- Setup ---
ROOM_ID = "room_1_1"

def load_room(state: dict) -> dict:
    """Loads the current room from the database."""
    room = get_room(ROOM_ID)
    return {"room": room}

def summarize_room(state: dict) -> dict:
    """Uses an LLM to summarize the room description and visible items."""
    room = state["room"]
    description = room["description"]
    items = ", ".join(room["items"]) if room["items"] else "nothing visible"
    prompt = f"Summarize the following room description in a few sentences for a player. " \
             f"Room description: {description}. Items in the room: {items}."
    summary = llm.invoke(prompt).content
    return {"summary": summary}

def show_summary_and_get_input(state: dict) -> dict:
    """Displays the room summary and gets the user's input."""
    print("\n--- Room Summary ---")
    print(state["summary"])
    user_input = input("\nWhat would you like to do or ask? ")
    return {"user_input": user_input}

def respond_to_user(state: dict) -> dict:
    """Responds to the user's input using the LLM, staying in-character."""
    room = state["room"]
    prompt = (
        f"You are a text-based game interpreter. The player is in a room described as:\n"
        f"{room['description']}\n"
        f"They can see the following items: {', '.join(room['items']) or 'nothing'}.\n"
        f"The player asks: \"{state['user_input']}\"\n"
        f"Respond as the game would, staying in-character and not breaking the fourth wall."
    )
    response = llm.invoke(prompt).content
    print("\n--- Game Responds ---")
    print(response)
    return {"llm_response": response}


# --- Graph Definition ---
builder = StateGraph(state_schema=dict)
builder.add_node("load_room", load_room)
builder.add_node("summarize_room", summarize_room)
builder.add_node("show_input", show_summary_and_get_input)
builder.add_node("respond", respond_to_user)

builder.set_entry_point("load_room")

builder.add_edge("load_room", "summarize_room")
builder.add_edge("summarize_room", "show_input")
builder.add_edge("show_input", "respond")
builder.add_edge("respond", "show_input")  # loop after response

graph = builder.compile()

# --- Run Loop ---
if __name__ == "__main__":
    print("Starting One-Room LangGraph Game. Type Ctrl+C to quit.")
    try:
        graph.invoke(HumanMessage(content="Start the game"))
    except KeyboardInterrupt:
        print("\nGame exited.")