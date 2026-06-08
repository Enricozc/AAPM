import os
from pathlib import Path
from fastapi import FastAPI, Request, Depends
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from fastapi.responses import RedirectResponse

# Banco
from app.config.database import engine, Base

# Controllers
from app.controllers.auth_controller import router as auth_router
from app.controllers.admin_controller import router as admin_router
from app.controllers.categoria_controller import router as categoria_router
from app.controllers.produto_controller import router as produto_router
from app.controllers.usuario_controller import router as usuario_router
from app.controllers.armario_controller import router as armario_router

# Routes
from app.routes.dashboard_routes import router as dashboard_router

# Segurança
from app.config.security import get_usuario_opcional

# Models (IMPORTANTE)
import app.models.user_model
import app.models.produto_model
import app.models.categoria_model
import app.models.log_model
import app.models.armario_model
import app.models.venda_model

# Cria as tabelas
Base.metadata.create_all(bind=engine)

app = FastAPI(title="Sistema AAPM SENAI")

BASE_DIR = Path(__file__).resolve().parent

app.mount(
    "/static",
    StaticFiles(directory=str(BASE_DIR / "static")),
    name="static"
)

templates = Jinja2Templates(
    directory=str(BASE_DIR / "templates")
)

# Rotas
app.include_router(auth_router)
app.include_router(admin_router)
app.include_router(categoria_router)
app.include_router(produto_router)
app.include_router(usuario_router)
app.include_router(armario_router)
app.include_router(dashboard_router)


@app.get("/")
def tela_home(
    request: Request,
    usuario=Depends(get_usuario_opcional)
):
    if usuario is None:
        return templates.TemplateResponse(
            request=request,
            name="index.html",
            context={
                "request": request,
                "usuario": None
            }
        )

    return RedirectResponse(url="/dashboard")