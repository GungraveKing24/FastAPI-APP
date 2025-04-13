from fastapi import APIRouter, Depends, HTTPException 
from fastapi.responses import RedirectResponse 
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session
from models.models import User
from schemas.schemas import UserCreate, UserLogin, UserGoogleAuth

from services.cifrar import hash_password, verify_password
from services.jwt import create_access_token, verify_jwt_token
from typing import Optional

from config import GOOGLE_REDIRECT_URI, CLIENT_ID, CLIENT_SECRET, SessionLocal, F_URL
import httpx
from urllib.parse import urlencode

router = APIRouter()

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

#Login manual
@router.post("/login")
async def login_user(user_data: UserLogin, db: Session = Depends(get_db)):
    user = db.query(User).filter(User.user_email == user_data.user_email).first()

    # Verificar si el usuario existe
    if not user:
        raise HTTPException(status_code=400, detail="Credenciales incorrectas")

    # Verificar si el usuario se registró con Google (no tiene contraseña)
    if not user.user_password:
        raise HTTPException(
            status_code=400,
            detail="Este usuario se registró con Google. Por favor, inicia sesión con Google."
        )

    # Verificar la contraseña
    if not verify_password(user_data.user_password, user.user_password):
        raise HTTPException(status_code=400, detail="Credenciales incorrectas")

    # Generar el token JWT
    access_token = create_access_token({
        "sub": user.id,
        "email": user.user_email,
        "user_name": user.user_name,
        "user_number": user.user_number,
        "user_direction": user.user_direction,
        "user_role": user.user_role,
        "user_url_photo": user.user_url_photo
    })

    return {"token": access_token}

#Registro manual
@router.post("/register")
async def register(user_data: UserCreate, db: Session = Depends(get_db)):
    existing_user = db.query(User).filter(User.user_email == user_data.user_email).first()
    if existing_user:
        raise HTTPException(status_code=400, detail="Este correo ya existe, por favor inicie sesión")

    hashed_password = hash_password(user_data.user_password)
    print(user_data.user_name, user_data.user_email, user_data.user_password, user_data.user_role, user_data.user_direction, user_data.user_number)
    new_user = User(
        user_name=user_data.user_name,
        user_email=user_data.user_email,
        user_password=hashed_password,
        user_number=user_data.user_number,
        user_direction=user_data.user_direction
    )

    db.add(new_user)
    db.commit()
    db.refresh(new_user)

    return {"message": "Usuario registrado exitosamente"}

@router.get("/google/login")
async def google_login(callback_url: str = F_URL + "/google/callback"):
    # Verifica que la callback_url sea válida
    if not callback_url.startswith((F_URL)):
        callback_url = F_URL + "/google/callback"
    
    auth_url = (
        "https://accounts.google.com/o/oauth2/v2/auth?"
        + urlencode({
            "client_id": CLIENT_ID,
            "redirect_uri": GOOGLE_REDIRECT_URI,
            "response_type": "code",
            "scope": "openid profile email",
            "state": callback_url,
            "access_type": "offline",
            "prompt": "consent"
        })
    )
    return RedirectResponse(url=auth_url)

@router.get("/google/callback")
async def google_callback(code: str, state: str, db: Session = Depends(get_db)): 
    try:
        callback_url = state
        async with httpx.AsyncClient() as client:
            # Obtener el token de acceso
            token_response = await client.post(
                "https://oauth2.googleapis.com/token",
                data={
                    "code": code,
                    "client_id": CLIENT_ID,
                    "client_secret": CLIENT_SECRET,
                    "redirect_uri": GOOGLE_REDIRECT_URI,
                    "grant_type": "authorization_code",
                },
            )
            
            token_data = token_response.json()

            if "access_token" not in token_data:
                error_url = f"{callback_url}?error=Error al obtener el token de acceso"
                return RedirectResponse(url=error_url)

            access_token = token_data["access_token"]

            # Obtener información del usuario
            userinfo_response = await client.get(
                "https://www.googleapis.com/oauth2/v3/userinfo",
                headers={"Authorization": f"Bearer {access_token}"},
            )
            userinfo = userinfo_response.json()

            if "email" not in userinfo:
                error_url = f"{callback_url}?error=No se pudo obtener el correo del usuario"
                return RedirectResponse(url=error_url)

            # Buscar o crear usuario
            user = db.query(User).filter(User.user_email == userinfo["email"]).first()
            if not user:
                new_user = User(
                    user_name=userinfo.get("name", "Usuario de Google"),
                    user_email=userinfo["email"],
                    user_password="",
                    user_url_photo=userinfo.get("picture", ""),
                    user_number="",
                    user_role="Cliente",
                    user_direction="",
                    user_google_id=userinfo.get("sub", "")
                )
                db.add(new_user)
                db.commit()
                db.refresh(new_user)
                user = new_user

            # Generar JWT
            access_token = create_access_token({
                "sub": user.id,
                "email": user.user_email,
                "user_name": user.user_name,
                "user_number": user.user_number,
                "user_direction": user.user_direction,
                "user_role": user.user_role,
                "user_url_photo": user.user_url_photo
            })

            # Redirigir al frontend
            redirect_url = f"{callback_url}?token={access_token}"
            return RedirectResponse(url=redirect_url)

    except Exception as e:
        print("Error en la autenticación:", str(e))
        error_url = f"{callback_url}?error=Error interno del servidor"
        return RedirectResponse(url=error_url)