from fastapi import APIRouter, Request, Depends
from fastapi.templating import Jinja2Templates
from fastapi.responses import RedirectResponse
from pathlib import Path
from sqlalchemy.orm import Session

from app.config.security import get_current_user
from app.config.database import get_db
from app.models.user_model import Usuario
from app.models.produto_model import Produto
from app.models.categoria_model import Categoria

router = APIRouter()
BASE_DIR = Path(__file__).resolve().parent.parent
templates = Jinja2Templates(directory=str(BASE_DIR / "templates"))


class UsuarioObj:
    """Converte o payload JWT (dict) em objeto com atributos para o template."""
    def __init__(self, payload: dict):
        self.id    = payload.get("id")
        self.nome  = payload.get("nome")
        self.email = payload.get("sub")
        self.role  = payload.get("role")


@router.get("/dashboard")
async def dashboard(
    request: Request,
    payload=Depends(get_current_user),
    db: Session = Depends(get_db)
):
    # Redireciona se não autenticado
    if not payload:
        return RedirectResponse(url="/auth/login")

    usuario = UsuarioObj(payload)

    # Dados reais do banco
    total_associados  = db.query(Usuario).filter(Usuario.ativo == True).count()
    total_produtos    = db.query(Produto).filter(Produto.ativo == True).count()
    total_categorias  = db.query(Categoria).filter(Categoria.ativo == True).count()
    estoque_total     = db.query(Produto).with_entities(
                            __import__('sqlalchemy').func.sum(Produto.estoque_atual)
                        ).scalar() or 0

    return templates.TemplateResponse(
        request=request,
        name="dashboard.html",
        context={
            "request":          request,
            "usuario":          usuario,
            "total_associados": total_associados,
            "total_produtos":   total_produtos,
            "total_categorias": total_categorias,
            "estoque_total":    estoque_total,
        }
    )