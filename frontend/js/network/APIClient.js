/**
 * APIClient - REST API client for game management
 */
class APIClient {
    constructor(baseUrl = '') {
        this.baseUrl = baseUrl || window.location.origin;
    }

    async request(method, path, data = null) {
        const url = `${this.baseUrl}${path}`;
        const options = {
            method,
            headers: {
                'Content-Type': 'application/json',
            },
        };

        if (data) {
            options.body = JSON.stringify(data);
        }

        const response = await fetch(url, options);

        if (!response.ok) {
            const error = await response.json().catch(() => ({ message: response.statusText }));
            throw new Error(error.detail || error.message || 'Request failed');
        }

        return response.json();
    }

    async get(path) {
        return this.request('GET', path);
    }

    async post(path, data = null) {
        return this.request('POST', path, data);
    }

    // Game API methods

    async getAvailableCritters() {
        return this.get('/api/critters');
    }

    async newGame(config) {
        return this.post('/api/game/new', config);
    }

    async startGame() {
        return this.post('/api/game/start');
    }

    async pauseGame() {
        return this.post('/api/game/pause');
    }

    async stepGame() {
        return this.post('/api/game/step');
    }

    async getGameStatus() {
        return this.get('/api/game/status');
    }

    async getGameState() {
        return this.get('/api/game/state');
    }

    async setSpeed(turnDelay) {
        return this.post(`/api/game/speed?turn_delay=${turnDelay}`);
    }
}
