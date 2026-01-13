#!/bin/bash
set -e

echo "Installing lightweight production Python dependencies..."
pip install -r requirements-prod.txt --no-cache-dir

echo "Building frontend..."
cd client
npm install
npm run build
echo "Frontend build complete!"
