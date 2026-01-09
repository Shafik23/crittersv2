"""
World class representing the game grid.

The world is a toroidal grid (wraps around edges) containing critters and food.
"""

from dataclasses import dataclass, field
from typing import Dict, List, Set, Tuple, Optional
import random

from .critter_base import Direction, CritterInfo


@dataclass
class Position:
    """A position on the grid."""
    x: int
    y: int

    def moved(self, direction: Direction, world_width: int, world_height: int) -> "Position":
        """Return new position after moving in direction (with wrapping)."""
        dx, dy = direction.dx_dy()
        return Position(
            x=(self.x + dx) % world_width,
            y=(self.y + dy) % world_height
        )

    def as_tuple(self) -> Tuple[int, int]:
        return (self.x, self.y)

    def __hash__(self):
        return hash((self.x, self.y))

    def __eq__(self, other):
        if isinstance(other, Position):
            return self.x == other.x and self.y == other.y
        return False


@dataclass
class CritterState:
    """Runtime state for a critter instance in the world."""
    id: str
    species: str  # Class name
    owner: str    # Player name
    position: Position
    color: str
    display: str
    is_alive: bool = True
    food_eaten: int = 0
    fights_won: int = 0
    is_sleeping: bool = False
    sleep_turns_remaining: int = 0

    def to_dict(self) -> dict:
        """Convert to dictionary for JSON serialization."""
        return {
            "id": self.id,
            "species": self.species,
            "owner": self.owner,
            "x": self.position.x,
            "y": self.position.y,
            "color": self.color,
            "display": self.display,
            "is_alive": self.is_alive,
            "food_eaten": self.food_eaten,
            "fights_won": self.fights_won,
            "is_sleeping": self.is_sleeping,
        }


class World:
    """
    The game world - a toroidal grid containing critters and food.

    Coordinate system:
    - (0, 0) is top-left
    - x increases going right
    - y increases going down
    - Edges wrap around (toroidal topology)
    """

    DEFAULT_WIDTH = 60
    DEFAULT_HEIGHT = 50
    FOOD_SPAWN_RATE = 0.01  # Probability per empty cell per turn

    def __init__(self, width: int = DEFAULT_WIDTH, height: int = DEFAULT_HEIGHT):
        self.width = width
        self.height = height
        self.turn_number = 0

        # Critter storage
        self.critters: Dict[str, CritterState] = {}  # id -> state

        # Spatial index: position -> list of critter IDs at that position
        self._position_index: Dict[Tuple[int, int], List[str]] = {}

        # Food positions
        self.food_positions: Set[Tuple[int, int]] = set()

    def add_critter(self, state: CritterState) -> None:
        """Add a critter to the world."""
        self.critters[state.id] = state
        self._position_index.setdefault(state.position.as_tuple(), []).append(state.id)

    def remove_critter(self, critter_id: str) -> None:
        """Remove a critter from the world."""
        if critter_id not in self.critters:
            return
        state = self.critters[critter_id]
        pos = state.position.as_tuple()
        if pos in self._position_index:
            self._position_index[pos] = [
                cid for cid in self._position_index[pos] if cid != critter_id
            ]
            if not self._position_index[pos]:
                del self._position_index[pos]
        del self.critters[critter_id]

    def move_critter(self, critter_id: str, new_position: Position) -> None:
        """Move a critter to a new position."""
        if critter_id not in self.critters:
            return

        state = self.critters[critter_id]
        old_pos = state.position.as_tuple()
        new_pos = new_position.as_tuple()

        # Update spatial index
        if old_pos in self._position_index:
            self._position_index[old_pos] = [
                cid for cid in self._position_index[old_pos] if cid != critter_id
            ]
            if not self._position_index[old_pos]:
                del self._position_index[old_pos]

        self._position_index.setdefault(new_pos, []).append(critter_id)

        # Update critter state
        state.position = new_position

    def get_critters_at(self, position: Position) -> List[str]:
        """Get list of critter IDs at a position."""
        return self._position_index.get(position.as_tuple(), [])

    def has_food_at(self, position: Position) -> bool:
        """Check if there's food at a position."""
        return position.as_tuple() in self.food_positions

    def add_food(self, position: Position) -> None:
        """Add food at a position."""
        self.food_positions.add(position.as_tuple())

    def remove_food(self, position: Position) -> None:
        """Remove food from a position."""
        self.food_positions.discard(position.as_tuple())

    def spawn_random_food(self, count: int = 1) -> None:
        """Spawn food at random empty positions."""
        empty_positions = []
        for x in range(self.width):
            for y in range(self.height):
                pos = (x, y)
                if pos not in self._position_index and pos not in self.food_positions:
                    empty_positions.append(pos)

        if empty_positions:
            positions = random.sample(empty_positions, min(count, len(empty_positions)))
            for pos in positions:
                self.food_positions.add(pos)

    def get_neighbor_content(self, position: Position, direction: Direction) -> str:
        """Get what's in a neighboring cell."""
        new_pos = position.moved(direction, self.width, self.height)

        # Check for critters
        critters_at = self.get_critters_at(new_pos)
        if critters_at:
            # Return the display string of the first critter
            critter_id = critters_at[0]
            return self.critters[critter_id].display

        # Check for food
        if self.has_food_at(new_pos):
            return "F"

        return "."

    def create_critter_info(self, critter_id: str) -> CritterInfo:
        """Create a CritterInfo object for a critter."""
        state = self.critters[critter_id]
        pos = state.position

        # Get neighbor contents
        neighbors = {}
        for direction in [Direction.NORTH, Direction.SOUTH, Direction.EAST, Direction.WEST]:
            neighbors[direction] = self.get_neighbor_content(pos, direction)

        # Find nearest food (simple implementation - check visible area)
        direction_to_food = self._find_nearest(pos, self.food_positions, max_distance=10)

        # Find nearest enemy
        enemy_positions = set()
        for cid, cstate in self.critters.items():
            if cid != critter_id and cstate.is_alive and cstate.species != state.species:
                enemy_positions.add(cstate.position.as_tuple())
        direction_to_enemy = self._find_nearest(pos, enemy_positions, max_distance=10)

        return CritterInfo(
            x=pos.x,
            y=pos.y,
            neighbors=neighbors,
            direction_to_food=direction_to_food,
            direction_to_enemy=direction_to_enemy,
        )

    def _find_nearest(
        self,
        pos: Position,
        targets: Set[Tuple[int, int]],
        max_distance: int
    ) -> Optional[Direction]:
        """Find direction to nearest target within max_distance."""
        if not targets:
            return None

        best_direction = None
        best_distance = float('inf')

        for target in targets:
            # Calculate wrapped distance
            dx = target[0] - pos.x
            dy = target[1] - pos.y

            # Handle wrapping - find shorter path
            if abs(dx) > self.width / 2:
                dx = dx - self.width if dx > 0 else dx + self.width
            if abs(dy) > self.height / 2:
                dy = dy - self.height if dy > 0 else dy + self.height

            distance = abs(dx) + abs(dy)  # Manhattan distance

            if distance < best_distance and distance <= max_distance:
                best_distance = distance
                # Determine primary direction
                if abs(dx) >= abs(dy):
                    best_direction = Direction.EAST if dx > 0 else Direction.WEST
                else:
                    best_direction = Direction.SOUTH if dy > 0 else Direction.NORTH

        return best_direction

    def get_alive_critters(self) -> List[CritterState]:
        """Get all alive critters."""
        return [c for c in self.critters.values() if c.is_alive]

    def get_species_counts(self) -> Dict[str, int]:
        """Get count of alive critters by species."""
        counts: Dict[str, int] = {}
        for critter in self.get_alive_critters():
            key = f"{critter.owner}:{critter.species}"
            counts[key] = counts.get(key, 0) + 1
        return counts

    def to_dict(self) -> dict:
        """Convert world state to dictionary for JSON serialization."""
        return {
            "width": self.width,
            "height": self.height,
            "turn": self.turn_number,
            "critters": [c.to_dict() for c in self.critters.values()],
            "food": list(self.food_positions),
        }
