from fastapi import APIRouter, Request, Form, UploadFile, File
from fastapi.responses import RedirectResponse
from fastapi.templating import Jinja2Templates
import os
import shutil

router = APIRouter()
templates = Jinja2Templates(directory="app/templates")

# Configura a pasta onde as fotos dos produtos vão ficar salvas
UPLOAD_DIR = "static/uploads"
os.makedirs(UPLOAD_DIR, exist_ok=True)

# REQUISITO PARTE 4: Produtos reais demonstrativos relacionados por ID com as categorias
DB_PRODUTOS = [
    {"id": 1, "nome": "Camiseta Polo SENAI", "preco": 49.90, "categoria_id": 1, "imagem": "/static/uploads/polo.png"},
    {"id": 2, "nome": "Apostila de Logística Básica", "preco": 19.90, "categoria_id": 2, "imagem": "/static/uploads/apostila.png"},
    {"id": 3, "nome": "Garrafa Térmica AAPM Inox", "preco": 35.00, "categoria_id": 3, "imagem": "/static/uploads/garrafa.png"}
]

# REQUISITO: Listagem de produtos
@router.get("/produtos")
async def listar_produtos(request: Request, nome: str = "Eduardo", perfil: str = "ADMIN"):
    from app.routes.category_routes import DB_CATEGORIAS
    
    # CORREÇÃO: Ajustado para apontar para a subpasta correta do seu projeto
    return templates.TemplateResponse(
        "produtos/index.html", 
        {
            "request": request, 
            "nome": nome, 
            "perfil": perfil, 
            "produtos": DB_PRODUTOS,
            "categorias": DB_CATEGORIAS # Passa as categorias para o formulário saber onde associar
        }
    )

# REQUISITO: Cadastro de produtos + Upload de imagem
@router.post("/produtos/cadastrar")
async def cadastrar_produto(
    nome_prod: str = Form(...),
    preco_prod: float = Form(...),
    categoria_id: int = Form(...),
    admin_nome: str = Form(...),
    admin_perfil: str = Form(...),
    imagem_file: UploadFile = File(...) # Captura o arquivo de imagem enviado pelo HTML
):
    # MELHORIA: Substitui espaços por underline para evitar links quebrados no HTML
    nome_seguro_arquivo = imagem_file.filename.replace(" ", "_")
    caminho_arquivo = f"{UPLOAD_DIR}/{nome_seguro_arquivo}"
    
    # Salva o arquivo fisicamente na pasta static/uploads
    with open(caminho_arquivo, "wb") as buffer:
        shutil.copyfileobj(imagem_file.file, buffer)
        
    novo_id = max([p["id"] for p in DB_PRODUTOS]) + 1 if DB_PRODUTOS else 1
    
    DB_PRODUTOS.append({
        "id": novo_id,
        "nome": nome_prod,
        "preco": preco_prod,
        "categoria_id": categoria_id,
        "imagem": f"/static/uploads/{nome_seguro_arquivo}" # Caminho limpo da URL da imagem
    })
    
    return RedirectResponse(url=f"/produtos?nome={admin_nome}&perfil={admin_perfil}", status_code=303)

# REQUISITO: Atualização de produtos
@router.post("/produtos/atualizar/{prod_id}")
async def atualizar_produto(
    prod_id: int,
    nome_prod: str = Form(...),
    preco_prod: float = Form(...),
    categoria_id: int = Form(...),
    admin_nome: str = Form(...),
    admin_perfil: str = Form(...)
):
    for prod in DB_PRODUTOS:
        if prod["id"] == prod_id:
            prod["nome"] = nome_prod
            prod["preco"] = preco_prod
            prod["categoria_id"] = categoria_id
            break
    return RedirectResponse(url=f"/produtos?nome={admin_nome}&perfil={admin_perfil}", status_code=303)

# REQUISITO: Exclusão de produtos
@router.get("/produtos/excluir/{prod_id}")
async def excluir_produto(prod_id: int, nome: str = "Eduardo", perfil: str = "ADMIN"):
    global DB_PRODUTOS
    DB_PRODUTOS = [p for p in DB_PRODUTOS if p["id"] != prod_id]
    return RedirectResponse(url=f"/produtos?nome={nome}&perfil={perfil}", status_code=303)