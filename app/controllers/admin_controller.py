from fastapi import APIRouter, Depends, Request, Form, status
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session

# Caminhos e funções totalmente alinhados
from app.config.database import get_db
from app.models.user_model import Usuario
from app.config.security import hash_password, verify_password, create_access_token

router = APIRouter(prefix="/auth", tags=["Autenticação"])

templates = Jinja2Templates(directory="app/templates")


@router.get("/cadastro")
def tela_cadastro(request: Request):
    return templates.TemplateResponse(
        request,
        "auth/cadastro.html",
        {"request": request}
    )


# 1. CORRIGIDO: Nome da função alterado para 'tela_login' (estava duplicado)
@router.get("/login")
def tela_login(request: Request):
    return templates.TemplateResponse(
        request,
        "auth/login.html",
        {"request": request}
    )


# Rota para criar um usuario no banco de dados
@router.post("/cadastro")
def fazer_cadastro(
    request: Request,
    nome: str = Form(...),
    email: str = Form(...),
    senha: str = Form(...),
    db: Session = Depends(get_db)
):
    
    # Verificar o email do usuario
    user_existente = db.query(Usuario).filter_by(email=email).first()

    if user_existente:
        return templates.TemplateResponse(
            request,
            "auth/cadastro.html",
            {"request": request, "erro": "Este e-mail já está cadastrado."}
        )
    
    # 2. CORRIGIDO: Alterado de 'hash_senha' para 'hash_password'
    novo_usuario = Usuario(nome=nome, email=email, hashed_password=hash_password(senha))
    db.add(novo_usuario)
    db.commit()

    return RedirectResponse(url="/auth/login?cadastro=ok", status_code=302)


@router.post("/login")
def login(
    request: Request,
    email: str = Form(...),
    senha: str = Form(...),
    db: Session = Depends(get_db)
):
    """
    Processa o login e define o cookie JWT.
    """

    # Busca o usuário no banco pelo email
    usuario = db.query(Usuario).filter(
        Usuario.email == email
    ).first()

    # 3. CORRIGIDO: Alterado de 'verificar_senha' para 'verify_password'
    senha_correta = (
        usuario is not None and
        verify_password(senha, usuario.hashed_password)
    )

    if not senha_correta:
        return templates.TemplateResponse(
            request,
            "auth/login.html",
            {
                "request": request,
                "erro": "E-mail ou senha incorretos."
            },
            status_code=401
        )

    if not usuario.ativo:
        return templates.TemplateResponse(
            request,
            "auth/login.html",
            {
                "request": request,
                "erro": "Usuário inativo. Contate o administrador."
            },
            status_code=403
        )

    # Dados que ficarão no payload do JWT
    token_data = {
        "sub": usuario.email,
        "nome": usuario.nome,
        "role": usuario.role,
        "id": usuario.id
    }

    # 4. CORRIGIDO: Alterado de 'criar_token' para 'create_access_token'
    token = create_access_token(token_data)

    # Cria a resposta de redirecionamento
    response = RedirectResponse(url="/", status_code=302)

    # Define o cookie com o token JWT
    response.set_cookie(
        key="access_token",
        value=token,
        httponly=True,    # JavaScript NÃO pode ler este cookie (proteção XSS)
        max_age=3600,     # expira em 1 hora (em segundos)
        samesite="lax",   # proteção básica contra CSRF
    )

    return response


@router.get("/logout")
def logout():
    response = RedirectResponse(url="/", status_code=302)
    response.delete_cookie("access_token")
    return response