# Critters v2

An educational game simulation where different critter species compete on a grid-based world. Students create custom critter subclasses to battle against each other in a survival arena.

## Features

- **Real-time simulation** with adjustable speed
- **Toroidal grid world** (edges wrap around)
- **Rock-paper-scissors combat** (ROAR > SCRATCH > POUNCE > ROAR)
- **Food mechanics** with sleep states after eating
- **Live scoreboard** tracking survival, food eaten, and fights won
- **WebSocket updates** for smooth real-time rendering

## Quick Start

```bash
./run.sh
```

Then open http://localhost:8000/game in your browser.

## How to Play

1. Select which critter species to include using the checkboxes
2. Set the number of critters per species
3. Click **New Game** to initialize the world
4. Click **Start** to begin the simulation
5. Watch the critters compete! Use the speed slider to adjust simulation speed.

## Creating Your Own Critter

Create a new file in `backend/sample_critters/` that extends the `Critter` class:

```python
from app.core.critter_base import Critter, Direction, Attack, CritterInfo

class MyCritter(Critter):
    def get_move(self, info: CritterInfo) -> Direction:
        # Return which direction to move (NORTH, SOUTH, EAST, WEST, CENTER)
        return Direction.NORTH

    def fight(self, opponent: str) -> Attack:
        # Return your attack (ROAR, SCRATCH, or POUNCE)
        return Attack.ROAR

    def eat(self) -> bool:
        # Return True to eat food when on it, False to skip
        return True

    def get_color(self) -> str:
        # Return a CSS color for rendering
        return "#FF0000"

    def __str__(self) -> str:
        # Return a single character to display on the grid
        return "M"
```

Then register it in `backend/app/main.py`:

```python
from sample_critters.my_critter import MyCritter

AVAILABLE_CRITTERS = {
    # ... existing critters ...
    "MyCritter": MyCritter,
}
```

## CritterInfo API

Your critter's `get_move()` method receives a `CritterInfo` object with:

- `neighbors` - Dict of adjacent critters by direction (NORTH, SOUTH, EAST, WEST)
- `direction_to_food` - Direction to nearest food (or CENTER if none)
- `direction_to_enemy` - Direction to nearest enemy (or CENTER if none)

## Scoring

- **+1 point** for staying alive each turn
- **+1 point** for each food eaten
- **+2 points** for each fight won

## Tech Stack

- **Backend**: Python FastAPI with WebSocket support
- **Frontend**: Vanilla JavaScript with HTML5 Canvas
- **No build step** - just run and go

## License

MIT
