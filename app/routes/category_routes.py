from fastapi import APIRouter, Request, Form, FastAPI
from fastapi.responses import RedirectResponse
from fastapi.templating import Jinja2Templates
from fastapi.staticfiles import StaticFiles
import os

router = APIRouter()
templates = Jinja2Templates(directory="app/templates")

# ==========================================
# ROTAS DE AUTENTICAÇÃO E DASHBOARD
# ==========================================

# 1. TELA DE LOGIN (Acessível via /login ou apenas /)
@router.get("/login")
@router.get("/")
async def login_page(request: Request, erro: str = None):
    return templates.TemplateResponse("login.html", {"request": request, "erro": erro})

# 2. PROCESSAMENTO DO LOGIN
@router.post("/login")
async def fazer_login(email: str = Form(...), senha: str = Form(...)):
    # Validação do Administrador
    if email == "admin@email.com" and senha == "123456":
        return RedirectResponse(url="/dashboard?nome=Eduardo&perfil=ADMIN", status_code=303)
    
    # Validação de um Funcionário comum
    elif email == "user@email.com" and senha == "123456":
        return RedirectResponse(url="/dashboard?nome=Carlos+Souza&perfil=FUNCIONARIO", status_code=303)
    
    # Se errar os dados, volta para o login com a mensagem de erro
    return RedirectResponse(url="/login?erro=E-mail+ou+senha+incorretos.", status_code=303)

# 🌟 3. ROTA DO DASHBOARD (Faltava essa rota para receber os dados do login!)
@router.get("/dashboard")
async def exibir_dashboard(request: Request, nome: str = "Eduardo", perfil: str = "ADMIN"):
    return templates.TemplateResponse(
        "dashboard.html", 
        {
            "request": request, 
            "nome": nome, 
            "perfil": perfil
        }
    )

# 4. SAÍDA DO SISTEMA (LOGOUT)
@router.get("/logout")
async def logout():
    return RedirectResponse(url="/login", status_code=303)


# ==========================================
# CONFIGURAÇÃO DO APLICATIVO FASTAPI (main.py)
# ==========================================

app = FastAPI()

# Garante que as pastas do sistema existam para não dar erro de diretório
os.makedirs("app/static", exist_ok=True)

app.mount(
    "/static",
    StaticFiles(directory="app/static"),
    name="static"
)

# Importação das outras rotas do seu projeto
from app.routes import category_routes, product_routes

# Inclui a rota de autenticação/dashboard que criamos acima
app.include_router(router)

# Inclui as rotas de categorias e produtos
app.include_router(category_routes.router)
app.include_router(product_routes.router)