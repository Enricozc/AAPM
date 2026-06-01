import os
from pathlib import Path

from fastapi import APIRouter, Depends, Request, Form, status
from fastapi.responses import RedirectResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session

from app.config.database import get_db
from app.models.user_model import Usuario
from app.config.security import hash_password, verify_password, create_access_token, get_usuario_opcional

router = APIRouter(prefix="/auth", tags=["Autenticação"])

templates = Jinja2Templates(directory="app/templates")

# ============================================================
# 🔒 REQUISITO 1: CONTROLE DE ACESSO PARA CADASTRO DE USUÁRIOS
# ============================================================

@router.get("/cadastro")
def tela_cadastro(
    request: Request,
    usuario=Depends(get_usuario_opcional)
):
    # 🛑 SEGURANÇA: Se o usuário não estiver logado ou não for ADMIN, barra
    if not usuario or usuario.get("role") != "ADMIN":
        return templates.TemplateResponse(
            request,
            "dashboard.html",  # Mantido na raiz de templates
            {
                "request": request,
                "usuario": usuario,
                "erro": "Acesso negado. Apenas administradores podem acessar a tela de cadastro."
            }
        )

    # 📁 CAMINHO CORRIGIDO: O seu HTML de cadastro fica na pasta 'usuarios' ou 'auth'
    # Olhando seu print, se o arquivo estiver em 'usuarios/cadastro.html':
    return templates.TemplateResponse(
        request,
        "usuarios/cadastro.html",  # ✅ Ajustado para a subpasta real do projeto
        {
            "request": request,
            "usuario": usuario
        }
    )


@router.post("/cadastro")
def fazer_cadastro(
    request: Request,
    nome: str = Form(...),
    email: str = Form(...),
    senha: str = Form(...),
    role: str = Form(...),  
    db: Session = Depends(get_db),
    usuario_logado=Depends(get_usuario_opcional)
):
    if not usuario_logado or usuario_logado.get("role") != "ADMIN":
        return RedirectResponse(url="/", status_code=status.HTTP_303_SEE_OTHER)

    usuario_existente = db.query(Usuario).filter(
        Usuario.email == email
    ).first()

    if usuario_existente:
        return templates.TemplateResponse(
            request,
            "usuarios/cadastro.html",  # ✅ Ajustado para a subpasta real
            {
                "request": request,
                "usuario": usuario_logado,
                "erro": "Este e-mail já está cadastrado."
            }
        )

    novo_usuario = Usuario(
        nome=nome,
        email=email,
        hashed_password=hash_password(senha),
        role=role,       
        is_active=True   
    )

    db.add(novo_usuario)
    db.commit()

    return RedirectResponse(
        url="/?cadastro=sucesso",
        status_code=status.HTTP_303_SEE_OTHER
    )


# ============================================================
# 🔑 LOGIN E LOGOUT (CAMINHOS DE PASTAS CORRIGIDOS)
# ============================================================

@router.get("/login")
def tela_login(request: Request):
    # 📁 CAMINHO CORRIGIDO: O login está dentro da pasta 'auth/'
    return templates.TemplateResponse(
        request,
        "auth/login.html",  # ✅ Resolve o erro TemplateNotFound
        {"request": request}
    )


@router.post("/login")
def login(
    request: Request,
    email: str = Form(...),
    senha: str = Form(...),
    db: Session = Depends(get_db)
):
    usuario = db.query(Usuario).filter(
        Usuario.email == email
    ).first()

    if not usuario:
        return templates.TemplateResponse(
            request,
            "auth/login.html",  # ✅ Ajustado para a subpasta real
            {
                "request": request,
                "erro": "E-mail ou senha incorretos."
            },
            status_code=401
        )

    if not verify_password(senha, usuario.hashed_password):
        return templates.TemplateResponse(
            request,
            "auth/login.html",  # ✅ Ajustado para a subpasta real
            {
                "request": request,
                "erro": "E-mail ou senha incorretos."
            },
            status_code=401
        )

    token = create_access_token(
        {
            "sub": usuario.email,
            "nome": usuario.nome,
            "role": usuario.role,
            "id": usuario.id
        }
    )

    response = RedirectResponse(
        url="/",
        status_code=status.HTTP_303_SEE_OTHER
    )

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
    response = RedirectResponse(
        url="/auth/login",
        status_code=status.HTTP_303_SEE_OTHER
    )
    response.delete_cookie("access_token")
    return response