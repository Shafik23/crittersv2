"""
Ant - walks in a square pattern.

Classic critter that moves: South, East, North, West, repeat.
Always scratches in fights. Always eats food.
"""

import sys
import os

# Add parent directory to path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from app.core.critter_base import Critter, Direction, Attack, CritterInfo


class Ant(Critter):
    """
    Ant walks in a square pattern: S, E, N, W, repeat.
    Takes 3 steps in each direction before turning.
    Always scratches in fights. Always eats food.
    """

    def __init__(self):
        self.directions = [Direction.SOUTH, Direction.EAST, Direction.NORTH, Direction.WEST]
        self.direction_index = 0
        self.steps_in_direction = 0
        self.steps_per_side = 3

    def get_move(self, info: CritterInfo) -> Direction:
        direction = self.directions[self.direction_index]
        self.steps_in_direction += 1

        # Turn after completing one side of the square
        if self.steps_in_direction >= self.steps_per_side:
            self.steps_in_direction = 0
            self.direction_index = (self.direction_index + 1) % 4

        return direction

    def fight(self, opponent: str) -> Attack:
        return Attack.SCRATCH

    def eat(self) -> bool:
        return True

    def get_color(self) -> str:
        return "#8B0000"  # Dark red

    def __str__(self) -> str:
        return "%"
