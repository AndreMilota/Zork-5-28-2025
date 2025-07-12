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
    engine.check_room("kitchen")
    engine.print()
    engine.step("go west")
    engine.print()
    engine.step("look at the mirror")
    engine.print()
    engine.check("mentions a pentagram")

if __name__ == "__main__":
    # Run the test
    test_1()
    print("Test 1 passed successfully.")