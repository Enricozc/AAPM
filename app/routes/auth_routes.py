from fastapi import APIRouter, Depends, Request, Form, status
from fastapi.responses import RedirectResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session

from app.config.database import get_db
from app.models.user_model import Usuario
from app.config.security import hash_password, verify_password, create_access_token, get_usuario_opcional

router = APIRouter(prefix="/auth", tags=["Autenticação"])
templates = Jinja2Templates(directory="app/templates")


@router.get("/login")
def tela_login(request: Request):
    return templates.TemplateResponse(request, "auth/login.html", {"request": request})


@router.post("/login")
def login(
    request: Request,
    email: str = Form(...),
    senha: str = Form(...),
    db: Session = Depends(get_db)
):
    usuario = db.query(Usuario).filter(Usuario.email == email).first()

    if not usuario or not verify_password(senha, usuario.hashed_password):
        return templates.TemplateResponse(
            request, "auth/login.html",
            {"request": request, "erro": "E-mail ou senha incorretos."},
            status_code=401
        )

    if not usuario.ativo:
        return templates.TemplateResponse(
            request, "auth/login.html",
            {"request": request, "erro": "Usuário inativo. Contate o administrador."},
            status_code=403
        )

    token = create_access_token({
        "sub":  usuario.email,
        "nome": usuario.nome,
        "role": usuario.role,
        "id":   usuario.id,
    })

    response = RedirectResponse(url="/", status_code=status.HTTP_303_SEE_OTHER)
    response.set_cookie(
        key="access_token",
        value=token,
        httponly=True,
        max_age=3600,
        samesite="lax"
    )
    return response


@router.get("/logout")
def logout():
    response = RedirectResponse(url="/auth/login", status_code=status.HTTP_303_SEE_OTHER)
    response.delete_cookie("access_token")
    return response