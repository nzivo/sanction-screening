#!/bin/bash

# Sanctions Screening System Startup Script

echo "=========================================="
echo "  Sanctions Screening System"
echo "=========================================="
echo ""

# Check if we're in the project root
if [ ! -d "backend" ] || [ ! -d "frontend" ]; then
    echo "Error: Please run this script from the project root directory"
    exit 1
fi

# Function to start backend
start_backend() {
    echo "Starting Backend Server..."
    cd backend
    
    # Activate virtual environment
    if [ -f "../venv/Scripts/activate" ]; then
        source ../venv/Scripts/activate
    elif [ -f "../venv/bin/activate" ]; then
        source ../venv/bin/activate
    else
        echo "Warning: Virtual environment not found"
    fi
    
    # Start uvicorn
    python main.py &
    BACKEND_PID=$!
    echo "Backend started (PID: $BACKEND_PID)"
    cd ..
}

# Function to start frontend
start_frontend() {
    echo "Starting Frontend Server..."
    cd frontend
    
    # Check if node_modules exists
    if [ ! -d "node_modules" ]; then
        echo "Installing frontend dependencies..."
        npm install
    fi
    
    # Start vite dev server
    npm run dev &
    FRONTEND_PID=$!
    echo "Frontend started (PID: $FRONTEND_PID)"
    cd ..
}

# Start services
echo "Starting services..."
echo ""

start_backend
sleep 3  # Give backend time to start

start_frontend

echo ""
echo "=========================================="
echo "  Startup Complete!"
echo "=========================================="
echo ""
echo "Backend API:  http://localhost:8000"
echo "API Docs:     http://localhost:8000/docs"
echo "Frontend:     http://localhost:3000"
echo ""
echo "Press Ctrl+C to stop both servers"
echo ""

# Wait for Ctrl+C
trap "echo 'Shutting down...'; kill $BACKEND_PID $FRONTEND_PID; exit 0" SIGINT SIGTERM

# Keep script running
wait
