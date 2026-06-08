from fastapi import APIRouter, Request, Form, UploadFile, File, Depends
from fastapi.responses import RedirectResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session
import os, shutil, uuid

from app.config.database import get_db
from app.config.security import get_current_user
from app.models.produto_model import Produto
from app.models.categoria_model import Categoria

router = APIRouter()
templates = Jinja2Templates(directory="app/templates")

UPLOAD_DIR = "static/uploads"
os.makedirs(UPLOAD_DIR, exist_ok=True)


@router.get("/produtos")
async def listar_produtos(
    request: Request,
    busca: str = "",
    categoria_id: int = 0,
    user=Depends(get_current_user),
    db: Session = Depends(get_db)
):
    query = db.query(Produto).filter(Produto.ativo == True)
    if busca:
        query = query.filter(Produto.nome.ilike(f"%{busca}%"))
    if categoria_id:
        query = query.filter(Produto.categoria_id == categoria_id)

    produtos   = query.order_by(Produto.nome).all()
    categorias = db.query(Categoria).filter(Categoria.ativo == True).all()

    return templates.TemplateResponse("produtos/index.html", {
        "request":      request,
        "produtos":     produtos,
        "categorias":   categorias,
        "usuario":      user,
        "busca":        busca,
        "categoria_id": categoria_id,
    })


@router.get("/produtos/novo")
async def form_novo_produto(
    request: Request,
    user=Depends(get_current_user),
    db: Session = Depends(get_db)
):
    categorias = db.query(Categoria).filter(Categoria.ativo == True).all()
    return templates.TemplateResponse("produtos/novo.html", {
        "request":    request,
        "categorias": categorias,
        "usuario":    user,
    })


@router.post("/produtos/cadastrar")
async def cadastrar_produto(
    nome:         str        = Form(...),
    preco:        float      = Form(...),
    estoque:      int        = Form(...),
    categoria_id: int        = Form(...),
    imagem:       UploadFile = File(None),
    user=Depends(get_current_user),
    db: Session = Depends(get_db)
):
    imagem_path = None
    if imagem and imagem.filename:
        ext      = imagem.filename.rsplit(".", 1)[-1]
        filename = f"{uuid.uuid4().hex}.{ext}"
        caminho  = f"{UPLOAD_DIR}/{filename}"
        with open(caminho, "wb") as f:
            shutil.copyfileobj(imagem.file, f)
        imagem_path = f"uploads/{filename}"

    db.add(Produto(
        nome=nome,
        preco=preco,
        estoque_atual=estoque,
        categoria_id=categoria_id,
        imagem_path=imagem_path,
    ))
    db.commit()
    return RedirectResponse(url="/produtos?criado=ok", status_code=303)


@router.get("/produtos/{prod_id}/editar")
async def form_editar_produto(
    prod_id: int,
    request: Request,
    user=Depends(get_current_user),
    db: Session = Depends(get_db)
):
    produto    = db.query(Produto).filter(Produto.id == prod_id).first()
    categorias = db.query(Categoria).filter(Categoria.ativo == True).all()
    return templates.TemplateResponse("produtos/editar.html", {
        "request":    request,
        "produto":    produto,
        "categorias": categorias,
        "usuario":    user,
    })


@router.post("/produtos/{prod_id}/atualizar")
async def atualizar_produto(
    prod_id:      int,
    nome:         str        = Form(...),
    preco:        float      = Form(...),
    estoque:      int        = Form(...),
    categoria_id: int        = Form(...),
    imagem:       UploadFile = File(None),
    user=Depends(get_current_user),
    db: Session = Depends(get_db)
):
    produto = db.query(Produto).filter(Produto.id == prod_id).first()
    if produto:
        produto.nome          = nome
        produto.preco         = preco
        produto.estoque_atual = estoque
        produto.categoria_id  = categoria_id

        if imagem and imagem.filename:
            ext      = imagem.filename.rsplit(".", 1)[-1]
            filename = f"{uuid.uuid4().hex}.{ext}"
            caminho  = f"{UPLOAD_DIR}/{filename}"
            with open(caminho, "wb") as f:
                shutil.copyfileobj(imagem.file, f)
            produto.imagem_path = f"uploads/{filename}"

        db.commit()
    return RedirectResponse(url="/produtos", status_code=303)


@router.post("/produtos/{prod_id}/desativar")
async def desativar_produto(
    prod_id: int,
    user=Depends(get_current_user),
    db: Session = Depends(get_db)
):
    produto = db.query(Produto).filter(Produto.id == prod_id).first()
    if produto:
        produto.ativo = False
        db.commit()
    return RedirectResponse(url="/produtos?desativado=ok", status_code=303)


@router.get("/produtos/{prod_id}")
async def detalhe_produto(
    prod_id: int,
    request: Request,
    user=Depends(get_current_user),
    db: Session = Depends(get_db)
):
    produto = db.query(Produto).filter(Produto.id == prod_id).first()
    return templates.TemplateResponse("produtos/detalhe.html", {
        "request": request,
        "produto": produto,
        "usuario": user,
    })