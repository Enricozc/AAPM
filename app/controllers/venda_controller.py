from fastapi import APIRouter, Request, Depends, Form
from fastapi.responses import RedirectResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session
from pathlib import Path
from datetime import datetime
from typing import List

from app.config.database import get_db
from app.config.security import get_current_user
from app.models.venda_model import Venda
from app.models.venda_item_model import VendaItem
from app.models.produto_model import Produto

router = APIRouter(prefix="/vendas", tags=["Vendas"])

BASE_DIR = Path(__file__).resolve().parent.parent
templates = Jinja2Templates(directory=str(BASE_DIR / "templates"))


@router.get("/")
def listar_vendas(
    request: Request,
    db: Session = Depends(get_db),
    usuario=Depends(get_current_user),
):
    vendas      = db.query(Venda).order_by(Venda.data_venda.desc()).all()
    produtos_db = db.query(Produto).filter(Produto.ativo == True).all()
    produtos    = [
        {"id": p.id, "nome": p.nome, "preco": p.preco, "estoque_atual": p.estoque_atual}
        for p in produtos_db
    ]

    hoje        = datetime.utcnow().date()
    vendas_hoje = sum(1 for v in vendas if v.data_venda.date() == hoje)
    total_mes   = sum(1 for v in vendas if v.data_venda.month == hoje.month)
    receita_mes = sum(v.valor_total for v in vendas if v.data_venda.month == hoje.month)
    pendentes   = sum(1 for v in vendas if v.status == "pendente")

    return templates.TemplateResponse(
        request=request,
        name="vendas/index.html",
        context={
            "request":     request,
            "usuario":     usuario,
            "vendas":      vendas,
            "produtos":    produtos,
            "vendas_hoje": vendas_hoje,
            "total_mes":   total_mes,
            "receita_mes": receita_mes,
            "pendentes":   pendentes,
        },
    )


@router.post("/")
def criar_venda(
    request: Request,
    responsavel:     str         = Form(...),
    produto_ids:     List[int]   = Form(...),
    quantidades:     List[int]   = Form(...),
    precos:          List[float] = Form(...),
    forma_pagamento: str         = Form(...),
    observacao:      str         = Form(""),
    status:          str         = Form("concluida"),
    db: Session = Depends(get_db),
    usuario=Depends(get_current_user),
):
    itens_validos = []

    for produto_id, quantidade, preco in zip(produto_ids, quantidades, precos):
        produto = db.query(Produto).filter(Produto.id == produto_id).first()
        if not produto:
            continue
        if produto.estoque_atual < quantidade:
            continue
        itens_validos.append((produto, quantidade, preco))

    if not itens_validos:
        return RedirectResponse(url="/vendas?erro=estoque", status_code=303)

    valor_total = sum(q * p for _, q, p in itens_validos)

    venda = Venda(
        responsavel=responsavel,
        valor_total=valor_total,
        forma_pagamento=forma_pagamento,
        observacao=observacao,
        status=status,
    )
    db.add(venda)
    db.flush()

    for produto, quantidade, preco in itens_validos:
        item = VendaItem(
            venda_id=venda.id,
            produto_id=produto.id,
            quantidade=quantidade,
            preco_unitario=preco,
            valor_total=quantidade * preco,
        )
        db.add(item)
        produto.estoque_atual -= quantidade

    db.commit()
    return RedirectResponse(url="/vendas?sucesso=1", status_code=303)


@router.post("/{venda_id}/deletar")
def deletar_venda(
    venda_id: int,
    db: Session = Depends(get_db),
    usuario=Depends(get_current_user),
):
    venda = db.query(Venda).filter(Venda.id == venda_id).first()
    if venda:
        db.delete(venda)
        db.commit()
    return RedirectResponse(url="/vendas", status_code=303)