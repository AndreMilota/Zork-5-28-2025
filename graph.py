# Builds and compiles the LangGraph graph

from langgraph.graph import StateGraph
from langgraph.checkpoint.memory import MemorySaver
from state import GameState
from nodes import summarize_room, ask_for_action, interpret_action
from tools import move_room, send_to_player, modify_room_description, modify_player_description
from langgraph.prebuilt import ToolNode, tools_condition

def build_graph():
    graph_builder = StateGraph(GameState)

    # Add nodes
    graph_builder.add_node("summarize", summarize_room)
    graph_builder.add_node("ask", ask_for_action)
    graph_builder.add_node("interpret", interpret_action)
    graph_builder.add_node("tools", ToolNode([move_room, send_to_player, modify_room_description, modify_player_description]))

    # Add edges
    graph_builder.add_edge("summarize", "ask")
    graph_builder.add_edge("ask", "interpret")

    graph_builder.add_conditional_edges(
        "tools",
        lambda state: "summarize" if state.get("need_summary") else "interpret",
        {"summarize": "summarize", "interpret": "interpret"}
    )

    def router(state):
        if tools_condition(state) == "tools":
            return "tools"
        return "summarize" if state.get("need_summary") else "ask"

    graph_builder.add_conditional_edges(
        "interpret",
        router,
        {"tools": "tools", "summarize": "summarize", "ask": "ask"}
    )

    graph_builder.set_entry_point("summarize")

    # Compile and return
    return graph_builder.compile(checkpointer=MemorySaver())


