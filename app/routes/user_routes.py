from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.models.models import User, Inventory

from app.config import SessionLocal
from app.schemas.schemas import UserCreate, UserResponse

router = APIRouter(
    prefix="/users",
    tags=["users"]
)

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

@router.post("/", response_model=UserResponse)
def create_user(user: UserCreate, db:Session = Depends(get_db)):
    #Si el usuario ya existe, no se puede crear
    existing_user = db.query(User).filter(User.user_email == user.user_email).first()
    if existing_user:
        raise HTTPException(status_code=400, detail="El correo ya está registrado")

    new_user = User(**user.model_dump())  # Convertir Pydantic a SQLAlchemy
    db.add(new_user)
    db.commit()
    db.refresh(new_user)
    return new_user

@router.get("/", response_model=list[UserResponse])
def get_users(db: Session = Depends(get_db)):
    users = db.query(User).all()
    return users