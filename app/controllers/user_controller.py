from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.config.database import get_db
from app.services.auth_service import create_user, get_user_by_email
from pydantic import BaseModel

router = APIRouter(prefix="/users", tags=["users"])


class UserCreate(BaseModel):
    nome: str
    email: str
    password: str
    role: str = "FUNCIONARIO"


@router.post("/", status_code=201)
def criar_usuario(
    body: UserCreate,
    db: Session = Depends(get_db),
):
    if get_user_by_email(db, body.email):
        raise HTTPException(status_code=400, detail="E-mail já cadastrado")

    user = create_user(
        db,
        body.nome,
        body.email,
        body.password,
        body.role
    )

    return {
        "id": user.id,
        "email": user.email,
        "role": user.role
    }