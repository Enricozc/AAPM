import secrets

from datetime import datetime, timedelta

from fastapi import (
    APIRouter,
    Depends,
    Request,
    Form,
    status
)

from fastapi.responses import RedirectResponse

from fastapi.templating import Jinja2Templates

from sqlalchemy.orm import Session

from app.config.database import get_db

from app.models.user_model import Usuario

from app.models.password_reset_model import PasswordResetToken

from app.config.security import (
    hash_password,
    verify_password,
    create_access_token,
    get_usuario_opcional
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
def tela_login(
    request: Request
):

    return templates.TemplateResponse(
        request,
        "auth/login.html",
        {
            "request": request
        }
    )


# ============================================================
# PROCESSAR LOGIN
# ============================================================

@router.post("/login")
def login(

    request: Request,

    email: str = Form(...),

    senha: str = Form(...),

    db: Session = Depends(get_db)

):

    usuario = (
        db.query(Usuario)
        .filter(Usuario.email == email)
        .first()
    )


    if not usuario or not verify_password(
        senha,
        usuario.hashed_password
    ):

        return templates.TemplateResponse(

            request,

            "auth/login.html",

            {
                "request": request,

                "erro":
                "E-mail ou senha incorretos."
            },

            status_code=401
        )


    if not usuario.ativo:

        return templates.TemplateResponse(

            request,

            "auth/login.html",

            {
                "request": request,

                "erro":
                "Usuário inativo. Contate o administrador."
            },

            status_code=403
        )


    token = create_access_token({

        "sub": usuario.email,

        "nome": usuario.nome,

        "role": usuario.role,

        "id": usuario.id

    })


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

    response.delete_cookie(
        "access_token"
    )

    return response


# ============================================================
# ESQUECI MINHA SENHA
# ============================================================

@router.get("/forgot-password")
def forgot_password_page(
    request: Request
):

    return templates.TemplateResponse(

        request,

        "auth/forgot_password.html",

        {
            "request": request
        }

    )


# ============================================================
# PROCESSAR ESQUECI MINHA SENHA
# ============================================================

@router.post("/forgot-password")
def forgot_password(

    request: Request,

    email: str = Form(...),

    db: Session = Depends(get_db)

):

    usuario = (

        db.query(Usuario)

        .filter(
            Usuario.email == email
        )

        .first()

    )


    # --------------------------------------------------------
    # Por segurança, não informamos se o e-mail existe
    # --------------------------------------------------------

    mensagem = (
        "Se o e-mail estiver cadastrado, "
        "um link de recuperação será disponibilizado."
    )


    if not usuario:

        return templates.TemplateResponse(

            request,

            "auth/forgot_password.html",

            {
                "request": request,

                "mensagem": mensagem
            }

        )


    # --------------------------------------------------------
    # Remove tokens antigos desse usuário
    # --------------------------------------------------------

    db.query(
        PasswordResetToken
    ).filter(
        PasswordResetToken.usuario_id == usuario.id
    ).delete()


    # --------------------------------------------------------
    # Cria token aleatório seguro
    # --------------------------------------------------------

    token = secrets.token_urlsafe(48)


    # --------------------------------------------------------
    # Token válido por 30 minutos
    # --------------------------------------------------------

    expira_em = (
        datetime.utcnow()
        + timedelta(minutes=30)
    )


    reset_token = PasswordResetToken(

        usuario_id=usuario.id,

        token=token,

        expira_em=expira_em

    )


    db.add(reset_token)

    db.commit()


    # --------------------------------------------------------
    # Link de recuperação
    # --------------------------------------------------------

    reset_url = (
        f"{request.base_url}"
        f"auth/reset-password?token={token}"
    )


    print("")
    print("=" * 70)
    print("LINK PARA REDEFINIR A SENHA")
    print(reset_url)
    print("=" * 70)
    print("")


    return templates.TemplateResponse(

        request,

        "auth/forgot_password.html",

        {

            "request": request,

            "mensagem": mensagem,

            "reset_url": reset_url

        }

    )


# ============================================================
# TELA DE NOVA SENHA
# ============================================================

@router.get("/reset-password")
def reset_password_page(

    request: Request,

    token: str,

    db: Session = Depends(get_db)

):

    reset_token = (

        db.query(PasswordResetToken)

        .filter(
            PasswordResetToken.token == token
        )

        .first()

    )


    if not reset_token:

        return templates.TemplateResponse(

            request,

            "auth/reset_password.html",

            {

                "request": request,

                "erro":
                "Link de recuperação inválido."

            },

            status_code=400

        )


    if reset_token.expira_em < datetime.utcnow():

        db.delete(reset_token)

        db.commit()


        return templates.TemplateResponse(

            request,

            "auth/reset_password.html",

            {

                "request": request,

                "erro":
                "Este link de recuperação expirou."

            },

            status_code=400

        )


    return templates.TemplateResponse(

        request,

        "auth/reset_password.html",

        {

            "request": request,

            "token": token

        }

    )


# ============================================================
# SALVAR NOVA SENHA
# ============================================================

@router.post("/reset-password")
def reset_password(

    request: Request,

    token: str = Form(...),

    senha: str = Form(...),

    confirmar_senha: str = Form(...),

    db: Session = Depends(get_db)

):

    reset_token = (

        db.query(PasswordResetToken)

        .filter(
            PasswordResetToken.token == token
        )

        .first()

    )


    # --------------------------------------------------------
    # Verificar token
    # --------------------------------------------------------

    if not reset_token:

        return templates.TemplateResponse(

            request,

            "auth/reset_password.html",

            {

                "request": request,

                "erro":
                "Link de recuperação inválido."

            },

            status_code=400

        )


    # --------------------------------------------------------
    # Verificar validade
    # --------------------------------------------------------

    if reset_token.expira_em < datetime.utcnow():

        db.delete(reset_token)

        db.commit()


        return templates.TemplateResponse(

            request,

            "auth/reset_password.html",

            {

                "request": request,

                "erro":
                "Este link de recuperação expirou."

            },

            status_code=400

        )


    # --------------------------------------------------------
    # Verificar senha
    # --------------------------------------------------------

    if len(senha) < 6:

        return templates.TemplateResponse(

            request,

            "auth/reset_password.html",

            {

                "request": request,

                "token": token,

                "erro":
                "A senha precisa ter pelo menos 6 caracteres."

            },

            status_code=400

        )


    # --------------------------------------------------------
    # Confirmar senha
    # --------------------------------------------------------

    if senha != confirmar_senha:

        return templates.TemplateResponse(

            request,

            "auth/reset_password.html",

            {

                "request": request,

                "token": token,

                "erro":
                "As senhas não coincidem."

            },

            status_code=400

        )


    # --------------------------------------------------------
    # Buscar usuário
    # --------------------------------------------------------

    usuario = (

        db.query(Usuario)

        .filter(
            Usuario.id == reset_token.usuario_id
        )

        .first()

    )


    if not usuario:

        return templates.TemplateResponse(

            request,

            "auth/reset_password.html",

            {

                "request": request,

                "erro":
                "Usuário não encontrado."

            },

            status_code=400

        )


    # --------------------------------------------------------
    # Alterar senha
    # --------------------------------------------------------

    usuario.hashed_password = hash_password(
        senha
    )


    # --------------------------------------------------------
    # Token usado = apagar
    # --------------------------------------------------------

    db.delete(reset_token)

    db.commit()


    # --------------------------------------------------------
    # Voltar para login
    # --------------------------------------------------------

    return templates.TemplateResponse(

        request,

        "auth/login.html",

        {

            "request": request,

            "sucesso":
            "Senha alterada com sucesso! "
            "Agora você pode entrar com sua nova senha."

        }

    )