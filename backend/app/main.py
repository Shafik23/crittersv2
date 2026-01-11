"""
Critters v2 - FastAPI Server

Main entry point for the backend API.
"""

import asyncio
from contextlib import asynccontextmanager
from typing import Dict, List, Set

from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse, HTMLResponse
from pydantic import BaseModel

from .core import World, GameEngine
from .core.critter_base import Direction, Attack

# Import sample critters
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))
from sample_critters import Ant, Bird, Hippo, Stone


# Game size multiplier - controls grid dimensions
# 1.0 = 30x25 grid, 2.0 = 60x50 grid, etc.
GAME_SIZE = 1.5

# Base dimensions (multiplied by GAME_SIZE)
BASE_WIDTH = 30
BASE_HEIGHT = 25
BASE_CRITTERS_PER_SPECIES = 15
BASE_FOOD_COUNT = 25


# Game state
class GameState:
    def __init__(self):
        self.world: World = None
        self.engine: GameEngine = None
        self.is_running = False
        self.turn_delay = 0.2  # seconds between turns
        self.connections: Set[WebSocket] = set()


game_state = GameState()


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    print("Critters v2 server starting...")
    yield
    # Shutdown
    print("Critters v2 server shutting down...")
    game_state.is_running = False


app = FastAPI(
    title="Critters v2",
    description="Online Critters Game API",
    version="0.1.0",
    lifespan=lifespan,
)

# CORS for frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# Request/Response models
class GameConfig(BaseModel):
    width: int = int(BASE_WIDTH * GAME_SIZE)
    height: int = int(BASE_HEIGHT * GAME_SIZE)
    critters_per_species: int = int(BASE_CRITTERS_PER_SPECIES * GAME_SIZE)
    turn_delay: float = 0.2
    species: List[str] = ["Ant", "Bird"]


class GameStatus(BaseModel):
    is_running: bool
    turn: int
    scores: Dict[str, int]
    winner: str | None


# Available critter classes
AVAILABLE_CRITTERS = {
    "Ant": Ant,
    "Bird": Bird,
    "Hippo": Hippo,
    "Stone": Stone,
}


# REST Endpoints
@app.get("/")
async def root():
    """Health check endpoint."""
    return {"status": "ok", "game": "Critters v2"}


@app.get("/api/critters")
async def list_available_critters():
    """List all available critter species."""
    return {
        "critters": list(AVAILABLE_CRITTERS.keys()),
        "descriptions": {
            "Ant": "Walks in squares, scratches, eats everything",
            "Bird": "Flies in squares, roars, never eats",
            "Hippo": "Wanders toward food, pounces, always eats",
            "Stone": "Never moves, roars when attacked",
        }
    }


@app.post("/api/game/new")
async def new_game(config: GameConfig):
    """Create a new game with specified configuration."""
    # Stop any running game
    game_state.is_running = False
    await asyncio.sleep(0.1)

    # Create new world
    game_state.world = World(width=config.width, height=config.height)
    game_state.engine = GameEngine(game_state.world)
    game_state.turn_delay = config.turn_delay

    # Add initial food (scaled by game size)
    game_state.world.spawn_random_food(int(BASE_FOOD_COUNT * GAME_SIZE))

    # Add critters for each species
    for species_name in config.species:
        if species_name in AVAILABLE_CRITTERS:
            critter_class = AVAILABLE_CRITTERS[species_name]
            game_state.engine.add_critter_species(
                critter_class=critter_class,
                owner=species_name,  # Use species name as owner for now
                count=config.critters_per_species,
            )

    return {
        "status": "created",
        "config": config.model_dump(),
        "initial_state": game_state.engine.get_state(),
    }


@app.post("/api/game/start")
async def start_game():
    """Start the game simulation."""
    if game_state.engine is None:
        return {"error": "No game created. Call /api/game/new first."}

    if game_state.is_running:
        return {"status": "already_running"}

    game_state.is_running = True

    # Start the game loop in background
    asyncio.create_task(run_game_loop())

    return {"status": "started"}


@app.post("/api/game/pause")
async def pause_game():
    """Pause the game simulation."""
    game_state.is_running = False
    return {"status": "paused"}


@app.post("/api/game/step")
async def step_game():
    """Execute a single turn (when paused)."""
    if game_state.engine is None:
        return {"error": "No game created"}

    if game_state.is_running:
        return {"error": "Game is running. Pause first."}

    result = game_state.engine.run_turn()
    state = game_state.engine.get_state()

    # Broadcast to all connected clients
    await broadcast_state(state, result.to_dict())

    return {
        "status": "stepped",
        "turn_result": result.to_dict(),
        "state": state,
    }


@app.get("/api/game/status")
async def game_status():
    """Get current game status."""
    if game_state.engine is None:
        return {"is_running": False, "turn": 0, "scores": {}, "winner": None}

    return {
        "is_running": game_state.is_running,
        "turn": game_state.world.turn_number,
        "scores": game_state.engine._calculate_scores(),
        "winner": game_state.engine.get_winner(),
    }


@app.get("/api/game/state")
async def game_full_state():
    """Get full game state."""
    if game_state.engine is None:
        return {"error": "No game created"}

    return game_state.engine.get_state()


@app.post("/api/game/speed")
async def set_speed(turn_delay: float):
    """Set game speed (seconds between turns)."""
    game_state.turn_delay = max(0.05, min(2.0, turn_delay))
    return {"turn_delay": game_state.turn_delay}


# WebSocket for real-time updates
@app.websocket("/ws/game")
async def game_websocket(websocket: WebSocket):
    """WebSocket endpoint for real-time game updates."""
    await websocket.accept()
    game_state.connections.add(websocket)

    try:
        # Send current state on connect
        if game_state.engine:
            await websocket.send_json({
                "type": "initial_state",
                "data": game_state.engine.get_state(),
            })

        # Keep connection alive and handle client messages
        while True:
            try:
                data = await asyncio.wait_for(websocket.receive_json(), timeout=30.0)

                if data.get("type") == "ping":
                    await websocket.send_json({"type": "pong"})

            except asyncio.TimeoutError:
                # Send heartbeat
                await websocket.send_json({"type": "heartbeat"})

    except WebSocketDisconnect:
        pass
    finally:
        game_state.connections.discard(websocket)


async def broadcast_state(state: dict, turn_result: dict = None):
    """Broadcast game state to all connected clients."""
    if not game_state.connections:
        return

    message = {
        "type": "game_state",
        "data": state,
    }

    if turn_result:
        message["turn_result"] = turn_result

    dead = set()
    for ws in game_state.connections:
        try:
            await ws.send_json(message)
        except Exception:
            dead.add(ws)

    game_state.connections -= dead


async def run_game_loop():
    """Main game loop that runs turns and broadcasts state."""
    print("Game loop started")

    while game_state.is_running and game_state.engine:
        # Run one turn
        result = game_state.engine.run_turn()
        state = game_state.engine.get_state()

        # Broadcast to all clients
        await broadcast_state(state, result.to_dict())

        # Check for winner
        winner = game_state.engine.get_winner()
        if winner:
            game_state.is_running = False
            await broadcast_state({
                "type": "game_end",
                "winner": winner,
                "final_state": state,
            })
            break

        # Wait before next turn
        await asyncio.sleep(game_state.turn_delay)

    print("Game loop ended")


# Serve frontend static files (if available)
frontend_path = os.path.join(os.path.dirname(__file__), '..', '..', 'frontend')
DEV_MODE = os.environ.get('CRITTERS_DEV_MODE') == '1'

if os.path.exists(frontend_path):
    @app.get("/game")
    async def serve_frontend():
        html_path = os.path.join(frontend_path, 'index.html')

        if DEV_MODE:
            # Inject livereload script for hot-reload in development
            with open(html_path, 'r') as f:
                html_content = f.read()

            livereload_script = '<script src="http://localhost:35729/livereload.js"></script>'
            html_content = html_content.replace('</body>', f'{livereload_script}\n</body>')
            return HTMLResponse(content=html_content)

        return FileResponse(html_path)

    app.mount("/static", StaticFiles(directory=frontend_path), name="static")


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
