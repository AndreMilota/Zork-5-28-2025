# this uses the new game_test_wrapper

from game_test_wrapper import Wrapped_Game_Engine
from game_test_wrapper import compare

def test_1():
    """
    Test the Wrapped_Game_Engine with a series of inputs and expected characteristics.
    """
    # Create an instance of the wrapped game engine
    engine = Wrapped_Game_Engine()
    engine.step()
    engine.print()
    engine.step("draw a pentagram in the dust on the mirror")
    engine.print()
    engine.step("go east")
    if not engine.check_room("kitchen"):
        raise ValueError("Failed to move to the kitchen.")
    engine.print()
    engine.step("go west")
    engine.print()
    engine.step("look at the mirror")
    engine.print()
    engine.check("mentions a pentagram")

# test that just looks at the mirror
def test_look_at_mirror():
    """
    Test the Wrapped_Game_Engine by looking at the mirror.
    """
    engine = Wrapped_Game_Engine()
    engine.step()
    engine.print()
    engine.step("look at the mirror")
    engine.print()

# test picking up an itme
def test_pick_up_item():
    """
    Test the Wrapped_Game_Engine by picking up an item.
    """
    engine = Wrapped_Game_Engine()
    engine.step()
    engine.print()
    engine.step("pick up the crown")
    engine.print()

    if not engine.search_user_description("crown"):
        print (engine.state["player_description"])
        raise ValueError("Failed to pick up the crown.")

def test_retained_made_up_details():
    """
    Test the Wrapped_Game_Engine to ensure made-up details are retained.
    """
    engine = Wrapped_Game_Engine()
    engine.step()
    engine.print()
    engine.step("tell me more about the crown how many points doe it have what gems does it have etc")
    engine.print()
    # save a deep copy of the last response
    first_response = engine.last_response
    engine.step("go east")
    if not engine.check_room("kitchen"):
        raise ValueError("Failed to move to the kitchen.")
    engine.print()
    engine.step("go west")
    engine.print()
    engine.step("tell me more about the crown how many points doe it have what gems does it have etc")
    engine.print()
    ok, diff1, diff2 = compare(first_response, engine.last_response)
    if not ok:
        print("The made-up details were not retained correctly.")
        print("First response:", first_response)
        print("Second response:", engine.last_response)
        raise ValueError("Made-up details were not retained correctly.")

if __name__ == "__main__":
    # Run the test
    test_retained_made_up_details()
    print("test_retained_made_up_details.")