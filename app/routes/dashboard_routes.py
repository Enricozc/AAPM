from fastapi import APIRouter, Request, Depends
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session
from sqlalchemy import func

from app.config.security import get_current_user
from app.config.database import get_db
from app.models.user_model import Usuario
from app.models.produto_model import Produto
from app.models.categoria_model import Categoria

router = APIRouter()
templates = Jinja2Templates(directory="app/templates")


@router.get("/dashboard")
async def dashboard(
    request: Request,
    user=Depends(get_current_user),
    db: Session = Depends(get_db)
):
    total_usuarios = db.query(func.count(Usuario.id)).filter(Usuario.ativo == True).scalar() or 0
    total_produtos   = db.query(func.count(Produto.id)).filter(Produto.ativo == True).scalar() or 0
    total_estoque    = db.query(func.sum(Produto.estoque_atual)).scalar() or 0
    total_categorias = db.query(func.count(Categoria.id)).filter(Categoria.ativo == True).scalar() or 0

    return templates.TemplateResponse(
        request=request,
        name="dashboard.html",
        context={
            "usuario": {
                "nome": user.get("nome"),
                "role": user.get("role")
            },
            "stats": {
                "usuarios":   total_usuarios,
                "produtos":   total_produtos,
                "estoque":    total_estoque,
                "categorias": total_categorias,
            }
        }
    )