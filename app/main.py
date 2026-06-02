import os
from pathlib import Path
from fastapi import FastAPI, Request, Depends
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates

# Importações do projeto
from app.config.database import engine, Base
from app.controllers.auth_controller import router as auth_router
from app.controllers.admin_controller import router as admin_router
from app.controllers.categoria_controller import router as categoria_router
from app.controllers.produto_controller import router as produto_router
from app.controllers.usuario_controller import router as usuario_router
from app.config.security import get_usuario_opcional

# Cria as tabelas automaticamente
Base.metadata.create_all(bind=engine)

app = FastAPI(title="Sistema AAPM SENAI")

# ✅ CAMINHO CORRIGIDO: Referência absoluta ao diretório do main.py
BASE_DIR = Path(__file__).resolve().parent

# Monta os estáticos e templates
app.mount("/static", StaticFiles(directory=str(BASE_DIR / "static")), name="static")
templates = Jinja2Templates(directory=str(BASE_DIR / "templates"))

# Rotas
app.include_router(auth_router)
app.include_router(admin_router)
app.include_router(categoria_router)
app.include_router(produto_router)
app.include_router(usuario_router)

@app.get("/")
def tela_home(request: Request, usuario=Depends(get_usuario_opcional)):
    # ✅ FIX: Uso explícito dos argumentos request, name e context
    if usuario is None:
        return templates.TemplateResponse(
            request=request, 
            name="index.html", 
            context={"request": request, "usuario": None}
        )
    
    return templates.TemplateResponse(
        request=request, 
        name="dashboard.html", 
        context={"request": request, "usuario": usuario}
    )