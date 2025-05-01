from fastapi import FastAPI, APIRouter, HTTPException, status, Depends 
from sqlalchemy.orm import Session
from models.models import User
from services.jwt import get_current_user
from config import SessionLocal
from schemas.s_usuarios import users_data 

router = APIRouter()

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

@router.get("/Users", response_model=list[users_data])
async def get_users(current_user: dict = Depends(get_current_user), db: Session = Depends(get_db)):
    if current_user["user_role"] != "Administrador":
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="No autorizado")
    users = db.query(User).filter(User.user_role != "Administrador").all()

    # Convert the data to match the schema
    return [
        {
            **user.__dict__,
            "user_register_date": str(user.user_register_date),  # Convert datetime to string
            "user_account_state": bool(user.user_account_state) if user.user_account_state is not None else False
        }
        for user in users
    ]