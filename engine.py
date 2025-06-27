# GameEngine class (manages state, runs turns, exposes APIs)

from graph import build_graph
import uuid
from langgraph.types import Command
from langchain_core.messages import ToolMessage
from data import player_description, ROOMS

class GameEngine:
    def __init__(self, graph=None, default_player_description=None, start_room="hall"):
        if graph is None:
            self.graph = build_graph()
        else:
            self.graph = graph
        if default_player_description  is None:
            default_player_description = player_description
        self.state = {
            "current_room": start_room,
            "messages": [],
            "need_summary": False,
            "player_description": default_player_description,
        }
        self.config = {"configurable": {"thread_id": str(uuid.uuid4())}}
        self.prev_len = 0
        self.prev_first_message = None

    # def process_turn (self, command):
    #     """Core loop for processing a single command through the graph."""
    #     stream = self.graph.stream(command, self.config, stream_mode="values", debug=False)
    #     for event in stream:
    #         if "messages" in event:
    #             self._handle_messages(event["messages"])
    #         if "__interrupt__" in event:
    #             return event["__interrupt__"][0].value  # Return the prompt to ask for input
    #     return None  # No interrupt means the turn finished cleanly

    def process_turn(self, user_input=None):
        """Process one turn of the game. Handles initial state or resumed input."""
        if user_input is None:
            command = Command(update=self.state)
        else:
            command = Command(update=self.state, resume=user_input)

        stream = self.graph.stream(command, self.config, stream_mode="values", debug=False)

        for event in stream:
            if "messages" in event:
                self._handle_messages(event["messages"])

            if "state" in event:
                self.state.update(event["state"])

            if "__interrupt__" in event:
                return "__WAITING_FOR_INPUT__", event["__interrupt__"][0].value

        return "__TURN_COMPLETE__", None

    def _handle_messages(self, messages):
        if len(messages) > 0 and messages[0] != self.prev_first_message:
            self.prev_first_message = messages[0]
            self.prev_len = 0
        if len(messages) > self.prev_len:
            for msg in messages[self.prev_len:]:
                if isinstance(msg, ToolMessage) and msg.name == "send_to_player":
                    print(msg.content)
                    print()
                elif not getattr(msg, "tool_calls", []):
                    print(msg.content)
                    print()
            self.prev_len = len(messages)

    def play(self):
        """Interactive play loop."""
        command = Command(**self.state)
        while True:
            prompt = self.process_stream(command)
            if prompt:
                user_input = input(prompt)
                if user_input.lower() in {"quit", "exit", "q"}:
                    print("Goodbye!")
                    break
                command = Command(resume=user_input)
                self.prev_len += 1

graph = build_graph()
engine = GameEngine(graph, player_description)
