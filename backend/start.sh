#!/bin/bash

# Arrancar el servidor FastAPI
uvicorn backend.main:app --host 0.0.0.0 --port $PORT &

# Arrancar el servidor estático para React
npx serve -s frontend/build
