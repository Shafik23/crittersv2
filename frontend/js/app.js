/**
 * Critters v2 - Main Application
 */

class CrittersApp {
    constructor() {
        // Configuration
        this.config = {
            wsUrl: `ws://${window.location.host}/ws/game`,
        };

        // Components
        this.renderer = null;
        this.wsClient = null;
        this.apiClient = new APIClient();

        // State
        this.isRunning = false;
        this.hasGame = false;

        // Species colors for legend
        this.speciesColors = {};
    }

    async init() {
        console.log('Initializing Critters v2...');

        // Initialize renderer
        const canvas = document.getElementById('game-canvas');
        this.renderer = new GameRenderer(canvas);

        // Connect WebSocket
        await this.connectWebSocket();

        // Set up UI event listeners
        this.setupEventListeners();

        // Load available critters
        await this.loadAvailableCritters();

        console.log('Critters v2 initialized');
    }

    async connectWebSocket() {
        this.wsClient = new WebSocketClient(this.config.wsUrl);

        this.wsClient.on('connected', () => {
            console.log('WebSocket connected');
            this.updateConnectionStatus(true);
        });

        this.wsClient.on('disconnected', () => {
            console.log('WebSocket disconnected');
            this.updateConnectionStatus(false);
        });

        this.wsClient.on('initial_state', (data) => {
            console.log('Received initial state');
            this.handleGameState(data);
        });

        this.wsClient.on('game_state', (data) => {
            this.handleGameState(data);
        });

        this.wsClient.on('game_end', (data) => {
            this.handleGameEnd(data);
        });

        try {
            await this.wsClient.connect();
        } catch (e) {
            console.error('Failed to connect WebSocket:', e);
        }
    }

    setupEventListeners() {
        // New Game button
        document.getElementById('new-game-btn').addEventListener('click', () => {
            this.newGame();
        });

        // Start button
        document.getElementById('start-btn').addEventListener('click', () => {
            this.startGame();
        });

        // Pause button
        document.getElementById('pause-btn').addEventListener('click', () => {
            this.pauseGame();
        });

        // Step button
        document.getElementById('step-btn').addEventListener('click', () => {
            this.stepGame();
        });

        // Speed slider
        const speedSlider = document.getElementById('speed-slider');
        const speedDisplay = document.getElementById('speed-display');

        speedSlider.addEventListener('input', () => {
            const turnsPerSec = parseInt(speedSlider.value);
            speedDisplay.textContent = `${turnsPerSec} turns/sec`;
        });

        speedSlider.addEventListener('change', async () => {
            const turnsPerSec = parseInt(speedSlider.value);
            const turnDelay = 1 / turnsPerSec;
            try {
                await this.apiClient.setSpeed(turnDelay);
            } catch (e) {
                console.error('Failed to set speed:', e);
            }
        });
    }

    async loadAvailableCritters() {
        try {
            const result = await this.apiClient.getAvailableCritters();
            console.log('Available critters:', result);
        } catch (e) {
            console.error('Failed to load critters:', e);
        }
    }

    getSelectedSpecies() {
        const checkboxes = document.querySelectorAll('#species-selector input[type="checkbox"]:checked');
        return Array.from(checkboxes).map(cb => cb.value);
    }

    async newGame() {
        const species = this.getSelectedSpecies();
        if (species.length < 1) {
            alert('Please select at least one species');
            return;
        }

        const crittersCount = parseInt(document.getElementById('critters-count').value) || 25;
        const speedSlider = document.getElementById('speed-slider');
        const turnsPerSec = parseInt(speedSlider.value);
        const turnDelay = 1 / turnsPerSec;

        try {
            const result = await this.apiClient.newGame({
                width: 60,
                height: 50,
                critters_per_species: crittersCount,
                turn_delay: turnDelay,
                species: species,
            });

            console.log('New game created:', result);

            this.hasGame = true;
            this.isRunning = false;

            // Update UI
            this.hideOverlay();
            this.updateButtons();
            this.renderer.clear();

            if (result.initial_state) {
                this.handleGameState(result.initial_state);
            }

            // Update legend with species colors
            this.updateLegend(result.initial_state?.world?.critters || []);

        } catch (e) {
            console.error('Failed to create game:', e);
            alert('Failed to create game: ' + e.message);
        }
    }

    async startGame() {
        try {
            await this.apiClient.startGame();
            this.isRunning = true;
            this.updateButtons();
            this.updateGameStatus('Running');
        } catch (e) {
            console.error('Failed to start game:', e);
        }
    }

    async pauseGame() {
        try {
            await this.apiClient.pauseGame();
            this.isRunning = false;
            this.updateButtons();
            this.updateGameStatus('Paused');
        } catch (e) {
            console.error('Failed to pause game:', e);
        }
    }

    async stepGame() {
        try {
            const result = await this.apiClient.stepGame();
            if (result.state) {
                this.handleGameState(result.state);
            }
        } catch (e) {
            console.error('Failed to step game:', e);
        }
    }

    handleGameState(state) {
        // Update renderer
        this.renderer.updateState(state);

        // Update stats
        if (state.world) {
            document.getElementById('turn-number').textContent = state.world.turn || 0;

            const aliveCritters = state.world.critters?.filter(c => c.is_alive).length || 0;
            document.getElementById('critters-alive').textContent = aliveCritters;
        }

        // Update scoreboard
        if (state.scores) {
            this.updateScoreboard(state.scores, state.world?.critters || []);
        }

        // Check for winner
        if (state.winner && state.winner !== null) {
            this.handleGameEnd({ winner: state.winner, final_state: state });
        }
    }

    handleGameEnd(data) {
        this.isRunning = false;
        this.updateButtons();
        this.updateGameStatus('Game Over');

        const winner = data.winner;

        // Show winner announcement
        const announcement = document.createElement('div');
        announcement.className = 'winner-announcement';
        announcement.innerHTML = `
            <h2>Game Over!</h2>
            <p>${winner === 'DRAW' ? "It's a draw!" : `Winner: ${winner}`}</p>
            <button class="btn btn-primary" onclick="this.parentElement.remove()">Close</button>
        `;
        document.body.appendChild(announcement);
    }

    updateScoreboard(scores, critters) {
        const scoreboard = document.getElementById('scoreboard');

        if (!scores || Object.keys(scores).length === 0) {
            scoreboard.innerHTML = '<p class="no-game">No game in progress</p>';
            return;
        }

        // Get colors for each species
        const speciesColors = {};
        for (const critter of critters) {
            if (!speciesColors[critter.owner]) {
                speciesColors[critter.owner] = critter.color;
            }
        }

        // Sort by score
        const sortedScores = Object.entries(scores).sort((a, b) => b[1] - a[1]);

        let html = '';
        for (const [species, score] of sortedScores) {
            const color = speciesColors[species] || '#888';
            html += `
                <div class="score-row">
                    <div class="score-species">
                        <span class="score-color" style="background: ${color};"></span>
                        <span class="score-name">${species}</span>
                    </div>
                    <span class="score-value">${score}</span>
                </div>
            `;
        }

        scoreboard.innerHTML = html;
    }

    updateLegend(critters) {
        const legend = document.getElementById('legend');

        // Get unique species with colors
        const species = {};
        for (const critter of critters) {
            if (!species[critter.owner]) {
                species[critter.owner] = critter.color;
            }
        }

        let html = `
            <div class="legend-item">
                <span class="legend-color" style="background: #4CAF50;"></span>
                <span>Food</span>
            </div>
        `;

        for (const [name, color] of Object.entries(species)) {
            html += `
                <div class="legend-item">
                    <span class="legend-color" style="background: ${color};"></span>
                    <span>${name}</span>
                </div>
            `;
        }

        legend.innerHTML = html;
    }

    updateButtons() {
        const startBtn = document.getElementById('start-btn');
        const pauseBtn = document.getElementById('pause-btn');
        const stepBtn = document.getElementById('step-btn');

        startBtn.disabled = !this.hasGame || this.isRunning;
        pauseBtn.disabled = !this.hasGame || !this.isRunning;
        stepBtn.disabled = !this.hasGame || this.isRunning;
    }

    updateGameStatus(status) {
        document.getElementById('game-status').textContent = status;
    }

    updateConnectionStatus(connected) {
        // Could add a visual indicator for connection status
    }

    hideOverlay() {
        document.getElementById('game-overlay').classList.add('hidden');
    }

    showOverlay(title, message) {
        const overlay = document.getElementById('game-overlay');
        overlay.classList.remove('hidden');
        overlay.querySelector('h2').textContent = title;
        overlay.querySelector('p').textContent = message;
    }
}

// Initialize app on page load
document.addEventListener('DOMContentLoaded', () => {
    window.app = new CrittersApp();
    window.app.init().catch(e => console.error('Failed to initialize app:', e));
});
