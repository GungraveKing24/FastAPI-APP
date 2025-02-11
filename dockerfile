# Usa una imagen base de Python y Node.js
FROM python:3.11-slim

# Instala Node.js
RUN apt-get update && apt-get install -y nodejs npm

# Establece el directorio de trabajo
WORKDIR /app

# Copia y configura el backend
COPY backend/ backend/
RUN pip install -r backend/requirements.txt

# Copia y configura el frontend
COPY frontend/ frontend/
RUN cd frontend && npm install && npm run build

# Comando de inicio
CMD ["hypercorn", "backend.main:app", "--bind", "[::]:$PORT"]
