#!/bin/bash
set -e
echo "Building TORQ Console frontend..."
cd frontend
npm install
npx vite build
echo "Build complete!"
