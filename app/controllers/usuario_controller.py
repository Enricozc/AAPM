from fastapi import APIRouter, Depends, Request, Form
from fastapi.responses import RedirectResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session

from app.config.database import get_db
from app.models.user_model import Usuario
from app.config.security import hash_password, require_admin

router = APIRouter(prefix="/usuarios", tags=["Usuários"])

templates = Jinja2Templates(directory="app/templates")


@router.get("/")
def listar_usuarios(request: Request, db: Session = Depends(get_db), admin=Depends(require_admin)):
    usuarios = db.query(Usuario).order_by(Usuario.id).all()
    return templates.TemplateResponse(request, "usuarios/index.html", {"request": request, "usuarios": usuarios, "usuario": admin})


@router.get("/novo")
def form_criar(request: Request, admin=Depends(require_admin)):
    return templates.TemplateResponse(request, "usuarios/form.html", {"request": request, "usuario": admin, "editando": None})


@router.post("/novo")
def criar_usuario(request: Request, nome: str = Form(...), email: str = Form(...), senha: str = Form(...), role: str = Form("operador"), ativo: bool = Form(True), db: Session = Depends(get_db), admin=Depends(require_admin)):
    if db.query(Usuario).filter_by(email=email).first():
        return templates.TemplateResponse(request, "usuarios/form.html", {"request": request, "usuario": admin, "editando": None, "erro": "E-mail já cadastrado."})
    db.add(Usuario(nome=nome, email=email, hashed_password=hash_password(senha), role=role.upper(), ativo=ativo))
    db.commit()
    return RedirectResponse(url="/usuarios/?sucesso=criado", status_code=302)


@router.get("/{usuario_id}/editar")
def form_editar(usuario_id: int, request: Request, db: Session = Depends(get_db), admin=Depends(require_admin)):
    editando = db.query(Usuario).filter_by(id=usuario_id).first()
    if not editando:
        return RedirectResponse(url="/usuarios/", status_code=302)
    return templates.TemplateResponse(request, "usuarios/form.html", {"request": request, "usuario": admin, "editando": editando})


@router.post("/{usuario_id}/editar")
def editar_usuario(usuario_id: int, request: Request, nome: str = Form(...), email: str = Form(...), senha: str = Form(""), role: str = Form("operador"), ativo: bool = Form(False), db: Session = Depends(get_db), admin=Depends(require_admin)):
    editando = db.query(Usuario).filter_by(id=usuario_id).first()
    if not editando:
        return RedirectResponse(url="/usuarios/", status_code=302)
    if db.query(Usuario).filter(Usuario.email == email, Usuario.id != usuario_id).first():
        return templates.TemplateResponse(request, "usuarios/form.html", {"request": request, "usuario": admin, "editando": editando, "erro": "E-mail já em uso."})
    editando.nome = nome
    editando.email = email
    editando.role = role.upper()
    editando.ativo = ativo
    if senha.strip():
        editando.hashed_password = hash_password(senha)
    db.commit()
    return RedirectResponse(url="/usuarios/?sucesso=editado", status_code=302)


@router.post("/{usuario_id}/deletar")
def deletar_usuario(usuario_id: int, request: Request, db: Session = Depends(get_db), admin=Depends(require_admin)):
    u = db.query(Usuario).filter_by(id=usuario_id).first()
    if u:
        db.delete(u)
        db.commit()
    return RedirectResponse(url="/usuarios/?sucesso=deletado", status_code=302)