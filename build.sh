#!/bin/bash
set -e

echo "=== Installing Python dependencies ==="
pip install -r requirements.txt

echo "=== Building React frontend ==="
cd client
npm install
npm run build

echo "=== Build complete ==="
