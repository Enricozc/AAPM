from fastapi import APIRouter, Depends, Request, Form
from fastapi.responses import RedirectResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session

from app.config.database import get_db
from app.models.categoria_model import Categoria
from app.config.security import require_admin

router = APIRouter(prefix="/categorias", tags=["Categorias"])

templates = Jinja2Templates(directory="app/templates")


# ── LISTAR ─────────────────────────────
@router.get("/")
def listar(request: Request, db: Session = Depends(get_db), admin=Depends(require_admin)):
    categorias = db.query(Categoria).order_by(Categoria.id).all()

    return templates.TemplateResponse(
        "categorias/index.html",
        {"request": request, "categorias": categorias, "usuario": admin}
    )


# ── FORM NOVA ──────────────────────────
@router.get("/nova")
def form_nova(request: Request, admin=Depends(require_admin)):
    return templates.TemplateResponse(
        "categorias/form.html",
        {"request": request, "usuario": admin, "editando": None}
    )


# ── CRIAR ──────────────────────────────
@router.post("/nova")
def criar(nome: str = Form(...), db: Session = Depends(get_db), admin=Depends(require_admin)):
    nova = Categoria(nome=nome, ativo=True)
    db.add(nova)
    db.commit()

    return RedirectResponse("/categorias/", status_code=302)


# ── EDITAR (FORM) ──────────────────────
@router.get("/{id}/editar")
def form_editar(id: int, request: Request, db: Session = Depends(get_db), admin=Depends(require_admin)):
    cat = db.query(Categoria).filter_by(id=id).first()

    return templates.TemplateResponse(
        "categorias/form.html",
        {"request": request, "usuario": admin, "editando": cat}
    )


# ── EDITAR (POST) ──────────────────────
@router.post("/{id}/editar")
def editar(id: int, nome: str = Form(...), db: Session = Depends(get_db), admin=Depends(require_admin)):
    cat = db.query(Categoria).filter_by(id=id).first()

    if cat:
        cat.nome = nome
        db.commit()

    return RedirectResponse("/categorias/", status_code=302)


# ── TOGGLE ATIVO ───────────────────────
@router.post("/{id}/toggle-ativo")
def toggle(id: int, db: Session = Depends(get_db), admin=Depends(require_admin)):
    cat = db.query(Categoria).filter_by(id=id).first()

    if cat:
        cat.ativo = not cat.ativo
        db.commit()

    return RedirectResponse("/categorias/", status_code=302)