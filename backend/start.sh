#!/bin/bash
echo "Iniciando FastAPI..."
uvicorn main:app --host 0.0.0.0 --port $PORT
