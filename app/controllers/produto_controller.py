import os
import shutil
import uuid
from fastapi import APIRouter, Depends, Request, Form, UploadFile, File, status
from fastapi.responses import RedirectResponse
from fastapi.templating import Jinja2Templates
from pathlib import Path
from sqlalchemy.orm import Session

from app.config.database import get_db
from app.models.produto_model import Produto
from app.models.categoria_model import Categoria
from app.config.security import get_current_user, require_admin
from app.services.log_service import registrar_log

router = APIRouter(prefix="/produtos", tags=["Produtos"])

BASE_DIR = Path(__file__).resolve().parent.parent
templates = Jinja2Templates(directory=str(BASE_DIR / "templates"))

UPLOAD_DIR = str(BASE_DIR / "static" / "uploads")
os.makedirs(UPLOAD_DIR, exist_ok=True)


def _obj(payload):
    class U:
        id=payload.get("id"); nome=payload.get("nome"); email=payload.get("sub"); role=payload.get("role")
    return U()


async def _salvar_imagem(imagem: UploadFile | None):
    if not imagem or not imagem.filename:
        return None
    extensoes = {".jpg", ".jpeg", ".png", ".webp"}
    _, ext = os.path.splitext(imagem.filename.lower())
    if ext not in extensoes:
        return None
    nome_arquivo = f"{uuid.uuid4()}{ext}"
    caminho = os.path.join(UPLOAD_DIR, nome_arquivo)
    try:
        with open(caminho, "wb") as f:
            shutil.copyfileobj(imagem.file, f)
        return f"uploads/{nome_arquivo}"
    except Exception:
        return None


def _remover_imagem(imagem_path: str | None):
    if not imagem_path:
        return
    caminho = str(BASE_DIR / "static" / imagem_path)
    if os.path.exists(caminho):
        os.remove(caminho)


# ─────────────────────────────────────────
# LISTAGEM
# ─────────────────────────────────────────
@router.get("/")
def listar_produtos(
    request: Request,
    busca: str = "",
    categoria_id: int = 0,
    db: Session = Depends(get_db),
    payload=Depends(get_current_user)
):
    usuario = _obj(payload)
    query = db.query(Produto).filter(Produto.ativo == True)
    if busca:
        query = query.filter(Produto.nome.ilike(f"%{busca}%"))
    if categoria_id:
        query = query.filter(Produto.categoria_id == categoria_id)
    produtos   = query.order_by(Produto.nome).all()
    categorias = db.query(Categoria).filter(Categoria.ativo == True).all()
    return templates.TemplateResponse(request, "produtos/index.html", {
        "request": request, "usuario": usuario,
        "produtos": produtos, "categorias": categorias,
        "busca": busca, "categoria_id": categoria_id
    })


# ─────────────────────────────────────────
# CRIAR
# ─────────────────────────────────────────
@router.get("/novo")
def form_novo(request: Request, db: Session = Depends(get_db), payload=Depends(require_admin)):
    categorias = db.query(Categoria).filter(Categoria.ativo == True).all()
    return templates.TemplateResponse(request, "produtos/form.html", {
        "request": request, "usuario": _obj(payload), "editando": None, "categorias": categorias
    })


@router.post("/novo")
async def criar_produto(
    request: Request,
    nome: str = Form(...),
    preco: float = Form(...),
    estoque_atual: int = Form(...),
    categoria_id: int = Form(0),
    imagem: UploadFile = File(None),
    db: Session = Depends(get_db),
    payload=Depends(require_admin)
):
    ul = _obj(payload)
    imagem_path = await _salvar_imagem(imagem)
    produto = Produto(
        nome=nome, preco=preco, estoque_atual=estoque_atual,
        categoria_id=categoria_id or None, imagem_path=imagem_path
    )
    db.add(produto)
    db.commit()
    registrar_log(db, f"Produto criado: {nome}", f"Por: {ul.nome}", "sucesso", ul.id)
    return RedirectResponse(url="/produtos/?criado=ok", status_code=status.HTTP_303_SEE_OTHER)


# ─────────────────────────────────────────
# EDITAR
# ─────────────────────────────────────────
@router.get("/{produto_id}/editar")
def form_editar(
    produto_id: int,
    request: Request,
    db: Session = Depends(get_db),
    payload=Depends(require_admin)
):
    produto    = db.query(Produto).filter(Produto.id == produto_id).first()
    if not produto:
        return RedirectResponse(url="/produtos/")
    categorias = db.query(Categoria).filter(Categoria.ativo == True).all()
    return templates.TemplateResponse(request, "produtos/form.html", {
        "request": request, "usuario": _obj(payload),
        "editando": produto, "categorias": categorias
    })


@router.post("/{produto_id}/editar")
async def salvar_edicao(
    produto_id: int,
    request: Request,
    nome: str = Form(...),
    preco: float = Form(...),
    estoque_atual: int = Form(...),
    categoria_id: int = Form(0),
    imagem: UploadFile = File(None),
    db: Session = Depends(get_db),
    payload=Depends(require_admin)
):
    ul      = _obj(payload)
    produto = db.query(Produto).filter(Produto.id == produto_id).first()
    if not produto:
        return RedirectResponse(url="/produtos/")

    produto.nome          = nome
    produto.preco         = preco
    produto.estoque_atual = estoque_atual
    produto.categoria_id  = categoria_id or None

    nova_imagem = await _salvar_imagem(imagem)
    if nova_imagem:
        _remover_imagem(produto.imagem_path)
        produto.imagem_path = nova_imagem

    db.commit()
    registrar_log(db, f"Produto editado: {nome}", f"Por: {ul.nome}", "info", ul.id)
    return RedirectResponse(url="/produtos/?editado=ok", status_code=status.HTTP_303_SEE_OTHER)


# ─────────────────────────────────────────
# DESATIVAR
# ─────────────────────────────────────────
@router.post("/{produto_id}/desativar")
def desativar_produto(
    produto_id: int,
    db: Session = Depends(get_db),
    payload=Depends(require_admin)
):
    ul      = _obj(payload)
    produto = db.query(Produto).filter(Produto.id == produto_id).first()
    if produto:
        produto.ativo = False
        db.commit()
        registrar_log(db, f"Produto desativado: {produto.nome}", f"Por: {ul.nome}", "alerta", ul.id)
    return RedirectResponse(url="/produtos/?desativado=ok", status_code=status.HTTP_303_SEE_OTHER)


# ─────────────────────────────────────────
# ATIVAR
# ─────────────────────────────────────────
@router.post("/{produto_id}/ativar")
def ativar_produto(
    produto_id: int,
    db: Session = Depends(get_db),
    payload=Depends(require_admin)
):
    ul      = _obj(payload)
    produto = db.query(Produto).filter(Produto.id == produto_id).first()
    if produto:
        produto.ativo = True
        db.commit()
        registrar_log(db, f"Produto ativado: {produto.nome}", f"Por: {ul.nome}", "sucesso", ul.id)
    return RedirectResponse(url="/produtos/?ativado=ok", status_code=status.HTTP_303_SEE_OTHER)