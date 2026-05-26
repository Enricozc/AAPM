from fastapi import APIRouter, Request, Form
from fastapi.responses import RedirectResponse
from fastapi.templating import Jinja2Templates

router = APIRouter()
templates = Jinja2Templates(directory="app/templates")

# REQUISITO PARTE 4: Banco populado com dados reais da AAPM
DB_CATEGORIAS = [
    {"id": 1, "nome": "Uniformes", "descricao": "Camisetas, calças e agasalhos padrão SENAI"},
    {"id": 2, "nome": "Papelaria", "descricao": "Cadernos, blocos, canetas e réguas"},
    {"id": 3, "nome": "Acessórios", "descricao": "Squeezes, chaveiros e mochilas da AAPM"}
]

# REQUISITO: Rota para listar categorias
@router.get("/categorias")
async def listar_categorias(request: Request, nome: str = "Eduardo", perfil: str = "ADMIN"):
    return templates.TemplateResponse(
        "categorias.html", 
        {
            "request": request, 
            "nome": nome, 
            "perfil": perfil,
            "categorias": DB_CATEGORIAS
        }
    )

# REQUISITO: Rota para cadastrar categorias
@router.post("/categorias/cadastrar")
async def cadastrar_categoria(
    nome_cat: str = Form(...), 
    descricao_cat: str = Form(...),
    admin_nome: str = Form(...),
    admin_perfil: str = Form(...)
):
    novo_id = max([c["id"] for c in DB_CATEGORIAS]) + 1 if DB_CATEGORIAS else 1
    DB_CATEGORIAS.append({"id": novo_id, "nome": nome_cat, "descricao": descricao_cat})
    
    return RedirectResponse(url=f"/categorias?nome={admin_nome}&perfil={admin_perfil}", status_code=303)

# REQUISITO: Rota para editar categorias
@router.post("/categorias/editar/{cat_id}")
async def editar_categoria(
    cat_id: int,
    nome_cat: str = Form(...),
    descricao_cat: str = Form(...),
    admin_nome: str = Form(...),
    admin_perfil: str = Form(...)
):
    for cat in DB_CATEGORIAS:
        if cat["id"] == cat_id:
            cat["nome"] = nome_cat
            cat["descricao"] = descricao_cat
            break
    return RedirectResponse(url=f"/categorias?nome={admin_nome}&perfil={admin_perfil}", status_code=303)

# REQUISITO: Rota para excluir categorias
@router.get("/categorias/excluir/{cat_id}")
async def excluir_categoria(cat_id: int, nome: str = "Eduardo", perfil: str = "ADMIN"):
    global DB_CATEGORIAS
    DB_CATEGORIAS = [c for c in DB_CATEGORIAS if c["id"] != cat_id]
    return RedirectResponse(url=f"/categorias?nome={nome}&perfil={perfil}", status_code=303)