# Room definitions / database
from typing_extensions import Dict

ROOMS: Dict[str, Dict] = {
    "hall": {
        "description": (
            "A dimly lit hallway with rough stone walls. Faintly glowing torches "
            "cast long shadows across the cracked floor, and cobwebs hang in the "
            "corners. Ancient portraits, nearly faded to nothing, line the walls "
            "with ghostly faces. A heavy oak door, its iron handle worn smooth, "
            "leads east."
            "There is a very dusty floor to ceiling mirror on one side which will allow someone to see a reflection of themselves."
            "There is a golden crown on the floor."
        ),
        "exits": {"east": "kitchen"},
    },
    "kitchen": {
        "description": (
            "Dusty pots hang from the ceiling above a scarred wooden table. "
            "A large stone hearth dominates one side, still carrying the faint "
            "smell of old herbs and smoke. Rusty utensils litter the counters, "
            "and a grimy window barely lets in any light. An archway to the "
            "west returns to the hallway."
        ),
        "exits": {"west": "hall"},
    },
}

player_description = ("You are a short Man about 50 years old. Have a long green beard with liken growing in it." ""
"Your eys are blue eyes and short black hair. You are wearing a battered brown leather jacket "
"torn blue jeans and boots. You bave a backpack with six pairs of socks and nothing else. "
"Have a bow with six arrows one of which is broken. You are wearing a comical hat made of red "
"felt that has little bells on it. "
"You have bulging pockets, bulging with something that may be important some day.")