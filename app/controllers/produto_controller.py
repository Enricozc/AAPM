import os
import shutil
import uuid
from fastapi import APIRouter, Depends, Request, Form, UploadFile, File
from fastapi.responses import RedirectResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session
from app.models.produto_variacao_model import ProdutoVariacao
from typing import List
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
    categoria_id: int = Form(0),
    tamanhos: List[str] = Form(...),
    cores: List[str] = Form(...),
    estoques: List[int] = Form(...),
    imagem: UploadFile = File(None),
    db: Session = Depends(get_db),
    admin=Depends(require_admin)
):
    imagem_path = await _salvar_imagem(imagem)
    produto = Produto(
        nome=nome,
        preco=preco,
        categoria_id=categoria_id or None,
        imagem_path=imagem_path,
    )
    db.add(produto)
    db.flush()  # gera produto.id antes do commit

    for tamanho, cor, estoque in zip(tamanhos, cores, estoques):
        db.add(ProdutoVariacao(
            produto_id=produto.id,
            tamanho=tamanho,
            cor=cor,
            estoque_atual=estoque,
        ))

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
    categoria_id: int = Form(0),
    variacao_ids: List[str] = Form(...),
    tamanhos: List[str] = Form(...),
    cores: List[str] = Form(...),
    estoques: List[int] = Form(...),
    imagem: UploadFile = File(None),
    db: Session = Depends(get_db),
    admin=Depends(require_admin)
):
    produto = db.query(Produto).filter(Produto.id == prod_id).first()
    if not produto:
        return RedirectResponse(url="/produtos?erro=nao_encontrado", status_code=302)

    produto.nome = nome
    produto.preco = preco
    produto.categoria_id = categoria_id or None

    nova_imagem = await _salvar_imagem(imagem)
    if nova_imagem:
        _remover_imagem(produto.imagem_path)
        produto.imagem_path = nova_imagem

    ids_enviados = set()
    for variacao_id, tamanho, cor, estoque in zip(variacao_ids, tamanhos, cores, estoques):
        if variacao_id:
            variacao = db.query(ProdutoVariacao).filter(
                ProdutoVariacao.id == int(variacao_id),
                ProdutoVariacao.produto_id == produto.id,
            ).first()
            if variacao:
                variacao.tamanho = tamanho
                variacao.cor = cor
                variacao.estoque_atual = estoque
                variacao.ativo = True
                ids_enviados.add(variacao.id)
        else:
            nova_variacao = ProdutoVariacao(
                produto_id=produto.id, tamanho=tamanho, cor=cor, estoque_atual=estoque,
            )
            db.add(nova_variacao)
            db.flush()
            ids_enviados.add(nova_variacao.id)

    for variacao_existente in produto.variacoes:
        if variacao_existente.id not in ids_enviados:
            variacao_existente.ativo = False

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


@router.get("/{prod_id}/variacoes")
def listar_variacoes(
    prod_id: int,
    db: Session = Depends(get_db),
    usuario=Depends(get_current_user)
):
    variacoes = db.query(ProdutoVariacao).filter(
        ProdutoVariacao.produto_id == prod_id,
        ProdutoVariacao.ativo == True,
    ).all()
    return [
        {"id": v.id, "descricao": v.descricao, "preco": v.preco_efetivo, "estoque_atual": v.estoque_atual}
        for v in variacoes
    ]