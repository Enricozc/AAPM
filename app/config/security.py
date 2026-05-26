import jwt
from datetime import datetime, timedelta
from typing import Optional
from passlib.context import CryptContext
from fastapi import Request, HTTPException

from app.config.settings import settings

# Criptografia de senha
pwd_context = CryptContext(
    schemes=["bcrypt"],
    deprecated="auto"
)


def hash_password(password: str) -> str:
    return pwd_context.hash(password)


def verify_password(
    plain_password: str,
    hashed_password: str
) -> bool:

    return pwd_context.verify(
        plain_password,
        hashed_password
    )


def create_access_token(
    data: dict,
    expires_delta: Optional[timedelta] = None
):

    to_encode = data.copy()

    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(
            minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES
        )

    to_encode.update(
        {"exp": expire}
    )

    encoded_jwt = jwt.encode(
        to_encode,
        settings.SECRET_KEY,
        algorithm=settings.ALGORITHM
    )

    return encoded_jwt


def decode_access_token(token: str):

    try:

        payload = jwt.decode(
            token,
            settings.SECRET_KEY,
            algorithms=[settings.ALGORITHM]
        )

        return payload

    except jwt.PyJWTError:
        return None


# Pega usuário logado
def get_current_user(request: Request):

    token = request.cookies.get(
        "access_token"
    )

    if not token:

        raise HTTPException(
            status_code=401,
            detail="Usuário não autenticado"
        )

    payload = decode_access_token(token)

    if not payload:

        raise HTTPException(
            status_code=401,
            detail="Token inválido"
        )

    return payload


# Permite apenas ADMIN
def require_admin(request: Request):

    user = get_current_user(
        request
    )

    if user.get("role") != "ADMIN":

        raise HTTPException(
            status_code=403,
            detail="Acesso negado"
        )

    return user