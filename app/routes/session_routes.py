from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from models.models import User
from config import SessionLocal
from schemas.schemas import UserLogin, Token

router = APIRouter(
    prefix="/session",
    tags=["session"]
)

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

@router.get("/", response_model=UserLogin)
async def get_user_verification(user: UserLogin, db: Session = Depends(get_db)):
    db_user = db.query(User).filter(User.user_email == user.user_email).first()
    if not db_user:
        raise HTTPException(status_code=400, detail="El correo no esta registrado")
    elif db_user.user_password != user.user_password:
        raise HTTPException(status_code=400, detail="La contraseña es incorrecta")
    else:
        raise HTTPException(status_code=200, detail="El correo y la contraseña son correctos")