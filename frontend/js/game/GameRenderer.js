/**
 * GameRenderer - Canvas-based rendering for the Critters game
 */
class GameRenderer {
    constructor(canvas) {
        this.canvas = canvas;
        this.ctx = canvas.getContext('2d');

        // World dimensions (will be updated when game starts)
        this.worldWidth = 60;
        this.worldHeight = 50;

        // Calculate cell size to fit canvas
        this.updateCellSize();

        // Visual settings
        this.gridLineColor = '#1a4f7a';
        this.backgroundColor = '#16213e';
        this.foodColor = '#4CAF50';

        // Game state
        this.critters = new Map(); // id -> critter data
        this.foodPositions = new Set();
        this.currentTurn = 0;

        // Animation
        this.critterPositions = new Map(); // id -> {x, y} for smooth movement
        this.animationSpeed = 0.2;

        // Start render loop
        this.isRunning = true;
        this.lastFrameTime = 0;
        requestAnimationFrame((t) => this.renderLoop(t));
    }

    updateCellSize() {
        this.cellSize = Math.min(
            Math.floor(this.canvas.width / this.worldWidth),
            Math.floor(this.canvas.height / this.worldHeight)
        );

        // Center the grid
        this.offsetX = Math.floor((this.canvas.width - this.worldWidth * this.cellSize) / 2);
        this.offsetY = Math.floor((this.canvas.height - this.worldHeight * this.cellSize) / 2);
    }

    setWorldSize(width, height) {
        this.worldWidth = width;
        this.worldHeight = height;
        this.updateCellSize();
    }

    renderLoop(timestamp) {
        if (!this.isRunning) return;

        const deltaTime = timestamp - this.lastFrameTime;
        this.lastFrameTime = timestamp;

        // Update animations
        this.updateAnimations(deltaTime);

        // Clear canvas
        this.ctx.fillStyle = this.backgroundColor;
        this.ctx.fillRect(0, 0, this.canvas.width, this.canvas.height);

        // Draw grid
        this.drawGrid();

        // Draw food
        this.drawFood();

        // Draw critters
        this.drawCritters();

        // Draw overlay info
        this.drawOverlay();

        requestAnimationFrame((t) => this.renderLoop(t));
    }

    updateAnimations(deltaTime) {
        // Smooth movement interpolation
        for (const [id, critter] of this.critters) {
            if (!this.critterPositions.has(id)) {
                this.critterPositions.set(id, { x: critter.x, y: critter.y });
            }

            const pos = this.critterPositions.get(id);
            const targetX = critter.x;
            const targetY = critter.y;

            // Handle wrapping - move in shorter direction
            let dx = targetX - pos.x;
            let dy = targetY - pos.y;

            // Handle world wrapping
            if (Math.abs(dx) > this.worldWidth / 2) {
                dx = dx > 0 ? dx - this.worldWidth : dx + this.worldWidth;
            }
            if (Math.abs(dy) > this.worldHeight / 2) {
                dy = dy > 0 ? dy - this.worldHeight : dy + this.worldHeight;
            }

            // Interpolate
            pos.x += dx * this.animationSpeed;
            pos.y += dy * this.animationSpeed;

            // Wrap position
            pos.x = ((pos.x % this.worldWidth) + this.worldWidth) % this.worldWidth;
            pos.y = ((pos.y % this.worldHeight) + this.worldHeight) % this.worldHeight;

            // Snap if close enough
            if (Math.abs(dx) < 0.01 && Math.abs(dy) < 0.01) {
                pos.x = targetX;
                pos.y = targetY;
            }
        }
    }

    drawGrid() {
        this.ctx.strokeStyle = this.gridLineColor;
        this.ctx.lineWidth = 0.5;

        // Vertical lines
        for (let x = 0; x <= this.worldWidth; x++) {
            this.ctx.beginPath();
            this.ctx.moveTo(this.offsetX + x * this.cellSize, this.offsetY);
            this.ctx.lineTo(this.offsetX + x * this.cellSize, this.offsetY + this.worldHeight * this.cellSize);
            this.ctx.stroke();
        }

        // Horizontal lines
        for (let y = 0; y <= this.worldHeight; y++) {
            this.ctx.beginPath();
            this.ctx.moveTo(this.offsetX, this.offsetY + y * this.cellSize);
            this.ctx.lineTo(this.offsetX + this.worldWidth * this.cellSize, this.offsetY + y * this.cellSize);
            this.ctx.stroke();
        }
    }

    drawFood() {
        this.ctx.fillStyle = this.foodColor;

        for (const posStr of this.foodPositions) {
            const [x, y] = posStr.split(',').map(Number);

            // Draw food as a small circle
            const centerX = this.offsetX + x * this.cellSize + this.cellSize / 2;
            const centerY = this.offsetY + y * this.cellSize + this.cellSize / 2;

            this.ctx.beginPath();
            this.ctx.arc(centerX, centerY, this.cellSize / 4, 0, Math.PI * 2);
            this.ctx.fill();
        }
    }

    drawCritters() {
        for (const [id, critter] of this.critters) {
            if (!critter.is_alive) continue;

            const pos = this.critterPositions.get(id) || { x: critter.x, y: critter.y };

            const x = this.offsetX + pos.x * this.cellSize;
            const y = this.offsetY + pos.y * this.cellSize;

            // Draw background circle
            this.ctx.fillStyle = critter.color || '#888';
            this.ctx.beginPath();
            this.ctx.arc(
                x + this.cellSize / 2,
                y + this.cellSize / 2,
                this.cellSize / 2 - 1,
                0, Math.PI * 2
            );
            this.ctx.fill();

            // Draw display character
            this.ctx.fillStyle = this.getContrastColor(critter.color || '#888');
            this.ctx.font = `bold ${this.cellSize * 0.65}px monospace`;
            this.ctx.textAlign = 'center';
            this.ctx.textBaseline = 'middle';
            this.ctx.fillText(
                critter.display || '?',
                x + this.cellSize / 2,
                y + this.cellSize / 2 + 1
            );

            // Draw sleeping indicator
            if (critter.is_sleeping) {
                this.ctx.fillStyle = 'rgba(0, 0, 0, 0.5)';
                this.ctx.beginPath();
                this.ctx.arc(
                    x + this.cellSize / 2,
                    y + this.cellSize / 2,
                    this.cellSize / 2 - 1,
                    0, Math.PI * 2
                );
                this.ctx.fill();

                this.ctx.fillStyle = '#fff';
                this.ctx.font = `bold ${this.cellSize * 0.5}px sans-serif`;
                this.ctx.fillText('z', x + this.cellSize / 2, y + this.cellSize / 2);
            }
        }
    }

    drawOverlay() {
        // Turn counter in top-left
        this.ctx.fillStyle = 'rgba(0, 0, 0, 0.5)';
        this.ctx.fillRect(5, 5, 100, 25);

        this.ctx.fillStyle = '#fff';
        this.ctx.font = '14px monospace';
        this.ctx.textAlign = 'left';
        this.ctx.textBaseline = 'top';
        this.ctx.fillText(`Turn: ${this.currentTurn}`, 10, 10);
    }

    getContrastColor(hexColor) {
        // Return black or white depending on background brightness
        if (!hexColor || !hexColor.startsWith('#') || hexColor.length < 4) {
            return '#ffffff';
        }

        // Parse hex color (supports both #RGB and #RRGGBB)
        const isShortHex = hexColor.length === 4;
        const r = parseInt(isShortHex ? hexColor[1] + hexColor[1] : hexColor.slice(1, 3), 16);
        const g = parseInt(isShortHex ? hexColor[2] + hexColor[2] : hexColor.slice(3, 5), 16);
        const b = parseInt(isShortHex ? hexColor[3] + hexColor[3] : hexColor.slice(5, 7), 16);

        const brightness = (r * 299 + g * 587 + b * 114) / 1000;
        return brightness > 128 ? '#000000' : '#ffffff';
    }

    // State update methods

    updateState(gameState) {
        if (!gameState || !gameState.world) return;

        const world = gameState.world;

        this.currentTurn = world.turn || 0;

        // Update world size if changed
        if (world.width !== this.worldWidth || world.height !== this.worldHeight) {
            this.setWorldSize(world.width, world.height);
        }

        // Update food positions
        this.foodPositions.clear();
        if (world.food) {
            for (const pos of world.food) {
                this.foodPositions.add(`${pos[0]},${pos[1]}`);
            }
        }

        // Update critters
        const existingIds = new Set(this.critters.keys());

        if (world.critters) {
            for (const critterData of world.critters) {
                this.critters.set(critterData.id, critterData);
                existingIds.delete(critterData.id);
            }
        }

        // Remove dead/missing critters
        for (const id of existingIds) {
            this.critters.delete(id);
            this.critterPositions.delete(id);
        }
    }

    clear() {
        this.critters.clear();
        this.critterPositions.clear();
        this.foodPositions.clear();
        this.currentTurn = 0;
    }

    stop() {
        this.isRunning = false;
    }
}
