"""
Stone - doesn't move, just sits there.

A baseline critter that never moves.
Good for testing other critters.
"""

import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from app.core.critter_base import Critter, Direction, Attack, CritterInfo


class Stone(Critter):
    """
    Stone never moves. It just sits there being a stone.
    Roars if attacked (surprisingly fierce).
    Never eats.
    """

    def get_move(self, info: CritterInfo) -> Direction:
        return Direction.CENTER  # Never moves

    def fight(self, opponent: str) -> Attack:
        return Attack.ROAR  # Stones are loud

    def eat(self) -> bool:
        return False  # Stones don't eat

    def get_color(self) -> str:
        return "#A9A9A9"  # Dark gray

    def __str__(self) -> str:
        return "S"
