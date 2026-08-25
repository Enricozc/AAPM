import jwt

from datetime import datetime, timedelta

from typing import Optional

from passlib.context import CryptContext

from fastapi import Request, HTTPException

from app.config.settings import settings


# ============================================================
# CRIPTOGRAFIA
# ============================================================

pwd_context = CryptContext(
    schemes=["bcrypt"],
    deprecated="auto"
)


# ============================================================
# GERAR HASH DA SENHA
# ============================================================

def hash_password(password: str):

    return pwd_context.hash(password)


# ============================================================
# VERIFICAR SENHA
# ============================================================

def verify_password(
    plain_password: str,
    hashed_password: str
):

    return pwd_context.verify(
        plain_password,
        hashed_password
    )


# ============================================================
# GERAR TOKEN
# ============================================================

def create_access_token(
    data: dict,
    expires_delta: Optional[timedelta] = None
):

    to_encode = data.copy()

    if expires_delta:

        expire = datetime.utcnow() + expires_delta

    else:

        expire = (
            datetime.utcnow()
            + timedelta(
                minutes=settings.access_token_expire_minutes
            )
        )

    to_encode.update({
        "exp": expire
    })

    encoded_jwt = jwt.encode(
        to_encode,
        settings.secret_key,
        algorithm=settings.algorithm
    )

    return encoded_jwt


# ============================================================
# DECODIFICAR TOKEN
# ============================================================

def decode_access_token(token: str):

    try:

        payload = jwt.decode(
            token,
            settings.secret_key,
            algorithms=[
                settings.algorithm
            ]
        )

        return payload

    except jwt.PyJWTError:

        return None


# ============================================================
# USUÁRIO LOGADO
# ============================================================

def get_current_user(
    request: Request
):

    token = request.cookies.get(
        "access_token"
    )

    if not token:

        raise HTTPException(
            status_code=401,
            detail="Usuário não autenticado"
        )

    payload = decode_access_token(
        token
    )

    if not payload:

        raise HTTPException(
            status_code=401,
            detail="Token inválido"
        )

    return payload


# ============================================================
# SOMENTE ADMIN
# ============================================================

def require_admin(
    request: Request
):

    user = get_current_user(
        request
    )

    role = str(
        user.get("role", "")
    ).upper()

    if role != "ADMIN":

        raise HTTPException(
            status_code=403,
            detail="Acesso negado"
        )

    return user


# ============================================================
# USUÁRIO OPCIONAL
# ============================================================

def get_usuario_opcional(
    request: Request
):

    token = request.cookies.get(
        "access_token"
    )

    if not token:

        return None

    payload = decode_access_token(
        token
    )

    if not payload:

        return None

    return payload