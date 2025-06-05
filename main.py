import core
from graph.zork_graph import graph, GameState
from db.init_db import init_db


def stream_graph(state: GameState, user_input: str) -> GameState:
    events = graph.stream({"messages": [{"role": "user", "content": user_input}], "current_room": state["current_room"]})
    new_state = state.copy()
    for event in events:
        if "current_room" in event:
            new_state["current_room"] = event["current_room"]
        if "messages" in event:
            new_state["messages"] = event["messages"]
            print("Assistant:", event["messages"][-1]["content"])
    return new_state


def main() -> None:
    init_db()
    state: GameState = {"messages": [], "current_room": "room1"}
    state = stream_graph(state, "")  # initial room description
    print("(Type 'quit' or 'exit' to quit)")
    while True:
        user_input = input("User: ")
        if user_input.lower() in {"quit", "exit", "q"}:
            print("Goodbye!")
            break
        state = stream_graph(state, user_input)


if __name__ == "__main__":
    main()
