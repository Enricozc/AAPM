import os
from pathlib import Path

from fastapi import FastAPI, Request, Depends
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates

# Banco de dados
from app.config.database import engine, Base

# Models
from app.models.user_model import Usuario

# Controllers
from app.controllers.auth_controller import router as auth_router
from app.controllers.admin_controller import router as admin_router
from app.controllers.categoria_controller import router as categoria_router
from app.controllers.produto_controller import router as produto_router

# Segurança
from app.config.security import get_usuario_opcional

# Cria as tabelas automaticamente
Base.metadata.create_all(bind=engine)

app = FastAPI(title="Sistema MVC")

# Caminho base da aplicação
BASE_DIR = Path(__file__).resolve().parent

# Arquivos estáticos
app.mount(
    "/static",
    StaticFiles(directory=str(BASE_DIR / "static")),
    name="static"
)

# Templates
templates = Jinja2Templates(
    directory=str(BASE_DIR / "templates")
)

# Rotas
app.include_router(auth_router)
app.include_router(admin_router)
app.include_router(categoria_router)
app.include_router(produto_router)


# ============================================================
# ✅ ROTA INICIAL CORRIGIDA (SEM ERRO 500 / TEMPLATE NOT FOUND)
# ============================================================
@app.get("/")
def tela_homee(
    request: Request,
    usuario=Depends(get_usuario_opcional)
):
    
    # 1. Se o usuário NÃO estiver logado:
    if usuario is None:
        return templates.TemplateResponse(
            request,
            "index.html",  # ✅ Renderiza a landing page pública da AAPM
            {
                "request": request,
                "usuario": None
            }
        )

    # 2. Se o usuário ESTIVER logado (Seja ADMIN ou FUNCIONARIO):
    # 💡 CORRIGIDO: Removida a barreira do 'home.html' que causava erro no usuário comum!
    return templates.TemplateResponse(
        request,
        "dashboard.html",  # ✅ Ambos os níveis de acesso usam o painel real que você possui
        {
            "request": request,
            "usuario": usuario
        }
    )