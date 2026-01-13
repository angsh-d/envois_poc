#!/bin/bash
# Start both backend and frontend in a single process namespace

# Start FastAPI backend in the background
cd /home/runner/workspace
uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload &
BACKEND_PID=$!

# Wait for backend to be ready
sleep 3

# Start Vite frontend
cd /home/runner/workspace/client
npm run dev &
FRONTEND_PID=$!

# Handle shutdown
trap "kill $BACKEND_PID $FRONTEND_PID 2>/dev/null" EXIT

# Wait for both processes
wait
