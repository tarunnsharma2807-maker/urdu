#!/bin/bash
# Render deployment start script for backend

cd backend
uvicorn server:app --host 0.0.0.0 --port ${PORT:-8000}
