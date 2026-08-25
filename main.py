from pathlib import Path

from fastapi import FastAPI, Request, Depends
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from fastapi.responses import RedirectResponse
from sqlalchemy.orm import Session

from app.config.database import engine, Base, get_db
from app.config.security import get_usuario_opcional


# =====================================================
# CONTROLLERS
# =====================================================

from app.controllers.auth_controller import router as auth_router
from app.controllers.categoria_controller import router as categoria_router
from app.controllers.produto_controller import router as produto_router
from app.controllers.usuario_controller import router as usuario_router
from app.controllers.armario_controller import router as armario_router
from app.controllers.venda_controller import router as venda_router
from app.controllers.fechamento_controller import router as fechamento_router


# =====================================================
# ROUTES
# =====================================================

from app.routes.dashboard_routes import router as dashboard_router


# =====================================================
# MODELS
# =====================================================

import app.models.user_model
import app.models.produto_model
import app.models.produto_variacao_model
import app.models.categoria_model
import app.models.log_model
import app.models.armario_model
import app.models.venda_model
import app.models.venda_item_model
import app.models.fechamento_model

from app.models.produto_model import Produto


# =====================================================
# CRIA TABELAS
# =====================================================

Base.metadata.create_all(bind=engine)


# =====================================================
# FASTAPI
# =====================================================

app = FastAPI(
    title="Sistema AAPM SENAI"
)


# =====================================================
# DIRETÓRIOS
# =====================================================

BASE_DIR = Path(__file__).resolve().parent


# =====================================================
# STATIC
# =====================================================

app.mount(
    "/static",
    StaticFiles(
        directory=str(BASE_DIR / "app" / "static")
    ),
    name="static"
)


# =====================================================
# TEMPLATES
# =====================================================

templates = Jinja2Templates(
    directory=str(BASE_DIR / "app" / "templates")
)


# =====================================================
# ROUTERS
# =====================================================

app.include_router(auth_router)

app.include_router(categoria_router)

app.include_router(produto_router)

app.include_router(usuario_router)

app.include_router(armario_router)

app.include_router(dashboard_router)

app.include_router(venda_router)

app.include_router(fechamento_router)


# =====================================================
# HOME
# =====================================================

@app.get("/")
def tela_home(
    request: Request,
    usuario=Depends(get_usuario_opcional),
    db: Session = Depends(get_db)
):

    if usuario is None:

        produtos = (
            db.query(Produto)
            .filter(Produto.ativo == True)
            .limit(6)
            .all()
        )

        return templates.TemplateResponse(
            request=request,
            name="index.html",
            context={
                "request": request,
                "usuario": None,
                "produtos": produtos,
            }
        )

    return RedirectResponse(
        url="/dashboard"
    )