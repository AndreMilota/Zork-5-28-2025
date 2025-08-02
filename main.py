from engine import GameEngine

def play():
    engine = GameEngine()  # Uses default rooms, player description, etc.
    user_input = None

    while True:
        status, text = engine.process_turn(user_input)
        if text:
            print(text, end="")
        if status == "__WAITING_FOR_INPUT__":
            user_input = input()
            print()
            if user_input.lower() in {"quit", "exit", "q"}:
                print("Goodbye!")
                break

if __name__ == "__main__":
    play()
