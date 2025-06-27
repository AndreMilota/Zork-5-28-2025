# Tool functions (e.g. move_room, send_to_player, modify_room_description)
from typing_extensions import Annotated
from langgraph.prebuilt import InjectedState
from langgraph.graph.message import REMOVE_ALL_MESSAGES
from langchain_core.tools import InjectedToolCallId
from langchain.tools import tool
from langchain_core.messages import ToolMessage, RemoveMessage
from langgraph.types import Command

from state import GameState
from data import ROOMS

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
    norm_direction = direction.lower()

    if norm_direction not in exits:
        return ToolMessage(
            "INVALID_DIRECTION",
            tool_call_id=tool_call_id,
            name="move_room",
        )

    new_room = exits[norm_direction]
    state["current_room"] = new_room
    msg = ToolMessage(
        "MOVED",
        tool_call_id=tool_call_id,
        name="move_room",
    )
    clear = RemoveMessage(id=REMOVE_ALL_MESSAGES)

    update = dict(state)  # copy all current state
    update["current_room"] = new_room
    update["messages"] = [msg, clear]
    update["need_summary"] = True

    return Command(update=update)


TOOLS = [move_room, send_to_player, modify_room_description, modify_player_description]