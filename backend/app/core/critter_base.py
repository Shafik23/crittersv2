"""
Base Critter class and related types.

Students implement subclasses of Critter to define creature behavior.
"""

from abc import ABC, abstractmethod
from enum import Enum
from typing import Optional


class Direction(Enum):
    """Movement directions for critters."""
    NORTH = "N"
    SOUTH = "S"
    EAST = "E"
    WEST = "W"
    CENTER = "C"  # Stay in place

    def dx_dy(self) -> tuple[int, int]:
        """Return (dx, dy) for this direction."""
        return {
            Direction.NORTH: (0, -1),
            Direction.SOUTH: (0, 1),
            Direction.EAST: (1, 0),
            Direction.WEST: (-1, 0),
            Direction.CENTER: (0, 0),
        }[self]


class Attack(Enum):
    """Attack types for combat."""
    ROAR = "ROAR"      # Beats SCRATCH
    POUNCE = "POUNCE"  # Beats ROAR
    SCRATCH = "SCRATCH"  # Beats POUNCE


class Neighbor(Enum):
    """What can be in a neighboring cell."""
    EMPTY = "."
    FOOD = "F"
    WALL = "W"  # Edge of world if not wrapping


class CritterInfo:
    """
    Information provided to critters about their surroundings.

    Passed to get_move() so critters can make decisions based on
    what's around them.
    """

    def __init__(
        self,
        x: int,
        y: int,
        neighbors: dict[Direction, str],
        direction_to_food: Optional[Direction] = None,
        direction_to_enemy: Optional[Direction] = None,
    ):
        self._x = x
        self._y = y
        self._neighbors = neighbors
        self._direction_to_food = direction_to_food
        self._direction_to_enemy = direction_to_enemy

    def get_x(self) -> int:
        """Returns current x coordinate."""
        return self._x

    def get_y(self) -> int:
        """Returns current y coordinate."""
        return self._y

    def get_neighbor(self, direction: Direction) -> str:
        """
        Returns what's in the adjacent cell.

        Returns:
            "." for empty, "F" for food, or the critter's string representation
        """
        return self._neighbors.get(direction, ".")

    def get_direction_to_food(self) -> Optional[Direction]:
        """Returns direction to nearest food, or None if no food visible."""
        return self._direction_to_food

    def get_direction_to_enemy(self) -> Optional[Direction]:
        """Returns direction to nearest enemy, or None if no enemies visible."""
        return self._direction_to_enemy


class Critter(ABC):
    """
    Base class for all Critters. Students must implement all abstract methods.

    Important: Your critter does NOT control the simulation. The simulator
    calls your methods one at a time. Use instance variables to remember
    state between calls.

    Example:
        class MyCritter(Critter):
            def __init__(self):
                self.move_count = 0

            def get_move(self, info: CritterInfo) -> Direction:
                self.move_count += 1
                return Direction.NORTH

            def fight(self, opponent: str) -> Attack:
                return Attack.ROAR

            def eat(self) -> bool:
                return True

            def get_color(self) -> str:
                return "red"

            def __str__(self) -> str:
                return "M"
    """

    @abstractmethod
    def get_move(self, info: CritterInfo) -> Direction:
        """
        Called each turn to determine movement direction.

        Args:
            info: Contains information about surroundings
                  - info.get_neighbor(direction) -> what's in adjacent cell
                  - info.get_direction_to_food() -> direction to nearest food (or None)
                  - info.get_direction_to_enemy() -> direction to nearest enemy (or None)

        Returns:
            Direction enum value (NORTH, SOUTH, EAST, WEST, or CENTER)
        """
        pass

    @abstractmethod
    def fight(self, opponent: str) -> Attack:
        """
        Called when this critter encounters another species.

        Args:
            opponent: String representation of the opponent (their __str__())

        Returns:
            Attack enum value (ROAR, POUNCE, or SCRATCH)

        Combat Rules (Rock-Paper-Scissors):
            - ROAR beats SCRATCH
            - POUNCE beats ROAR
            - SCRATCH beats POUNCE
            - Same attack = random winner
        """
        pass

    @abstractmethod
    def eat(self) -> bool:
        """
        Called when critter lands on food.

        Returns:
            True to eat the food, False to decline.

        Note: Eating causes the critter to "sleep" for a few turns,
        making them vulnerable to attack.
        """
        pass

    @abstractmethod
    def get_color(self) -> str:
        """
        Returns the display color for this critter.

        Returns:
            A color string (e.g., "red", "#FF0000", "rgb(255,0,0)")
        """
        pass

    @abstractmethod
    def __str__(self) -> str:
        """
        Returns the display character(s) for this critter.

        Returns:
            A short string (1-2 characters recommended) to display on grid.
            Can change based on state (e.g., direction facing).
        """
        pass
