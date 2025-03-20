from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import RedirectResponse
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session
from models.models import User
from schemas.schemas import UserCreate, UserLogin, UserGoogleAuth

from services.cifrar import hash_password, verify_password
from services.jwt import create_access_token, verify_jwt_token

from config import GOOGLE_REDIRECT_URI, CLIENT_ID, CLIENT_SECRET, SessionLocal
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
async def google_login():
    auth_url = (
        "https://accounts.google.com/o/oauth2/v2/auth?"
        + urlencode({
            "client_id": CLIENT_ID,
            "redirect_uri": GOOGLE_REDIRECT_URI,  # Asegúrate de que esta variable esté bien configurada
            "response_type": "code",
            "scope": "openid profile email",
        })
    )

    return RedirectResponse(url=auth_url)

@router.get("/google/callback")
async def google_callback(code: str, db: Session = Depends(get_db)):
    try:
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
                raise HTTPException(status_code=400, detail="Error al obtener el token de acceso")

            access_token = token_data["access_token"]

            # Obtener información del usuario
            userinfo_response = await client.get(
                "https://www.googleapis.com/oauth2/v3/userinfo",
                headers={"Authorization": f"Bearer {access_token}"},
            )
            userinfo = userinfo_response.json()

            if "email" not in userinfo:
                raise HTTPException(status_code=400, detail="No se pudo obtener el correo del usuario")

            # Buscar usuario en la base de datos
            user = db.query(User).filter(User.user_email == userinfo["email"]).first()
            if not user:
                # Crear un nuevo usuario si no existe
                new_user = User(
                    user_name=userinfo.get("name", "Usuario de Google"),
                    user_email=userinfo["email"],
                    user_password="",  # No se requiere contraseña para Google
                    user_url_photo=userinfo.get("picture", "https://lh3.googleusercontent.com/a/default-user=s96-c"),
                    user_number="",  # Placeholder, pedirlo después si es necesario
                    user_role="Cliente",
                    user_direction="",  # Placeholder, pedirlo después si es necesario
                    user_google_id=userinfo.get("sub", "ID_NO_PROVIDED")
                )
                db.add(new_user)
                db.commit()
                db.refresh(new_user)
                user = new_user

            # Generar un JWT para el usuario
            access_token = create_access_token({
                "sub": user.id,
                "email": user.user_email,
                "user_name": user.user_name,
                "user_number": user.user_number,
                "user_direction": user.user_direction,
                "user_role": user.user_role,
                "user_url_photo": user.user_url_photo
            })

            # Redirigir al frontend con el token en la URL
            redirect_url = f"http://localhost:5173/profile?token={access_token}"
            return RedirectResponse(url=redirect_url)

    except Exception as e:
        print("Error en la autenticación:", str(e))
        raise HTTPException(status_code=500, detail="Error interno del servidor")
