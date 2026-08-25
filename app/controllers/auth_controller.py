import smtplib
import secrets
from email.message import EmailMessage
from datetime import timedelta

from fastapi import APIRouter, Depends, Request, Form, status
from fastapi.responses import RedirectResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session

from app.config.database import get_db
from app.config.settings import settings
from app.models.user_model import Usuario
from app.config.security import (
    hash_password,
    verify_password,
    create_access_token,
    decode_access_token,
    get_usuario_opcional,
)


router = APIRouter(
    prefix="/auth",
    tags=["Autenticação"]
)

templates = Jinja2Templates(
    directory="app/templates"
)


# ============================================================
# LOGIN
# ============================================================

@router.get("/login")
def tela_login(request: Request):
    return templates.TemplateResponse(
        request=request,
        name="auth/login.html",
        context={
            "request": request,
            "erro": None,
            "sucesso": None,
        }
    )


# ============================================================
# FAZER LOGIN
# ============================================================

@router.post("/login")
def login(
    request: Request,
    email: str = Form(...),
    senha: str = Form(...),
    db: Session = Depends(get_db)
):

    email = email.strip().lower()

    usuario = (
        db.query(Usuario)
        .filter(Usuario.email == email)
        .first()
    )

    # --------------------------------------------------------
    # USUÁRIO NÃO ENCONTRADO / SENHA ERRADA
    # --------------------------------------------------------

    if not usuario or not verify_password(
        senha,
        usuario.hashed_password
    ):

        return templates.TemplateResponse(
            request=request,
            name="auth/login.html",
            context={
                "request": request,
                "erro": "E-mail ou senha incorretos.",
                "sucesso": None,
            },
            status_code=401
        )

    # --------------------------------------------------------
    # USUÁRIO INATIVO
    # --------------------------------------------------------

    if not usuario.ativo:

        return templates.TemplateResponse(
            request=request,
            name="auth/login.html",
            context={
                "request": request,
                "erro": "Usuário inativo. Contate o administrador.",
                "sucesso": None,
            },
            status_code=403
        )

    # --------------------------------------------------------
    # CRIAR TOKEN
    # --------------------------------------------------------

    token = create_access_token({
        "sub": usuario.email,
        "nome": usuario.nome,
        "role": usuario.role,
        "id": usuario.id,
    })

    # --------------------------------------------------------
    # REDIRECIONAR
    # --------------------------------------------------------

    response = RedirectResponse(
        url="/",
        status_code=status.HTTP_303_SEE_OTHER
    )

    response.set_cookie(
        key="access_token",
        value=token,
        httponly=True,
        max_age=3600,
        samesite="lax",
        secure=False
    )

    return response


# ============================================================
# LOGOUT
# ============================================================

@router.get("/logout")
def logout():

    response = RedirectResponse(
        url="/auth/login",
        status_code=status.HTTP_303_SEE_OTHER
    )

    response.delete_cookie("access_token")

    return response


# ============================================================
# RECUPERAÇÃO DE SENHA
# ============================================================

@router.post("/forgot-password")
def forgot_password(
    request: Request,
    email: str = Form(...),
    db: Session = Depends(get_db)
):

    email = email.strip().lower()

    usuario = (
        db.query(Usuario)
        .filter(Usuario.email == email)
        .first()
    )

    # --------------------------------------------------------
    # NÃO REVELAR SE O E-MAIL EXISTE
    # --------------------------------------------------------

    if not usuario:

        return templates.TemplateResponse(
            request=request,
            name="auth/login.html",
            context={
                "request": request,
                "erro": None,
                "sucesso": (
                    "Se o e-mail estiver cadastrado, "
                    "você receberá um link para redefinir sua senha."
                )
            }
        )

    # --------------------------------------------------------
    # TOKEN DE RECUPERAÇÃO
    # --------------------------------------------------------

    reset_token = create_access_token(
        {
            "type": "password_reset",
            "id": usuario.id,
            "email": usuario.email,
            "nonce": secrets.token_hex(16),
        },
        expires_delta=timedelta(minutes=15)
    )

    # --------------------------------------------------------
    # URL DE RECUPERAÇÃO
    # --------------------------------------------------------

    base_url = "http://127.0.0.1:8000"

    reset_url = (
        f"{base_url}/auth/reset-password"
        f"?token={reset_token}"
    )

    # --------------------------------------------------------
    # ENVIAR E-MAIL
    # --------------------------------------------------------

    try:

        enviar_email_recuperacao(
            destinatario=usuario.email,
            nome=usuario.nome,
            link=reset_url
        )

    except Exception as e:

        print("=" * 60)
        print("ERRO AO ENVIAR E-MAIL")
        print(e)
        print("=" * 60)

        return templates.TemplateResponse(
            request=request,
            name="auth/login.html",
            context={
                "request": request,
                "erro": (
                    "Não foi possível enviar o e-mail de recuperação. "
                    "Verifique a configuração de e-mail."
                ),
                "sucesso": None,
            },
            status_code=500
        )

    # --------------------------------------------------------
    # SUCESSO
    # --------------------------------------------------------

    return templates.TemplateResponse(
        request=request,
        name="auth/login.html",
        context={
            "request": request,
            "erro": None,
            "sucesso": (
                "Enviamos um link de recuperação "
                "para o seu e-mail."
            )
        }
    )


# ============================================================
# ENVIAR E-MAIL
# ============================================================

def enviar_email_recuperacao(
    destinatario: str,
    nome: str,
    link: str
):

    smtp_host = settings.smtp_server

    smtp_port = settings.smtp_port

    smtp_email = settings.smtp_email

    smtp_password = settings.smtp_password

    if not smtp_email or not smtp_password:

        raise Exception(
            "SMTP_EMAIL ou SMTP_PASSWORD não configurado no .env"
        )

    mensagem = EmailMessage()

    mensagem["Subject"] = "AAPM SENAI - Recuperação de senha"
    mensagem["From"] = smtp_email
    mensagem["To"] = destinatario

    mensagem.set_content(
        f"""
Olá, {nome}!

Recebemos uma solicitação para redefinir a senha
da sua conta no sistema AAPM SENAI.

Clique no link abaixo para criar uma nova senha:

{link}

Este link ficará válido por 15 minutos.

Se você não solicitou a recuperação da senha,
ignore este e-mail.

Atenciosamente,

AAPM SENAI
Sistema de Gestão
        """
    )

    with smtplib.SMTP(
        smtp_host,
        smtp_port
    ) as servidor:

        servidor.starttls()

        servidor.login(
            smtp_email,
            smtp_password
        )

        servidor.send_message(
            mensagem
        )


# ============================================================
# TELA DE NOVA SENHA
# ============================================================

@router.get("/reset-password")
def tela_reset_password(
    request: Request,
    token: str
):

    payload = decode_access_token(token)

    # --------------------------------------------------------
    # TOKEN INVÁLIDO
    # --------------------------------------------------------

    if not payload:

        return templates.TemplateResponse(
            request=request,
            name="auth/reset_password.html",
            context={
                "request": request,
                "erro": "O link é inválido ou expirou.",
                "token": None,
            },
            status_code=400
        )

    # --------------------------------------------------------
    # VERIFICAR TIPO
    # --------------------------------------------------------

    if payload.get("type") != "password_reset":

        return templates.TemplateResponse(
            request=request,
            name="auth/reset_password.html",
            context={
                "request": request,
                "erro": "Link de recuperação inválido.",
                "token": None,
            },
            status_code=400
        )

    return templates.TemplateResponse(
        request=request,
        name="auth/reset_password.html",
        context={
            "request": request,
            "erro": None,
            "token": token,
        }
    )


# ============================================================
# ALTERAR SENHA
# ============================================================

@router.post("/reset-password")
def reset_password(
    request: Request,
    token: str = Form(...),
    nova_senha: str = Form(...),
    confirmar_senha: str = Form(...),
    db: Session = Depends(get_db)
):

    # --------------------------------------------------------
    # VALIDAR TOKEN
    # --------------------------------------------------------

    payload = decode_access_token(token)

    if not payload:

        return templates.TemplateResponse(
            request=request,
            name="auth/reset_password.html",
            context={
                "request": request,
                "erro": "O link é inválido ou expirou.",
                "token": None,
            },
            status_code=400
        )

    # --------------------------------------------------------
    # VERIFICAR TIPO
    # --------------------------------------------------------

    if payload.get("type") != "password_reset":

        return templates.TemplateResponse(
            request=request,
            name="auth/reset_password.html",
            context={
                "request": request,
                "erro": "Link de recuperação inválido.",
                "token": None,
            },
            status_code=400
        )

    # --------------------------------------------------------
    # VALIDAR SENHA
    # --------------------------------------------------------

    if len(nova_senha) < 6:

        return templates.TemplateResponse(
            request=request,
            name="auth/reset_password.html",
            context={
                "request": request,
                "erro": "A senha deve ter pelo menos 6 caracteres.",
                "token": token,
            },
            status_code=400
        )

    if nova_senha != confirmar_senha:

        return templates.TemplateResponse(
            request=request,
            name="auth/reset_password.html",
            context={
                "request": request,
                "erro": "As senhas não são iguais.",
                "token": token,
            },
            status_code=400
        )

    # --------------------------------------------------------
    # BUSCAR USUÁRIO
    # --------------------------------------------------------

    usuario = (
        db.query(Usuario)
        .filter(
            Usuario.id == payload.get("id"),
            Usuario.email == payload.get("email")
        )
        .first()
    )

    if not usuario:

        return templates.TemplateResponse(
            request=request,
            name="auth/reset_password.html",
            context={
                "request": request,
                "erro": "Usuário não encontrado.",
                "token": None,
            },
            status_code=404
        )

    # --------------------------------------------------------
    # ALTERAR SENHA
    # --------------------------------------------------------

    usuario.hashed_password = hash_password(
        nova_senha
    )

    db.commit()

    # --------------------------------------------------------
    # VOLTAR PARA LOGIN
    # --------------------------------------------------------

    return RedirectResponse(
        url="/auth/login?senha_alterada=1",
        status_code=status.HTTP_303_SEE_OTHER
    )