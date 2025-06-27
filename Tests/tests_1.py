# import the adventure Python module
import adventure
from core import llm
from engine import GameEngine

def evaluate_response(response: str, characteristics: str) -> bool:
    """
    Evaluate whether a given response satisfies the specified characteristics using the LLM.

    Args:
        response: The text to evaluate.
        characteristics: A description of what the text should be like.

    Returns:
        True if the LLM judges the response meets the characteristics, False otherwise.
    """
    # Build the prompt
    messages = [
        {"role": "system", "content": "You are an expert evaluator for a text adventure game."},
        {"role": "user", "content": (
            f"Here is the response:\n\n{response}\n\n"
            f"The response should meet the following characteristics:\n{characteristics}\n\n"
            "Does the response satisfy these characteristics? Answer only with 'Yes' or 'No'."
        )}
    ]

    # Call the LLM (core.llm handles provider)
    result = llm.invoke(messages)

    # Normalize and parse the response
    answer = result.content.strip().lower()
    return answer.startswith("yes")

def test_evaluate_response():
    """
    Test the evaluate_response function with various inputs.
    """
    # Define some test cases
    test_cases = [
        {
            "response": "You find yourself in a dark forest. The path splits into two.",
            "characteristics": "there are eather 1 or 3 directions you can go.",
            "expected": False
        },
        {
            "response": "You find yourself in an eerie, ancient hallway with rough stone walls. Dimly lit torches cast menacing shadows, and cobwebs drape the corners like ghostly veils. Faded portraits with barely discernible faces hang silently, watching your every move. A heavy oak door sits to the east, its iron handle smoothed by time. A dusty floor-to-ceiling mirror catches your eye, marked with a mysterious five-pointed star drawn in the thick dust. As a seasoned adventurer with a green beard and jingling hat, you stand ready to explore this mysterious corridor, your worn leather jacket and bow at the ready.",
            "characteristics": "You can not go west.",
            "expected": True
        },
        {
            "response": "This appears to be an old, weathered kitchen with a neglected, somewhat eerie atmosphere. The space is dimly lit by a grimy window, with dusty pots hanging overhead and a prominent stone hearth that still hints at past culinary activities. Rusty utensils scattered about suggest long-abandoned use. The west archway leads back to a hallway. The room looks worn and slightly grim, with an air of forgotten history.",
            "characteristics": "it says we are in a dining room.",
            "expected": True
        }
    ]

    for i, case in enumerate(test_cases):
        result = evaluate_response(case["response"], case["characteristics"])
        assert result == case["expected"], f"Test case {i+1} failed: expected {case['expected']}, got {result}"

    print("All test cases passed!")

# def run_batch_tests_list(test_cases):
#     """
#     Run batch tests using a list-based input.
#
#     Args:
#         test_cases: List where each item is:
#             [action, [characteristics]]
#             OR
#             [action] (no characteristics required)
#
#     Returns:
#         True if all tests passed, False if any failed.
#     """
#     for test in test_cases:
#         action = test[0]
#         characteristics = test[1] if len(test) > 1 else []
#
#         # Simulate running the action through your game
#         response = simulate_game_action(action)
#
#         # Print input and output
#         print(f"> Action: {action}")
#         print(f"Response: {response}\n")
#
#         # Evaluate characteristics
#         for characteristic in characteristics:
#             passed = evaluate_response(response, characteristic)
#             print(f"  Check: {characteristic}")
#             print(f"  Passed: {'✅' if passed else '❌'}\n")
#
#             if not passed:
#                 return False  # Fail fast on first failure
#
#     return True  # All passed


def batch_response(tests: list) -> bool:
    # start the game
    engine = GameEngine()

    for test in tests:
        #see if it is a string
        if isinstance(test, str):
            # If it's a string, treat it as an action
            action = test
            characteristics = []
        else:
            # Otherwise, assume it's a list with action and characteristics
            action = test[0]
            # see if the characteristics are provided
            if len(test) > 1:
                characteristics = test[1]
                #see if characteristics is a string
                if isinstance(characteristics, str):
                    characteristics = [characteristics]

        # Process the action in the game engine
        status, response = engine.process_turn(action)
        # Print the action and response
        print(f"> Action: {action}")
        print(f"Response: {response}\n")
        # Evaluate the response against each characteristic
        for characteristic in characteristics:
            passed = evaluate_response(response, characteristic)
            print(f"  Check: {characteristic}")
            print(f"  Passed: {'✅' if passed else '❌'}\n")
            if not passed:
                return False
    return True  # All tests passed

def test_batch_response():
    """
    Test the batch_response function with various inputs.
    """
    # Define some test cases
    test_cases = [
        "go north",
        ["go west", "you can not go west."],
        ["look around", ["the room is dark.", "there are torches on the walls."]]]

    result = batch_response(test_cases)
    assert result, "Batch response test failed"

#def test_sequence(actions: list)


if __name__ == "__main__":
    # Run the tests
    test_batch_response()


