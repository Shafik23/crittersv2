"""
Hippo - a hungry beast that loves to eat.

Moves randomly but prioritizes food when nearby.
Pounces in fights. Always eats.
"""

import sys
import os
import random

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from app.core.critter_base import Critter, Direction, Attack, CritterInfo


class Hippo(Critter):
    """
    Hippo wanders around looking for food.
    If food is nearby, moves toward it.
    Otherwise moves randomly.
    Always pounces in fights. Always eats.
    """

    def __init__(self):
        self.all_directions = [Direction.NORTH, Direction.SOUTH, Direction.EAST, Direction.WEST]
        self.hunger = 0  # Increases when not eating

    def get_move(self, info: CritterInfo) -> Direction:
        self.hunger += 1

        # If we know where food is, go toward it
        food_dir = info.get_direction_to_food()
        if food_dir is not None:
            return food_dir

        # Otherwise, wander randomly
        return random.choice(self.all_directions)

    def fight(self, opponent: str) -> Attack:
        return Attack.POUNCE

    def eat(self) -> bool:
        self.hunger = 0
        return True

    def get_color(self) -> str:
        # Gets more gray when hungry
        if self.hunger > 10:
            return "#696969"  # Dim gray
        return "#808080"  # Gray

    def __str__(self) -> str:
        return "H"
