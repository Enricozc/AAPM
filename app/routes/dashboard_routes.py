from fastapi import APIRouter, Request, Depends
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session
from sqlalchemy import func
from datetime import date, datetime, timedelta

from app.config.security import get_current_user
from app.config.database import get_db
from app.models.user_model import Usuario
from app.models.produto_model import Produto
from app.models.categoria_model import Categoria
from app.models.venda_model import Venda

router = APIRouter()
templates = Jinja2Templates(directory="app/templates")


@router.get("/dashboard")
async def dashboard(
    request: Request,
    user=Depends(get_current_user),
    db: Session = Depends(get_db)
):
    hoje = datetime.utcnow().date()  # mesmo fuso das vendas salvas

    total_usuarios   = db.query(func.count(Usuario.id)).filter(Usuario.ativo == True).scalar() or 0
    total_produtos   = db.query(func.count(Produto.id)).filter(Produto.ativo == True).scalar() or 0
    total_estoque    = db.query(func.sum(Produto.estoque_atual)).scalar() or 0
    total_categorias = db.query(func.count(Categoria.id)).filter(Categoria.ativo == True).scalar() or 0

    vendas = db.query(Venda).all()
    vendas_hoje      = [v for v in vendas if v.data_venda.date() == hoje]
    vendas_mes       = [v for v in vendas if v.data_venda.month == hoje.month and v.data_venda.year == hoje.year]
    vendas_pendentes = [v for v in vendas if v.status == "pendente"]

    receita_hoje = sum(v.valor_total for v in vendas_hoje)
    receita_mes  = sum(v.valor_total for v in vendas_mes)

    ultimas_vendas = sorted(vendas, key=lambda v: v.data_venda, reverse=True)[:5]

    dias_semana    = [(hoje - timedelta(days=i)) for i in range(6, -1, -1)]
    grafico_labels  = [d.strftime("%d/%m") for d in dias_semana]
    grafico_receita = []
    grafico_qtd     = []
    for dia in dias_semana:
        vendas_dia = [v for v in vendas if v.data_venda.date() == dia]
        grafico_receita.append(round(sum(v.valor_total for v in vendas_dia), 2))
        grafico_qtd.append(len(vendas_dia))

    return templates.TemplateResponse(
        request=request,
        name="dashboard.html",
        context={
            "request":         request,
            "usuario":         {"nome": user.get("nome"), "role": user.get("role")},
            "stats":           {"usuarios": total_usuarios, "produtos": total_produtos, "estoque": total_estoque, "categorias": total_categorias},
            "vendas_hoje":     len(vendas_hoje),
            "receita_hoje":    receita_hoje,
            "receita_mes":     receita_mes,
            "total_mes":       len(vendas_mes),
            "pendentes":       len(vendas_pendentes),
            "ultimas_vendas":  ultimas_vendas,
            "grafico_labels":  grafico_labels,
            "grafico_receita": grafico_receita,
            "grafico_qtd":     grafico_qtd,
        }
    )