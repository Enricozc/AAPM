from pathlib import Path

from fastapi import FastAPI, Request, Depends
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates

from app.config.database import engine, Base
from app.config.security import get_usuario_opcional

from app.controllers.auth_controller import router as auth_router
from app.controllers.admin_controller import router as admin_router
from app.controllers.categoria_controller import router as categoria_router
from app.controllers.produto_controller import router as produto_router
from app.controllers.usuario_controller import router as usuario_router
from app.controllers.armario_controller import router as armario_router

from app.routes.dashboard_routes import router as dashboard_router

import app.models.log_model
import app.models.armario_model

# =====================================================
# CRIAÇÃO DAS TABELAS
# =====================================================

Base.metadata.create_all(bind=engine)

# =====================================================
# APP
# =====================================================

app = FastAPI(
    title="AAPM SENAI"
)

BASE_DIR = Path(__file__).resolve().parent

# =====================================================
# ARQUIVOS ESTÁTICOS
# =====================================================

app.mount(
    "/static",
    StaticFiles(directory=str(BASE_DIR / "static")),
    name="static"
)

templates = Jinja2Templates(
    directory=str(BASE_DIR / "templates")
)

# =====================================================
# ROTAS
# =====================================================

app.include_router(auth_router)
app.include_router(admin_router)
app.include_router(categoria_router)
app.include_router(produto_router)
app.include_router(usuario_router)
app.include_router(armario_router)
app.include_router(dashboard_router)

# =====================================================
# HOME
# =====================================================

@app.get("/")
def tela_home(
    request: Request,
    usuario=Depends(get_usuario_opcional)
):
    return templates.TemplateResponse(
        request=request,
        name="index.html",
        context={
            "request": request,
            "usuario": usuario
        }
    )