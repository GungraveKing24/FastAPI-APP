from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from models.models import Comment, User, Arrangement
from schemas.s_comments import CommentCreate, CommentOut
from config import SessionLocal
from services.jwt import get_current_user

router = APIRouter()

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

@router.post("/Comments/{arrangements_id}", response_model=CommentOut)
async def create_comment(
    arrangements_id: int,
    comment: CommentCreate, 
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    if current_user["user_role"].lower() != "cliente":
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="No autorizado")

    user = db.query(User).filter(User.id == current_user["sub"]).first()
    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Usuario no encontrado")

    arrangement = db.query(Arrangement).filter(Arrangement.id == arrangements_id).first()
    if not arrangement:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Arreglo no encontrado")

    commentCreate = Comment(
        comment_user_id=current_user["sub"],
        comment_arrangement_id=arrangements_id,
        comment_text=comment.comment_text,
        comment_rating=comment.comment_rating
    )    

    db.add(commentCreate)
    db.commit()
    db.refresh(commentCreate)

    return commentCreate

@router.get("/Comments/{arrangements_id}", response_model=list[CommentOut])
async def get_comments(arrangements_id: int, db: Session = Depends(get_db)):
    arrangement = db.query(Arrangement).filter(Arrangement.id == arrangements_id).first()
    if not arrangement:
        raise HTTPException(status_code=404, detail="Arreglo no encontrado")

    comments_query = (
        db.query(Comment, User.user_name)
        .join(User, Comment.comment_user_id == User.id)
        .filter(Comment.comment_arrangement_id == arrangements_id)
        .order_by(Comment.comment_date.desc())
        .all()
    )

    comments_out = [
        CommentOut(
            user_name=user_name,
            comment_text=comment.comment_text,
            comment_rating=comment.comment_rating
        )
        for comment, user_name in comments_query
    ]

    return comments_out