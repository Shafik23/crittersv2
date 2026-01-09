"""
Bird - flies in a clockwise pattern and roars at everyone.

Classic critter that moves: North, East, South, West, repeat.
Always roars in fights. Never eats (keeps flying).
Display changes based on direction.
"""

import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from app.core.critter_base import Critter, Direction, Attack, CritterInfo


class Bird(Critter):
    """
    Bird flies in a clockwise square: N, E, S, W, repeat.
    Takes 3 steps in each direction before turning.
    Always roars in fights. Never eats (too busy flying).
    Display shows direction: ^, >, V, <
    """

    def __init__(self):
        self.directions = [Direction.NORTH, Direction.EAST, Direction.SOUTH, Direction.WEST]
        self.direction_index = 0
        self.steps_in_direction = 0
        self.steps_per_side = 3

    def get_move(self, info: CritterInfo) -> Direction:
        direction = self.directions[self.direction_index]
        self.steps_in_direction += 1

        if self.steps_in_direction >= self.steps_per_side:
            self.steps_in_direction = 0
            self.direction_index = (self.direction_index + 1) % 4

        return direction

    def fight(self, opponent: str) -> Attack:
        return Attack.ROAR

    def eat(self) -> bool:
        return False  # Birds don't stop to eat

    def get_color(self) -> str:
        return "#1E90FF"  # Dodger blue

    def __str__(self) -> str:
        symbols = {
            Direction.NORTH: "^",
            Direction.EAST: ">",
            Direction.SOUTH: "V",
            Direction.WEST: "<",
        }
        return symbols[self.directions[self.direction_index]]
