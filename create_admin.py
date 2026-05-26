from app.config.database import SessionLocal
from app.services.auth_service import create_user

db = SessionLocal()

create_user(
    db=db,
    nome="Administrador",
    email="admin@senai.com",
    password="123",
    role="ADMIN"
)

print("Usuário criado com sucesso!")z