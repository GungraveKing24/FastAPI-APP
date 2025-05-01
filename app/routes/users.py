from fastapi import FastAPI, APIRouter, HTTPException, status, Depends 
from sqlalchemy.orm import Session
from models.models import User
from services.jwt import get_current_user
from config import SessionLocal

router = APIRouter()

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


@router.get("/Users")
async def get_users(current_user: dict = Depends(get_current_user), db: Session = Depends(get_db)):
    if current_user["user_role"] != "admin":
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="No autorizado")
    users = db.query(users).all()
    return users