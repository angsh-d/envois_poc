#!/bin/bash
set -e

echo "Building frontend..."
cd client
npm install
npm run build
echo "Frontend build complete!"
