#!/bin/bash

# Verificar si pip está disponible
if ! command -v pip &> /dev/null
then
    echo "pip no encontrado, instalando..."
    python -m ensurepip --default-pip
    python -m pip install --upgrade pip
fi

# Instalar dependencias
pip install -r requirements.txt

# Iniciar FastAPI con uvicorn
uvicorn main:app --host 0.0.0.0 --port $PORT
