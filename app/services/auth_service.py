from sqlalchemy.orm import Session
from app.models.user_model import User
from app.config.security import verify_password, create_access_token, decode_access_token, hash_password

def get_user_by_email(db: Session, email: str):
    return db.query(User).filter(User.email == email).first()

def authenticate_user(db: Session, email: str, password: str):
    user = get_user_by_email(db, email)
    if not user:
        return None
    if not verify_password(password, user.hashed_password):
        return None
    return user

# ESSA É A FUNÇÃO QUE ESTÁ FALTANDO:
def create_user(db: Session, nome: str, email: str, password: str, role: str = "user"):
    hashed_pwd = hash_password(password)
    db_user = User(
        nome=nome,
        email=email,
        hashed_password=hashed_pwd,
        role=role
    )
    db.add(db_user)
    db.commit()
    db.refresh(db_user)
    return db_user