from fastapi import (
    APIRouter,
    Request,
    Depends,
    Form,
    status
)

from fastapi.responses import (
    RedirectResponse
)

from fastapi.templating import (
    Jinja2Templates
)

from sqlalchemy.orm import Session

from app.config.database import get_db
from app.models.user_model import Usuario
from app.models.user_model import User
from app.config.security import hash_password

router = APIRouter(
    prefix="/usuarios",
    tags=["Usuarios"]
)

templates = Jinja2Templates(
    directory="app/templates"
)


# LISTAR
@router.get("/")
def listar_usuarios(
    request: Request,
    db: Session = Depends(get_db),
    admin=Depends(get_admin)
):

    usuarios = db.query(
        Usuario
    ).order_by(
        Usuario.nome
    ).all()

    return templates.TemplateResponse(
        "usuarios/index.html",
        {
            "request": request,
            "usuarios": usuarios
        }
    )


# ABRIR FORM NOVO
@router.get("/novo")
def novo_usuario(
    request: Request,
    admin=Depends(get_admin)
):

    return templates.TemplateResponse(
        "usuarios/novo.html",
        {
            "request": request
        }
    )


# SALVAR USUÁRIO
@router.post("/novo")
def salvar_usuario(
    nome: str = Form(...),
    email: str = Form(...),
    senha: str = Form(...),
    role: str = Form(...),

    db: Session = Depends(get_db),
    admin=Depends(get_admin)
):

    usuario = Usuario(
        nome=nome,
        email=email,
        senha=hash_password(senha),
        role=role,
        ativo=True
    )

    db.add(usuario)
    db.commit()

    return RedirectResponse(
        "/usuarios?criado=ok",
        status_code=status.HTTP_303_SEE_OTHER
    )


# FORM EDITAR
@router.get("/{id}/editar")
def editar_form(
    id: int,
    request: Request,

    db: Session = Depends(get_db),
    admin=Depends(get_admin)
):

    usuario = db.query(
        Usuario
    ).filter(
        Usuario.id == id
    ).first()

    return templates.TemplateResponse(
        "usuarios/editar.html",
        {
            "request": request,
            "usuario": usuario
        }
    )


# SALVAR EDIÇÃO
@router.post("/{id}/editar")
def editar_usuario(
    id: int,

    nome: str = Form(...),
    email: str = Form(...),
    role: str = Form(...),

    db: Session = Depends(get_db),
    admin=Depends(get_admin)
):

    usuario = db.query(
        Usuario
    ).filter(
        Usuario.id == id
    ).first()

    usuario.nome = nome
    usuario.email = email
    usuario.role = role

    db.commit()

    return RedirectResponse(
        "/usuarios?editado=ok",
        status_code=status.HTTP_303_SEE_OTHER
    )


# EXCLUIR
@router.post("/{id}/excluir")
def excluir_usuario(
    id: int,

    db: Session = Depends(get_db),
    admin=Depends(get_admin)
):

    usuario = db.query(
        Usuario
    ).filter(
        Usuario.id == id
    ).first()

    db.delete(usuario)

    db.commit()

    return RedirectResponse(
        "/usuarios",
        status_code=status.HTTP_303_SEE_OTHER
    )