# this uses the new game_test_wrapper

from game_test_wrapper import Wrapped_Game_Engine

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

if __name__ == "__main__":
    # Run the test
    test_pick_up_item()
    print("Test 1 passed successfully.")