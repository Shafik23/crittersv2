#!/bin/bash

# Critters v2 - Development Server with Hot Reload
# - Backend: uvicorn with auto-reload on Python changes
# - Frontend: livereload for automatic browser refresh on JS/CSS/HTML changes

set -e

cd "$(dirname "$0")"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo -e "${GREEN}  Critters v2 - Development Server${NC}"
echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"

# Check for Python
if ! command -v python3 &> /dev/null; then
    echo -e "${RED}Python 3 is required but not installed.${NC}"
    exit 1
fi

# Create virtual environment if it doesn't exist
if [ ! -d "venv" ]; then
    echo -e "${YELLOW}Creating virtual environment...${NC}"
    python3 -m venv venv
fi

# Activate virtual environment
source venv/bin/activate

# Install dependencies (including dev dependencies)
echo -e "${YELLOW}Installing dependencies...${NC}"
pip install -q -r requirements-dev.txt

# Cleanup function
cleanup() {
    echo -e "\n${YELLOW}Shutting down servers...${NC}"
    kill $UVICORN_PID 2>/dev/null || true
    kill $LIVERELOAD_PID 2>/dev/null || true
    exit 0
}

trap cleanup SIGINT SIGTERM

# Export dev mode flag
export CRITTERS_DEV_MODE=1

echo ""
echo -e "${GREEN}Starting development servers...${NC}"
echo -e "  ${BLUE}→${NC} Backend:    http://localhost:8000/game (auto-reload on Python changes)"
echo -e "  ${BLUE}→${NC} LiveReload: Watching frontend/ for JS/CSS/HTML changes"
echo ""
echo -e "${YELLOW}Press Ctrl+C to stop${NC}"
echo ""

# Start uvicorn with reload watching both app and sample_critters
cd backend
python -m uvicorn app.main:app \
    --host 0.0.0.0 \
    --port 8000 \
    --reload \
    --reload-dir app \
    --reload-dir sample_critters &
UVICORN_PID=$!
cd ..

# Give uvicorn a moment to start
sleep 1

# Start livereload server watching frontend files
python -c "
import livereload

server = livereload.Server()

# Watch frontend files for changes
server.watch('frontend/js/**/*.js')
server.watch('frontend/styles/**/*.css')
server.watch('frontend/**/*.html')

print('LiveReload: Watching frontend/ for changes...')

# Serve on port 35729 (livereload default) - we only use the WebSocket notifications
# The actual files are served by FastAPI on port 8000
server.serve(port=35729, host='127.0.0.1', open_url_delay=None)
" &
LIVERELOAD_PID=$!

# Wait for either process to exit
wait $UVICORN_PID $LIVERELOAD_PID
