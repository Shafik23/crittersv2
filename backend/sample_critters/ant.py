"""
Ant - food-seeking colony critter.

Ants prioritize finding and eating food. They move toward food when detected,
and wander in search patterns when no food is visible.
Always scratches in fights. Always eats food.
"""

import sys
import os
import random

# Add parent directory to path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from app.core.critter_base import Critter, Direction, Attack, CritterInfo


class Ant(Critter):
    """
    Ant seeks food aggressively. When food is detected, moves toward it.
    When no food is visible, wanders in a search pattern.
    Always scratches in fights. Always eats food.
    """

    def __init__(self):
        self.wander_directions = [Direction.NORTH, Direction.EAST, Direction.SOUTH, Direction.WEST]
        self.current_wander = random.randint(0, 3)
        self.wander_steps = 0

    def get_move(self, info: CritterInfo) -> Direction:
        # Priority 1: Move toward food if detected
        food_dir = info.get_direction_to_food()
        if food_dir is not None and food_dir != Direction.CENTER:
            return food_dir

        # Priority 2: Check immediate neighbors for food
        for direction in [Direction.NORTH, Direction.EAST, Direction.SOUTH, Direction.WEST]:
            if info.get_neighbor(direction) == "F":
                return direction

        # Priority 3: Wander in search pattern
        self.wander_steps += 1
        if self.wander_steps >= random.randint(2, 5):
            self.wander_steps = 0
            self.current_wander = (self.current_wander + random.choice([1, -1])) % 4

        return self.wander_directions[self.current_wander]

    def fight(self, opponent: str) -> Attack:
        return Attack.SCRATCH

    def eat(self) -> bool:
        return True

    def get_color(self) -> str:
        return "#8B0000"  # Dark red

    def __str__(self) -> str:
        return "A"
