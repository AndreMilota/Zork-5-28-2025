import sys
import os

# Add the parent directory to sys.path so Python can find core.py
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

# Now you can import core
import core

from typing import Annotated

from typing_extensions import TypedDict

from langgraph.graph import StateGraph, START
from langgraph.graph.message import add_messages


class State(TypedDict):
    # Messages have the type "list". The `add_messages` function
    # in the annotation defines how this state key should be updated
    # (in this case, it appends messages to the list, rather than overwriting them)
    messages: Annotated[list, add_messages]


graph_builder = StateGraph(State)


#os.environ["OPENAI_API_KEY"] = "sk-..."

#llm = init_chat_model("anthropic:claude-3-5-sonnet-latest")

def chatbot(state: State):
    return {"messages": [core.core_llm.invoke(state["messages"])]}


# The first argument is the unique node name
# The second argument is the function or object that will be called whenever
# the node is used.
graph_builder.add_node("chatbot", chatbot)

graph_builder.add_edge(START, "chatbot")
graph = graph_builder.compile()

import pathlib

# Save the graph image to a file
try:
    output_path = pathlib.Path("graph.png")
    png_bytes = graph.get_graph().draw_mermaid_png()
    output_path.write_bytes(png_bytes)
    print(f"Graph image saved to {output_path.resolve()}")
except Exception as e:
    print(f"❌ Failed to generate graph image: {e}")

def stream_graph_updates(user_input: str):
    for event in graph.stream({"messages": [{"role": "user", "content": user_input}]}):
        for value in event.values():
            print("Assistant:", value["messages"][-1].content)


while True:
    try:
        user_input = input("User: ")
        if user_input.lower() in ["quit", "exit", "q"]:
            print("Goodbye!")
            break
        stream_graph_updates(user_input)
    except:
        # fallback if input() is not available
        user_input = "What do you know about LangGraph?"
        print("User: " + user_input)
        stream_graph_updates(user_input)
        break