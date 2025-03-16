from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from starlette.middleware.sessions import SessionMiddleware
from starlette.requests import Request
from starlette.responses import RedirectResponse
from authlib.integrations.starlette_client import OAuth, OAuthError

from routes import user_routes, inventory_routes
from config import engine, CLIENT_ID, CLIENT_SECRET, GOOGLE_REDIRECT_URI, secret_key
from models.models import Base

import requests
# Configuración de la aplicación
app = FastAPI()
Base.metadata.create_all(bind=engine)

origins = [
    "http://localhost:5173",  # Frontend local
    "http://127.0.0.1:5173",  # Frontend local
    "http://127.0.0.1:8000",  # Backend local
    "http://localhost:8000",  # Backend local
]
app.add_middleware(SessionMiddleware, secret_key=secret_key)

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,  # Lista de orígenes permitidos
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE"],  # Agrega otros métodos según lo necesites
    allow_headers=["*"],  # Permite todos los encabezados
)


@app.get("/login")
async def login(request: Request):
    """Redirige a la página de autenticación de Google"""
    google_auth_url = (
        f"https://accounts.google.com/o/oauth2/v2/auth"
        f"?client_id={CLIENT_ID}"
        f"&redirect_uri={GOOGLE_REDIRECT_URI}"
        f"&response_type=code"
        f"&scope=openid email profile"
        f"&access_type=offline"
        f"&state=randomstate"
    )
    return RedirectResponse(google_auth_url)

@app.get("/auth")
async def auth(request: Request):
    """Obtiene el token de Google usando la respuesta del código de autorización"""
    code = request.query_params.get("code")
    
    if not code:
        return JSONResponse(status_code=400, content={"message": "No code provided"})

    # Intercambiar el código por un token de acceso
    token_url = "https://oauth2.googleapis.com/token"
    data = {
        "code": code,
        "client_id": CLIENT_ID,
        "client_secret": CLIENT_SECRET,
        "redirect_uri": GOOGLE_REDIRECT_URI,
        "grant_type": "authorization_code",
    }
    response = requests.post(token_url, data=data)
    
    if response.status_code != 200:
        return JSONResponse(status_code=400, content={"message": "Error exchanging code for token"})
    
    token_data = response.json()
    access_token = token_data["access_token"]
    print("Access token:", access_token)
    
    # Obtener la información del usuario
    user_info_url = "https://www.googleapis.com/oauth2/v3/userinfo"
    headers = {"Authorization": f"Bearer {access_token}"}
    user_response = requests.get(user_info_url, headers=headers)

    if user_response.status_code != 200:
        return JSONResponse(status_code=400, content={"message": "Error fetching user info"})
    
    user_info = user_response.json()

    # Guardar la información del usuario en la sesión
    request.session['user'] = user_info

    # Redirigir al frontend sin pasar los datos por la URL
    return RedirectResponse("http://localhost:5173/profile")  # Redirige a una página segura

@app.get('/logout')
def logout(request: Request):
    """Cerrar sesión y redirigir al frontend"""
    request.session.pop('user', None)  # Elimina al usuario de la sesión
    return RedirectResponse("http://localhost:5173")

@app.get('/profile')
async def profile(request: Request):
    """Ruta para obtener la información del usuario autenticado"""
    user = request.session.get('user')
    if user:
        return JSONResponse(content=user)  # Devuelve los datos del usuario como respuesta JSON
    return RedirectResponse("http://localhost:5173/login")

app.include_router(user_routes.router)
app.include_router(inventory_routes.router)
