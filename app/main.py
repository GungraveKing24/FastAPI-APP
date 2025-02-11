from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

app = FastAPI()

# Configuración de CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["https://reactapp-production-d70d.up.railway.app", "*"],  # URL exacta del frontend
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Base de datos simulada para juegos
games = [
    {"id": 1, "name": "The Legend of Zelda", "platform": "Nintendo"},
    {"id": 2, "name": "God of War", "platform": "PlayStation"},
    {"id": 3, "name": "Halo", "platform": "Xbox"},
]

@app.get("/games")
def get_games():
    return games
