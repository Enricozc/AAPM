from datetime import datetime
from pathlib import Path
from fastapi import APIRouter, Depends, Request
from fastapi.responses import RedirectResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy import func
from sqlalchemy.orm import Session
from app.config.security import get_current_user
from app.config.database import get_db
from app.models.user_model import Usuario
from app.models.produto_model import Produto
from app.models.categoria_model import Categoria
from app.services.log_service import ultimos_logs

router = APIRouter()
BASE_DIR = Path(__file__).resolve().parent.parent
templates = Jinja2Templates(directory=str(BASE_DIR / "templates"))

class UsuarioObj:
    def __init__(self, p):
        self.id=p.get("id"); self.nome=p.get("nome"); self.email=p.get("sub"); self.role=p.get("role")

@router.get("/dashboard")
async def dashboard(request: Request, payload=Depends(get_current_user), db: Session=Depends(get_db)):
    if not payload: return RedirectResponse(url="/auth/login")
    return templates.TemplateResponse(request=request, name="dashboard.html", context={
        "request": request,
        "usuario": UsuarioObj(payload),
        "total_associados": db.query(Usuario).filter(Usuario.ativo==True).count(),
        "total_produtos":   db.query(Produto).filter(Produto.ativo==True).count(),
        "total_categorias": db.query(Categoria).filter(Categoria.ativo==True).count(),
        "estoque_total":    db.query(func.sum(Produto.estoque_atual)).scalar() or 0,
        "logs":             ultimos_logs(db, 6),
        "now":              datetime.utcnow(),
    })