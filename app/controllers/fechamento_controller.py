from fastapi import APIRouter, Request, Depends, Form
from fastapi.responses import RedirectResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session
from pathlib import Path
from datetime import datetime

from app.config.database import get_db
from app.config.security import get_current_user
from app.models.venda_model import Venda
from app.models.fechamento_model import Fechamento

router = APIRouter(prefix="/fechamento", tags=["Fechamento"])

BASE_DIR = Path(__file__).resolve().parent.parent
templates = Jinja2Templates(directory=str(BASE_DIR / "templates"))


@router.get("/")
def tela_fechamento(
    request: Request,
    db: Session = Depends(get_db),
    usuario=Depends(get_current_user),
):
    hoje   = datetime.utcnow().date()
    vendas = db.query(Venda).all()
    vendas_hoje = [v for v in vendas if v.data_venda.date() == hoje]

    total_vendas     = len(vendas_hoje)
    receita_total    = sum(v.valor_total for v in vendas_hoje)
    receita_pix      = sum(v.valor_total for v in vendas_hoje if v.forma_pagamento == "pix")
    receita_cartao   = sum(v.valor_total for v in vendas_hoje if v.forma_pagamento == "cartao")
    receita_dinheiro = sum(v.valor_total for v in vendas_hoje if v.forma_pagamento == "dinheiro")

    fechamentos    = db.query(Fechamento).order_by(Fechamento.data_fechamento.desc()).limit(10).all()
    ja_fechou_hoje = any(f.data_fechamento.date() == hoje for f in fechamentos)

    return templates.TemplateResponse(
        request=request,
        name="fechamento/index.html",
        context={
            "request":          request,
            "usuario":          usuario,
            "hoje":             hoje.strftime("%d/%m/%Y"),
            "total_vendas":     total_vendas,
            "receita_total":    receita_total,
            "receita_pix":      receita_pix,
            "receita_cartao":   receita_cartao,
            "receita_dinheiro": receita_dinheiro,
            "vendas_hoje":      vendas_hoje,
            "fechamentos":      fechamentos,
            "ja_fechou_hoje":   ja_fechou_hoje,
        },
    )


@router.post("/confirmar")
def confirmar_fechamento(
    request: Request,
    observacao: str = Form(""),
    db: Session = Depends(get_db),
    usuario=Depends(get_current_user),
):
    hoje   = datetime.utcnow().date()
    vendas = db.query(Venda).all()
    vendas_hoje = [v for v in vendas if v.data_venda.date() == hoje]

    # ✅ CORRIGIDO: usuario é dict JWT, usa .get() em vez de .nome
    nome_usuario = usuario.get("nome", "desconhecido") if isinstance(usuario, dict) else str(usuario)

    fechamento = Fechamento(
        data_fechamento  = datetime.utcnow(),
        total_vendas     = len(vendas_hoje),
        receita_total    = sum(v.valor_total for v in vendas_hoje),
        receita_pix      = sum(v.valor_total for v in vendas_hoje if v.forma_pagamento == "pix"),
        receita_cartao   = sum(v.valor_total for v in vendas_hoje if v.forma_pagamento == "cartao"),
        receita_dinheiro = sum(v.valor_total for v in vendas_hoje if v.forma_pagamento == "dinheiro"),
        observacao       = observacao,
        usuario          = nome_usuario,
    )
    db.add(fechamento)
    db.commit()
    return RedirectResponse(url="/fechamento?sucesso=1", status_code=303)