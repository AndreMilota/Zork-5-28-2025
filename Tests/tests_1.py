# import the adventure Python module
import adventure
from core import llm

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

    print("All test cases passed!"
def test_sequence(actions: list)


if __name__ == "__main__":
    # Run the tests
    test_evaluate_response()


