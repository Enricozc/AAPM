import os
import shutil
import uuid
from fastapi import APIRouter, Depends, Request, Form, UploadFile, File
from fastapi.responses import RedirectResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session

from app.config.database import get_db
from app.models.produto_model import Produto
from app.models.categoria_model import Categoria
from app.config.security import get_current_user, require_admin

router = APIRouter(prefix="/produtos", tags=["Produtos"])
templates = Jinja2Templates(directory="app/templates")

UPLOAD_DIR = "app/static/uploads"
os.makedirs(UPLOAD_DIR, exist_ok=True)

# ============================================================
# FUNÇÕES AUXILIARES DE IMAGEM
# ============================================================

async def _salvar_imagem(imagem: UploadFile | None):
    if not imagem or not imagem.filename or imagem.filename == "":
        return None

    extensoes_permitidas = {".jpg", ".jpeg", ".png", ".webp"}
    _, ext = os.path.splitext(imagem.filename.lower())

    if ext not in extensoes_permitidas:
        return None

    nome_arquivo = f"{uuid.uuid4()}{ext}"
    caminho_completo = os.path.join(UPLOAD_DIR, nome_arquivo)

    try:
        with open(caminho_completo, "wb") as buffer:
            shutil.copyfileobj(imagem.file, buffer)
        return f"uploads/{nome_arquivo}"
    except Exception:
        return None

def _remover_imagem(imagem_path: str | None) -> None:
    if not imagem_path:
        return
    caminho = os.path.join("app/static", imagem_path)
    if os.path.exists(caminho) and os.path.isfile(caminho):
        os.remove(caminho)

# ============================================================
# ROTAS
# ============================================================

@router.get("/")
def listar_produtos(
    request: Request,
    busca: str = "",
    categoria_id: int = 0,
    db: Session = Depends(get_db),
    usuario=Depends(get_current_user)
):
    query = db.query(Produto).filter(Produto.ativo == True)
    if busca:
        query = query.filter(Produto.nome.ilike(f"%{busca}%"))
    if categoria_id:
        query = query.filter(Produto.categoria_id == categoria_id)

    produtos = query.order_by(Produto.nome).all()
    categorias = db.query(Categoria).filter(Categoria.ativo == True).all()

    return templates.TemplateResponse(request, "produtos/index.html", {
        "request": request,
        "usuario": usuario,
        "produtos": produtos,
        "categorias": categorias,
        "busca": busca,
        "categoria_id": categoria_id,
    })


@router.get("/novo")
def form_novo_produto(
    request: Request,
    db: Session = Depends(get_db),
    admin=Depends(require_admin)
):
    categorias = db.query(Categoria).filter(Categoria.ativo == True).all()
    return templates.TemplateResponse(request, "produtos/form.html", {
        "request": request,
        "usuario": admin,
        "editando": None,
        "categorias": categorias,
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
    admin=Depends(require_admin)
):
    imagem_path = await _salvar_imagem(imagem)
    produto = Produto(
        nome=nome,
        preco=preco,
        estoque_atual=estoque_atual,
        categoria_id=categoria_id or None,
        imagem_path=imagem_path,
    )
    db.add(produto)
    db.commit()
    return RedirectResponse(url="/produtos?criado=ok", status_code=302)


@router.get("/{prod_id}/editar")
def form_editar_produto(
    prod_id: int,
    request: Request,
    db: Session = Depends(get_db),
    admin=Depends(require_admin)
):
    produto = db.query(Produto).filter(Produto.id == prod_id).first()
    categorias = db.query(Categoria).filter(Categoria.ativo == True).all()
    return templates.TemplateResponse(request, "produtos/form.html", {
        "request": request,
        "usuario": admin,
        "editando": produto,
        "categorias": categorias,
    })


@router.post("/{prod_id}/editar")
async def atualizar_produto(
    prod_id: int,
    request: Request,
    nome: str = Form(...),
    preco: float = Form(...),
    estoque_atual: int = Form(...),
    categoria_id: int = Form(0),
    imagem: UploadFile = File(None),
    db: Session = Depends(get_db),
    admin=Depends(require_admin)
):
    produto = db.query(Produto).filter(Produto.id == prod_id).first()
    if produto:
        produto.nome = nome
        produto.preco = preco
        produto.estoque_atual = estoque_atual
        produto.categoria_id = categoria_id or None

        nova_imagem = await _salvar_imagem(imagem)
        if nova_imagem:
            _remover_imagem(produto.imagem_path)
            produto.imagem_path = nova_imagem

        db.commit()
    return RedirectResponse(url="/produtos?atualizado=ok", status_code=302)


@router.post("/{prod_id}/desativar")
def desativar_produto(
    prod_id: int,
    db: Session = Depends(get_db),
    admin=Depends(require_admin)
):
    produto = db.query(Produto).filter(Produto.id == prod_id).first()
    if produto:
        produto.ativo = False
        db.commit()
    return RedirectResponse(url="/produtos?desativado=ok", status_code=302)