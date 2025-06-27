from typing_extensions import TypedDict, Annotated
from langgraph.graph.message import add_messages


class GameState(TypedDict):
    messages: Annotated[list, add_messages]
    current_room: str
    need_summary: bool
    player_description: str