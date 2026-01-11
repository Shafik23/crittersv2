"""
Bird - aggressive hunter that seeks out enemies.

Birds are predators that actively hunt other critters.
They move toward enemies when detected and roar in fights.
Never eats (keeps hunting). Fast and aggressive.
"""

import sys
import os
import random

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from app.core.critter_base import Critter, Direction, Attack, CritterInfo


class Bird(Critter):
    """
    Bird hunts enemies aggressively. Moves toward nearest enemy.
    When no enemies visible, flies in random directions searching.
    Always roars in fights. Never eats (too busy hunting).
    """

    def __init__(self):
        self.directions = [Direction.NORTH, Direction.EAST, Direction.SOUTH, Direction.WEST]
        self.current_direction = random.choice(self.directions)
        self.flight_steps = 0

    def get_move(self, info: CritterInfo) -> Direction:
        # Priority 1: Hunt enemies
        enemy_dir = info.get_direction_to_enemy()
        if enemy_dir is not None and enemy_dir != Direction.CENTER:
            self.current_direction = enemy_dir
            return enemy_dir

        # Priority 2: Check neighbors for enemies (not food, not empty)
        for direction in self.directions:
            neighbor = info.get_neighbor(direction)
            if neighbor not in [".", "F", ""]:
                self.current_direction = direction
                return direction

        # Priority 3: Fly in search pattern (more erratic than ant)
        self.flight_steps += 1
        if self.flight_steps >= random.randint(3, 7):
            self.flight_steps = 0
            self.current_direction = random.choice(self.directions)

        return self.current_direction

    def fight(self, opponent: str) -> Attack:
        return Attack.ROAR

    def eat(self) -> bool:
        return False  # Birds don't stop to eat - keep hunting

    def get_color(self) -> str:
        return "#1E90FF"  # Dodger blue

    def __str__(self) -> str:
        return "B"
