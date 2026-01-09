"""
Game Engine - the core simulation loop.

Handles turn resolution including movement, combat, eating, and scoring.
"""

from dataclasses import dataclass, field
from typing import Dict, List, Tuple, Any, Optional
import random
import uuid

from .critter_base import Critter, Direction, Attack, CritterInfo
from .world import World, Position, CritterState


@dataclass
class FightResult:
    """Result of a fight between two critters."""
    position: Tuple[int, int]
    attacker_id: str
    defender_id: str
    attacker_attack: str
    defender_attack: str
    winner_id: str
    loser_id: str


@dataclass
class TurnResult:
    """Results of a single turn of simulation."""
    turn_number: int
    movements: List[dict] = field(default_factory=list)
    fights: List[dict] = field(default_factory=list)
    eating: List[dict] = field(default_factory=list)
    deaths: List[str] = field(default_factory=list)
    scores: Dict[str, int] = field(default_factory=dict)

    def to_dict(self) -> dict:
        return {
            "turn": self.turn_number,
            "movements": self.movements,
            "fights": self.fights,
            "eating": self.eating,
            "deaths": self.deaths,
            "scores": self.scores,
        }


class GameEngine:
    """
    Main simulation engine that processes game turns.

    The engine:
    1. Collects moves from all critters
    2. Resolves movements and collisions
    3. Resolves fights between different species
    4. Processes eating
    5. Updates sleep states
    6. Spawns new food
    """

    SLEEP_TURNS_AFTER_EATING = 5
    FOOD_SPAWN_PER_TURN = 2
    METHOD_TIMEOUT_MS = 100

    # Combat resolution: attack -> what it beats
    BEATS = {
        Attack.ROAR: Attack.SCRATCH,
        Attack.SCRATCH: Attack.POUNCE,
        Attack.POUNCE: Attack.ROAR,
    }

    def __init__(self, world: World):
        self.world = world
        # Critter instances (the actual Critter objects)
        self.critter_instances: Dict[str, Critter] = {}
        self.is_running = False
        self.is_paused = False

    def add_critter_species(
        self,
        critter_class: type,
        owner: str,
        count: int = 25,
        species_name: Optional[str] = None
    ) -> List[str]:
        """
        Add multiple critters of a species to the world.

        Args:
            critter_class: The Critter subclass
            owner: Player name
            count: Number of critters to spawn
            species_name: Override for species name (defaults to class name)

        Returns:
            List of critter IDs created
        """
        species = species_name or critter_class.__name__
        critter_ids = []

        # Find empty positions
        occupied = set()
        for c in self.world.critters.values():
            occupied.add(c.position.as_tuple())
        occupied.update(self.world.food_positions)

        empty_positions = []
        for x in range(self.world.width):
            for y in range(self.world.height):
                if (x, y) not in occupied:
                    empty_positions.append((x, y))

        # Shuffle and take what we need
        random.shuffle(empty_positions)
        positions = empty_positions[:count]

        for x, y in positions:
            critter_id = str(uuid.uuid4())[:8]

            # Create instance
            try:
                instance = critter_class()
            except Exception as e:
                print(f"Error creating {species}: {e}")
                continue

            self.critter_instances[critter_id] = instance

            # Get initial display properties
            try:
                color = instance.get_color()
            except Exception:
                color = "gray"

            try:
                display = str(instance)
            except Exception:
                display = "?"

            # Create state
            state = CritterState(
                id=critter_id,
                species=species,
                owner=owner,
                position=Position(x, y),
                color=color,
                display=display,
            )

            self.world.add_critter(state)
            critter_ids.append(critter_id)

        return critter_ids

    def run_turn(self) -> TurnResult:
        """Execute one complete turn of the simulation."""
        self.world.turn_number += 1
        result = TurnResult(turn_number=self.world.turn_number)

        # Phase 1: Update sleep states
        self._update_sleep_states()

        # Phase 2: Collect all intended moves
        intended_moves = self._collect_moves()

        # Phase 3: Execute movements
        collisions = self._execute_movements(intended_moves, result)

        # Phase 4: Resolve fights at collision points
        self._resolve_fights(collisions, result)

        # Phase 5: Process eating
        self._process_eating(result)

        # Phase 6: Spawn new food
        self.world.spawn_random_food(self.FOOD_SPAWN_PER_TURN)

        # Phase 7: Update display properties
        self._update_displays()

        # Phase 8: Calculate scores
        result.scores = self._calculate_scores()

        return result

    def _update_sleep_states(self) -> None:
        """Decrement sleep counters for sleeping critters."""
        for state in self.world.critters.values():
            if state.is_sleeping and state.sleep_turns_remaining > 0:
                state.sleep_turns_remaining -= 1
                if state.sleep_turns_remaining == 0:
                    state.is_sleeping = False

    def _collect_moves(self) -> Dict[str, Direction]:
        """Ask each critter for their intended move."""
        moves: Dict[str, Direction] = {}

        for critter_id, state in self.world.critters.items():
            if not state.is_alive:
                continue

            # Sleeping critters can't move
            if state.is_sleeping:
                moves[critter_id] = Direction.CENTER
                continue

            try:
                instance = self.critter_instances.get(critter_id)
                if instance is None:
                    moves[critter_id] = Direction.CENTER
                    continue

                # Create info for this critter
                info = self.world.create_critter_info(critter_id)

                # Get move (with implicit timeout via game loop rate)
                move = instance.get_move(info)

                if isinstance(move, Direction):
                    moves[critter_id] = move
                else:
                    moves[critter_id] = Direction.CENTER

            except Exception as e:
                # Critter code failed - stay in place
                print(f"Error in {state.species}.get_move(): {e}")
                moves[critter_id] = Direction.CENTER

        return moves

    def _execute_movements(
        self,
        moves: Dict[str, Direction],
        result: TurnResult
    ) -> Dict[Tuple[int, int], List[str]]:
        """Move all critters and detect collisions."""
        # Track where each critter ends up
        final_positions: Dict[Tuple[int, int], List[str]] = {}

        for critter_id, direction in moves.items():
            state = self.world.critters.get(critter_id)
            if state is None or not state.is_alive:
                continue

            old_pos = state.position
            new_pos = old_pos.moved(direction, self.world.width, self.world.height)

            # Record movement
            if direction != Direction.CENTER:
                result.movements.append({
                    "id": critter_id,
                    "from": old_pos.as_tuple(),
                    "to": new_pos.as_tuple(),
                    "direction": direction.value,
                })

            # Move critter in world
            self.world.move_critter(critter_id, new_pos)

            # Track for collision detection
            pos_tuple = new_pos.as_tuple()
            if pos_tuple not in final_positions:
                final_positions[pos_tuple] = []
            final_positions[pos_tuple].append(critter_id)

        return final_positions

    def _resolve_fights(
        self,
        positions: Dict[Tuple[int, int], List[str]],
        result: TurnResult
    ) -> None:
        """Resolve fights when different species collide."""
        for pos, critter_ids in positions.items():
            if len(critter_ids) < 2:
                continue

            # Group by species
            species_groups: Dict[str, List[str]] = {}
            for cid in critter_ids:
                state = self.world.critters.get(cid)
                if state and state.is_alive:
                    key = f"{state.owner}:{state.species}"
                    if key not in species_groups:
                        species_groups[key] = []
                    species_groups[key].append(cid)

            # If only one species, no fight
            if len(species_groups) <= 1:
                continue

            # Fight! Pick one from each species
            fighters = []
            for species_critters in species_groups.values():
                # Pick a random fighter from this species
                fighters.append(random.choice(species_critters))

            # Round-robin fights until one species remains
            while len(fighters) > 1:
                random.shuffle(fighters)
                id1, id2 = fighters[0], fighters[1]

                fight_result = self._fight(id1, id2, pos)
                result.fights.append({
                    "position": pos,
                    "attacker": id1,
                    "defender": id2,
                    "attacker_attack": fight_result.attacker_attack,
                    "defender_attack": fight_result.defender_attack,
                    "winner": fight_result.winner_id,
                    "loser": fight_result.loser_id,
                })

                # Mark loser as dead
                loser_state = self.world.critters.get(fight_result.loser_id)
                if loser_state:
                    loser_state.is_alive = False
                    result.deaths.append(fight_result.loser_id)

                # Winner gets credit
                winner_state = self.world.critters.get(fight_result.winner_id)
                if winner_state:
                    winner_state.fights_won += 1

                # Remove loser from fighters
                fighters.remove(fight_result.loser_id)

    def _fight(
        self,
        id1: str,
        id2: str,
        position: Tuple[int, int]
    ) -> FightResult:
        """Execute a fight between two critters."""
        state1 = self.world.critters.get(id1)
        state2 = self.world.critters.get(id2)
        instance1 = self.critter_instances.get(id1)
        instance2 = self.critter_instances.get(id2)

        # Sleeping critters auto-lose
        if state1 and state1.is_sleeping:
            return FightResult(
                position=position,
                attacker_id=id1,
                defender_id=id2,
                attacker_attack="SLEEPING",
                defender_attack="N/A",
                winner_id=id2,
                loser_id=id1,
            )
        if state2 and state2.is_sleeping:
            return FightResult(
                position=position,
                attacker_id=id1,
                defender_id=id2,
                attacker_attack="N/A",
                defender_attack="SLEEPING",
                winner_id=id1,
                loser_id=id2,
            )

        # Get attacks
        attack1 = Attack.SCRATCH  # Default
        attack2 = Attack.SCRATCH

        try:
            if instance1 and instance2:
                attack1 = instance1.fight(str(instance2))
                if not isinstance(attack1, Attack):
                    attack1 = Attack.SCRATCH
        except Exception:
            pass

        try:
            if instance2 and instance1:
                attack2 = instance2.fight(str(instance1))
                if not isinstance(attack2, Attack):
                    attack2 = Attack.SCRATCH
        except Exception:
            pass

        # Determine winner
        if self.BEATS[attack1] == attack2:
            winner_id, loser_id = id1, id2
        elif self.BEATS[attack2] == attack1:
            winner_id, loser_id = id2, id1
        else:
            # Tie - random winner
            winner_id, loser_id = random.choice([(id1, id2), (id2, id1)])

        return FightResult(
            position=position,
            attacker_id=id1,
            defender_id=id2,
            attacker_attack=attack1.value,
            defender_attack=attack2.value,
            winner_id=winner_id,
            loser_id=loser_id,
        )

    def _process_eating(self, result: TurnResult) -> None:
        """Process eating for critters on food cells."""
        for critter_id, state in self.world.critters.items():
            if not state.is_alive or state.is_sleeping:
                continue

            pos = state.position
            if not self.world.has_food_at(pos):
                continue

            instance = self.critter_instances.get(critter_id)
            if instance is None:
                continue

            # Ask critter if it wants to eat
            try:
                wants_to_eat = instance.eat()
            except Exception:
                wants_to_eat = False

            if wants_to_eat:
                # Eat the food
                self.world.remove_food(pos)
                state.food_eaten += 1
                state.is_sleeping = True
                state.sleep_turns_remaining = self.SLEEP_TURNS_AFTER_EATING

                result.eating.append({
                    "id": critter_id,
                    "position": pos.as_tuple(),
                })

    def _update_displays(self) -> None:
        """Update display properties (color, character) for all critters."""
        for critter_id, state in self.world.critters.items():
            if not state.is_alive:
                continue

            instance = self.critter_instances.get(critter_id)
            if instance is None:
                continue

            try:
                state.color = instance.get_color()
            except Exception:
                pass

            try:
                state.display = str(instance)
            except Exception:
                pass

    def _calculate_scores(self) -> Dict[str, int]:
        """Calculate scores for each owner."""
        scores: Dict[str, int] = {}

        for state in self.world.critters.values():
            if not state.is_alive:
                continue

            owner = state.owner
            if owner not in scores:
                scores[owner] = 0

            # Score = alive (1) + food eaten + kills * 2
            scores[owner] += 1 + state.food_eaten + (state.fights_won * 2)

        return scores

    def get_winner(self) -> Optional[str]:
        """Check if there's a winner (only one species alive)."""
        alive_owners = set()
        for state in self.world.critters.values():
            if state.is_alive:
                alive_owners.add(state.owner)

        if len(alive_owners) == 1:
            return list(alive_owners)[0]
        elif len(alive_owners) == 0:
            return "DRAW"
        return None

    def get_state(self) -> dict:
        """Get current game state for sending to clients."""
        return {
            "turn": self.world.turn_number,
            "world": self.world.to_dict(),
            "scores": self._calculate_scores(),
            "winner": self.get_winner(),
        }
