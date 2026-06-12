#!/bin/bash
# Render deployment start script for frontend

cd frontend
npm install
npm run build
npx serve -s build -l ${PORT:-3000}
