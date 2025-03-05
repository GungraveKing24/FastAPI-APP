from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from config import engine
from models.models import Base
from routes import user_routes

# Configuración de la aplicación
app = FastAPI()
Base.metadata.create_all(bind=engine)

origin = "http://localhost:0000, http://127.0.0.1:0000"

app.add_middleware(
    CORSMiddleware,
    allow_origins=origin,
    allow_credentials=True,
    allow_methods=["GET", "POST"],
    allow_headers=["*"],    
)

app.include_router(user_routes.router)