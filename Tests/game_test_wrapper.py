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


class Wrapped_Game_Engine(GameEngine):
    """
    A wrapper around GameEngine to facilitate testing.
    It allows for controlled input and output during tests.
    """

    def __init__(self, graph=None, player_description=None, start_room="hall"):
        super().__init__(graph, player_description, start_room=start_room)
        # run the initial setup
        self.last_response = None
        self.last_input = None
        self.hault_on_error = True
        self.error_count = 0
        self.turns = 0
        self.tests_run = 0

    def step(self, user_input=None):
        """
        Process one turn of the game with optional user input.
        Returns the status and response text.
        """
        self.last_input = user_input
        status, response = super().process_turn(user_input)
        self.last_response = response
        return response

    def responce(self):
        """
        Get the last response from the game engine.
        """
        return self.last_response

    def print(self):
        """
        Print the last response to the console.
        """
        print(self.last_response)
        print()

    def check(self, characteristics: str, on_faile_comment: str=None) -> bool:
        """
        Check if the last response meets the specified characteristics.
        """
        if not evaluate_response(self.last_response, characteristics):
            print("TEST FAILED:    ")
            if on_faile_comment:
                print(f"{on_faile_comment}")
            print(f"\ninput :{self.last_input}\n"
                  f"output: {self.last_response}\n")
            print(f"Expected: {characteristics}\n")
            if self.hault_on_error:
                raise ValueError("Test failed")

            return False
        return True

    def print_summery(self):
        """
        Print a summary of the tests run.
        """
        print(f"Tests run: {self.tests_run}")
        print(f"Turns taken: {self.turns}")
        if self.error_count > 0:
            print(f"Errors encountered: {self.error_count}")
        else:
            print("All tests passed successfully!")

