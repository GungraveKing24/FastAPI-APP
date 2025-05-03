from fastapi import APIRouter, Depends, HTTPException, File, UploadFile, Form, Body, status 
from fastapi.responses import RedirectResponse 
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session
from models.models import User
from schemas.schemas import UserCreate, UserLogin, UserGoogleAuth

from services.cifrar import hash_password, verify_password
from services.jwt import create_access_token, verify_jwt_token, get_current_user
from services.cloudinary import upload_file
from typing import Optional

from config import GOOGLE_REDIRECT_URI, CLIENT_ID, CLIENT_SECRET, SessionLocal, F_URL
import httpx, uuid
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
async def register(
        user_name: str = Form(...),
        user_email: str = Form(...),
        user_password: str = Form(...),
        user_number: str = Form(...),
        user_direction: str = Form(...),
        image: Optional[UploadFile] = File(None),  # Hacer el parámetro opcional
        db: Session = Depends(get_db)
    ):
    # Verificar si ya existe el usuario por correo
    existing_user = db.query(User).filter(User.user_email == user_email).first()
    if existing_user:
        raise HTTPException(status_code=400, detail="Este correo ya existe, por favor inicie sesión")

    # URL de imagen por defecto
    default_image_url = "https://res.cloudinary.com/demo/image/upload/c_scale,w_200/d_avatar.png/non_existing_id.png"
    image_url = default_image_url

    # Procesar imagen solo si se proporcionó
    if image is not None:
        # Verificar que sea una imagen
        if not image.content_type.startswith("image/"):
            raise HTTPException(status_code=400, detail="El archivo debe ser una imagen.")

        # Subir la imagen a Cloudinary
        uploaded_url = await upload_file(image)
        if uploaded_url:
            image_url = uploaded_url

    # Hashear contraseña
    hashed_email = hash_password(user_email)
    hashed_password = hash_password(user_password)

    # Crear usuario
    new_user = User(
        user_name=user_name,
        user_email=user_email,
        user_password=hashed_password,
        user_number=user_number,
        user_direction=user_direction,
        user_url_photo=image_url,
        user_role="Cliente"
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

            # Generate random unnaccessable password
            raw_password = str(uuid.uuid4())
            
            hashed_password = hash_password(raw_password)
            
            # Buscar o crear usuario
            user = db.query(User).filter(User.user_email == userinfo["email"]).first()
            if not user:
                new_user = User(
                    user_name=userinfo.get("name", "Usuario de Google"),
                    user_email=userinfo["email"],
                    user_password=hashed_password,
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
    
@router.patch("/user/update")
async def update_user_data(
    current_user: dict = Depends(get_current_user),
    user_name: Optional[str] = Form(None),
    user_number: Optional[str] = Form(None),
    user_direction: Optional[str] = Form(None),
    image: Optional[UploadFile] = File(None),
    db: Session = Depends(get_db)
):
    
    print(f"user_name: {user_name}")
    print(f"user_number: {user_number}")
    print(f"user_direction: {user_direction}")
    print(f"image: {image}")

    # Verificar rol del usuario si es necesario
    if current_user["user_role"] != "Cliente":
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Solo los clientes pueden actualizar sus datos")
    
    # Obtener usuario de la base de datos
    user = db.query(User).filter(User.id == current_user["sub"]).first()
    
    return None

@router.patch("/user/password")
async def update_user_password(
    current_user: dict = Depends(get_current_user), 
    old_password: str = Form(...),
    new_password: str = Form(...),
    confirm_password: str = Form(...),
    db: Session = Depends(get_db)
):

    # Verificar rol del usuario
    if current_user["user_role"] != "Cliente":
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Solo los clientes pueden cambiar su contraseña"
        )
    
    # Obtener usuario de la base de datos
    user = db.query(User).filter(User.id == current_user["sub"]).first()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Usuario no encontrado"
        )
    
    # Verificar contraseña actual
    if not verify_password(old_password, user.user_password):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="La contraseña actual no es correcta"
        )
    
    # Validar coincidencia de nuevas contraseñas
    if new_password != confirm_password:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Las nuevas contraseñas no coinciden"
        )
    
    # Verificar que la nueva contraseña sea diferente
    if verify_password(new_password, user.user_password):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="La nueva contraseña debe ser diferente a la actual"
        )
    
    # Validar fortaleza de la nueva contraseña (mínimo 8 caracteres)
    if len(new_password) < 8:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="La contraseña debe tener al menos 8 caracteres"
        )
    
    # Actualizar contraseña
    user.user_password = hash_password(new_password)
    db.commit()
    
    return {
        "message": "Contraseña actualizada correctamente",
        "status": "success"
    }