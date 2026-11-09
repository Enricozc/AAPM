from fastapi import APIRouter, Request, Depends, Form
from fastapi.responses import RedirectResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session
from pathlib import Path
from datetime import datetime, timezone
from decimal import Decimal, InvalidOperation, ROUND_HALF_UP
import math
from typing import List

from app.config.database import get_db
from app.config.security import get_current_user
from app.models.venda_model import Venda
from app.models.venda_item_model import VendaItem
from app.models.produto_model import Produto
from app.models.produto_variacao_model import ProdutoVariacao

router = APIRouter(prefix="/vendas", tags=["Vendas"], redirect_slashes=False)

BASE_DIR = Path(__file__).resolve().parent.parent
templates = Jinja2Templates(directory=str(BASE_DIR / "templates"))

FORMAS_PAGAMENTO = {"pix", "cartao", "dinheiro"}

@router.get("")
@router.get("/")
def listar_vendas(
    request: Request,
    db: Session = Depends(get_db),
    usuario=Depends(get_current_user),
):
    vendas = db.query(Venda).order_by(Venda.data_venda.desc()).all()

    produtos_db = db.query(Produto).filter(Produto.ativo == True).all()
    produtos = []
    for p in produtos_db:
        variacoes_ativas = [v for v in p.variacoes if v.ativo]
        if not variacoes_ativas:
            continue
        produtos.append({
            "id": p.id,
            "nome": p.nome,
            "imagem_url": p.imagem_url,
            "variacoes": [
                {"id": v.id, "descricao": v.descricao, "preco": v.preco_efetivo, "estoque_atual": v.estoque_atual}
                for v in variacoes_ativas
            ]
        })

    hoje        = datetime.now(timezone.utc).date()
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


@router.post("")
@router.post("/")
def criar_venda(
    request: Request,
    responsavel:     str         = Form(...),
    variacao_ids:    List[int]   = Form(...),
    quantidades:     List[int]   = Form(...),
    precos:          List[float] = Form(...),
    forma_pagamento: str         = Form(...),
    valor_pagamento_1: float | None = Form(None),
    forma_pagamento_2: str | None = Form(None),
    valor_pagamento_2: float | None = Form(None),
    desconto: float = Form(0),
    tipo_desconto: str = Form("valor"),
    observacao:      str         = Form(""),
    status:          str         = Form("concluida"),
    db: Session = Depends(get_db),
    usuario=Depends(get_current_user),
):
    itens_validos = []

    if len(variacao_ids) != len(quantidades) or len(variacao_ids) != len(precos):
        return RedirectResponse(url="/vendas?erro=itens", status_code=303)

    for variacao_id, quantidade, preco in zip(variacao_ids, quantidades, precos):
        variacao = db.query(ProdutoVariacao).filter(ProdutoVariacao.id == variacao_id).first()
        if (
            not variacao
            or not variacao.ativo
            or quantidade <= 0
            or variacao.estoque_atual < quantidade
            or not math.isfinite(preco)
            or preco < 0
        ):
            return RedirectResponse(url="/vendas?erro=estoque", status_code=303)
        itens_validos.append((variacao, quantidade, preco))

    if not itens_validos:
        return RedirectResponse(url="/vendas?erro=estoque", status_code=303)

    def centavos(valor: float) -> int:
        return int(
            (Decimal(str(valor)) * 100).quantize(
                Decimal("1"), rounding=ROUND_HALF_UP
            )
        )

    try:
        subtotal_centavos = sum(
            centavos(Decimal(quantidade) * Decimal(str(preco)))
            for _, quantidade, preco in itens_validos
        )
    except (InvalidOperation, ValueError, OverflowError):
        return RedirectResponse(url="/vendas?erro=itens", status_code=303)

    if not math.isfinite(desconto) or desconto < 0:
        return RedirectResponse(url="/vendas?erro=desconto", status_code=303)

    try:
        if tipo_desconto == "percentual":
            if desconto > 100:
                return RedirectResponse(url="/vendas?erro=desconto", status_code=303)
            desconto_centavos = int(
                (Decimal(subtotal_centavos) * Decimal(str(desconto)) / 100)
                .quantize(Decimal("1"), rounding=ROUND_HALF_UP)
            )
        elif tipo_desconto == "valor":
            desconto_centavos = centavos(desconto)
        else:
            return RedirectResponse(url="/vendas?erro=desconto", status_code=303)
    except (InvalidOperation, ValueError, OverflowError):
        return RedirectResponse(url="/vendas?erro=desconto", status_code=303)

    if desconto_centavos > subtotal_centavos:
        return RedirectResponse(url="/vendas?erro=desconto", status_code=303)

    total_centavos = subtotal_centavos - desconto_centavos
    forma_pagamento = forma_pagamento.strip().lower()
    forma_pagamento_2 = (forma_pagamento_2 or "").strip().lower() or None

    if forma_pagamento not in FORMAS_PAGAMENTO:
        return RedirectResponse(url="/vendas?erro=pagamento", status_code=303)
    if forma_pagamento_2 and (
        forma_pagamento_2 not in FORMAS_PAGAMENTO
        or forma_pagamento_2 == forma_pagamento
        or valor_pagamento_2 is None
    ):
        return RedirectResponse(url="/vendas?erro=pagamento", status_code=303)
    if not forma_pagamento_2 and valor_pagamento_2 not in (None, 0):
        return RedirectResponse(url="/vendas?erro=pagamento", status_code=303)

    try:
        primeiro_centavos = (
            total_centavos
            if valor_pagamento_1 is None
            else centavos(valor_pagamento_1)
        )
        segundo_centavos = (
            0 if valor_pagamento_2 is None else centavos(valor_pagamento_2)
        )
    except (InvalidOperation, ValueError, OverflowError):
        return RedirectResponse(url="/vendas?erro=pagamento", status_code=303)

    if (
        (valor_pagamento_1 is not None and (not math.isfinite(valor_pagamento_1) or valor_pagamento_1 < 0))
        or (valor_pagamento_2 is not None and (not math.isfinite(valor_pagamento_2) or valor_pagamento_2 < 0))
        or (
            forma_pagamento_2
            and (primeiro_centavos <= 0 or segundo_centavos <= 0)
        )
        or primeiro_centavos + segundo_centavos != total_centavos
    ):
        return RedirectResponse(url="/vendas?erro=pagamento", status_code=303)

    venda = Venda(
        responsavel=responsavel,
        valor_subtotal=subtotal_centavos / 100,
        desconto=desconto_centavos / 100,
        valor_total=total_centavos / 100,
        forma_pagamento=forma_pagamento,
        valor_pagamento_1=primeiro_centavos / 100,
        forma_pagamento_2=forma_pagamento_2,
        valor_pagamento_2=segundo_centavos / 100 if forma_pagamento_2 else None,
        observacao=observacao,
        status=status,
    )
    db.add(venda)
    db.flush()

    for variacao, quantidade, preco in itens_validos:
        db.add(VendaItem(
            venda_id=venda.id,
            produto_variacao_id=variacao.id,
            quantidade=quantidade,
            preco_unitario=preco,
            valor_total=centavos(
                Decimal(quantidade) * Decimal(str(preco))
            ) / 100,
        ))
        variacao.estoque_atual -= quantidade

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