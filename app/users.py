"""Register users while enforcing database constraints and public serialization."""
from typing import Annotated
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session
from app.database import get_db
from app.models import User
from app.schemas import UserCreate, UserRead
from app.security import hash_password

router = APIRouter(prefix="/users", tags=["users"])

@router.post("", response_model=UserRead, status_code=201)
def register_user(data: UserCreate, db: Annotated[Session, Depends(get_db)]):
    user = User(username=data.username, email=str(data.email),
                password_hash=hash_password(data.password.get_secret_value()))
    db.add(user)
    try:
        db.commit()
    except IntegrityError:
        db.rollback()
        # The constraint, rather than a pre-insert check, also handles races.
        raise HTTPException(status_code=409, detail="Username or email already exists") from None
    db.refresh(user)
    return user
