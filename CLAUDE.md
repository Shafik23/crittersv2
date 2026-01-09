# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

Critters v2 is an educational game simulation where different critter species compete on a grid-based world. Students create custom critter subclasses to compete against each other.

**Tech Stack:**
- Backend: Python FastAPI with WebSocket real-time communication
- Frontend: Vanilla JavaScript with HTML5 Canvas rendering
- No build step required for frontend

## Development Commands

**Start the server:**
```bash
./run.sh
```
This creates/activates a Python venv, installs dependencies, and starts the server at `http://localhost:8000/game`.

**Manual server start:**
```bash
cd backend
python -m uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
```

## Architecture

### Backend Structure

```
backend/
├── app/
│   ├── main.py              # FastAPI entry point, REST/WebSocket endpoints, game loop
│   └── core/
│       ├── critter_base.py  # Abstract Critter class, Direction/Attack enums
│       ├── game_engine.py   # Turn resolution, combat, scoring
│       └── world.py         # Toroidal grid, spatial indexing, food spawning
└── sample_critters/         # Example critter implementations
```

### Frontend Structure

```
frontend/
├── js/
│   ├── app.js                    # Main controller, UI coordination
│   ├── game/GameRenderer.js      # Canvas rendering with interpolation
│   └── network/
│       ├── APIClient.js          # REST API wrapper
│       └── WebSocketClient.js    # Real-time updates with reconnection
```

### Game Engine Phases (per turn)

1. Update sleep states (post-eating)
2. Collect critter moves via `get_move()`
3. Execute movements on toroidal grid
4. Resolve fights (rock-paper-scissors: ROAR > SCRATCH > POUNCE > ROAR)
5. Process eating (triggers sleep)
6. Spawn food
7. Update displays
8. Calculate scores (alive: 1pt, food: 1pt, fight won: 2pts)

### REST API Endpoints

- `GET /api/critters` - Available species
- `POST /api/game/new` - Create game with selected species
- `POST /api/game/start|pause|step` - Control simulation
- `GET /api/game/state` - Full game state for debugging
- `WS /ws/game` - Real-time game state broadcasts

## Adding a New Critter Species

1. Create file in `backend/sample_critters/` inheriting from `Critter`
2. Implement required methods: `get_move()`, `fight()`, `eat()`, `get_color()`, `__str__()`
3. Add import to `backend/sample_critters/__init__.py`
4. Register in `main.py`'s `AVAILABLE_CRITTERS` dict

See `backend/sample_critters/ant.py` for a complete example.

## Key Implementation Details

- **Toroidal world**: Grid wraps at edges (handled by `Position` class in `world.py`)
- **CritterInfo**: Provides sensory input to critters (neighbors, food/enemy direction)
- **Combat**: Defined in `BEATS` dict in `game_engine.py` (line ~67)
- **Sleep mechanic**: Critters sleep for 5 turns after eating food
