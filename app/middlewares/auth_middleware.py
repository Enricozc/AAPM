from fastapi import Request, HTTPException
from fastapi.responses import RedirectResponse
from app.services.auth_service import decode_access_token


def get_current_user(request: Request) -> dict:
    """Lê o JWT do cookie e retorna o payload. Lança 401 se inválido."""
    token = request.cookies.get("access_token")
    if not token:
        raise HTTPException(status_code=401, detail="Não autenticado")
    payload = decode_access_token(token)
    if not payload:
        raise HTTPException(status_code=401, detail="Token inválido ou expirado")
    return payload


def require_admin(request: Request) -> dict:
    """Garante que o usuário autenticado tem role ADMIN."""
    user = get_current_user(request)
    if user.get("role") != "ADMIN":
        raise HTTPException(status_code=403, detail="Acesso restrito a administradores")
    return user