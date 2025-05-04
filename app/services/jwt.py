from fastapi import HTTPException, Depends
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from config import secret_key
from datetime import timedelta, datetime
import jwt
from typing import Optional

security = HTTPBearer()

def create_access_token(data: dict):
    to_encode = data.copy()
    # Asegurar que 'sub' sea string
    if 'sub' in to_encode:
        to_encode['sub'] = str(to_encode['sub'])  # Conversión explícita a string
    expire = datetime.utcnow() + timedelta(minutes=60)
    to_encode.update({"exp": expire})
    return jwt.encode(to_encode, secret_key, algorithm="HS256")

def verify_jwt_token(token: str):
    try:
        # Decodificar sin verificar inicialmente el tipo de 'sub'
        payload = jwt.decode(token, secret_key, algorithms=["HS256"], options={"verify_sub": False})
        
        # Conversión forzada de 'sub' a string si es necesario
        if 'sub' in payload and not isinstance(payload['sub'], str):
            payload['sub'] = str(payload['sub'])
            
        return payload
    except jwt.ExpiredSignatureError:
        raise HTTPException(status_code=401, detail="Token expirado")
    except jwt.InvalidTokenError:
        raise HTTPException(status_code=401, detail="Token inválido")

def get_current_user(token: str = Depends(security)):
    try:
        payload = verify_jwt_token(token.credentials)
        
        # Aceptar tanto string como número en 'sub'
        user_id = int(payload.get('sub')) if payload.get('sub') else None
        if not user_id:
            raise HTTPException(status_code=401, detail="Invalid user ID")
            
        return {"id": user_id, **payload}
    except ValueError:
        raise HTTPException(status_code=401, detail="Invalid user ID format")