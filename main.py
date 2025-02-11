from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

app = FastAPI()

# Configurar CORS para permitir peticiones desde el frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Cambiar en producción
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Base de datos simulada (puedes cambiar esto a SQLite o PostgreSQL en Railway)
games = [
    {"id": 1, "name": "The Legend of Zelda", "platform": "Nintendo"},
    {"id": 2, "name": "God of War", "platform": "PlayStation"},
    {"id": 3, "name": "Halo", "platform": "Xbox"},
]

@app.get("/games")
def get_games():
    return games
