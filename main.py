import core

from typing import Annotated

# from langchain_tavily import TavilySearch
from typing_extensions import TypedDict

from langgraph.checkpoint.memory import MemorySaver
from langgraph.graph import StateGraph
from langgraph.graph.message import add_messages
# from langgraph.prebuilt import ToolNode, tools_condition


class State(TypedDict):
    messages: Annotated[list, add_messages]


graph_builder = StateGraph(State)

# tool = TavilySearch(max_results=2)
# tools = [tool]
# llm_with_tools = core.llm.bind_tools(tools)


def chatbot(state: State):
    # return {"messages": [llm_with_tools.invoke(state["messages"])]}
    return {"messages": [core.llm.invoke(state["messages"])]}


graph_builder.add_node("chatbot", chatbot)

# tool_node = ToolNode(tools=[tool])
# graph_builder.add_node("tools", tool_node)

# graph_builder.add_conditional_edges(
#     "chatbot",
#     tools_condition,
# )
# graph_builder.add_edge("tools", "chatbot")
graph_builder.set_entry_point("chatbot")
memory = MemorySaver()
graph = graph_builder.compile(checkpointer=memory)

config = {"configurable": {"thread_id": "1"}}


def stream_graph_updates(user_input: str):
    events = graph.stream({"messages": [{"role": "user", "content": user_input}]}, config)
    for event in events:
        for value in event.values():
            print("Assistant:", value["messages"][-1].content)


print("(Type 'quit' or 'exit' to quit)")
while True:
    user_input = input("User: ")
    if user_input.lower() in ["quit", "exit", "q"]:
        print("Goodbye!")
        break
    stream_graph_updates(user_input)