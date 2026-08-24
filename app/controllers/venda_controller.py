from fastapi import APIRouter, Request, Depends, Form
from fastapi.responses import RedirectResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session
from sqlalchemy import func
from pathlib import Path
from datetime import datetime
from typing import List

from app.config.database import get_db
from app.config.security import get_current_user
from app.models.venda_model import Venda
from app.models.venda_item_model import VendaItem
from app.models.produto_model import Produto
from app.models.produto_variacao_model import ProdutoVariacao


router = APIRouter(
    prefix="/vendas",
    tags=["Vendas"],
    redirect_slashes=False
)


BASE_DIR = Path(__file__).resolve().parent.parent
templates = Jinja2Templates(directory=str(BASE_DIR / "templates"))


# ============================================================
# LISTAR VENDAS
# PAGINAÇÃO + BUSCA + FILTROS + ORDENAÇÃO
# ============================================================

@router.get("")
@router.get("/")
def listar_vendas(
    request: Request,

    # Paginação
    pagina: int = 1,
    por_pagina: int = 10,

    # Filtros
    busca: str = "",
    status_filtro: str = "",
    forma_pagamento: str = "",

    # Ordenação
    ordenar: str = "data_desc",

    db: Session = Depends(get_db),
    usuario=Depends(get_current_user),
):

    # ========================================================
    # VALIDAÇÃO DA PAGINAÇÃO
    # ========================================================

    if pagina < 1:
        pagina = 1

    if por_pagina not in [5, 10, 20, 50]:
        por_pagina = 10

    # ========================================================
    # QUERY DAS VENDAS
    # ========================================================

    query = db.query(Venda)

    # ========================================================
    # BUSCA POR RESPONSÁVEL
    # ========================================================

    if busca:
        query = query.filter(
            Venda.responsavel.ilike(f"%{busca}%")
        )

    # ========================================================
    # FILTRO POR STATUS
    # ========================================================

    if status_filtro:
        query = query.filter(
            Venda.status == status_filtro
        )

    # ========================================================
    # FILTRO POR FORMA DE PAGAMENTO
    # ========================================================

    if forma_pagamento:
        query = query.filter(
            Venda.forma_pagamento == forma_pagamento
        )

    # ========================================================
    # ORDENAÇÃO
    # ========================================================

    if ordenar == "data_asc":

        query = query.order_by(
            Venda.data_venda.asc()
        )

    elif ordenar == "valor_desc":

        query = query.order_by(
            Venda.valor_total.desc()
        )

    elif ordenar == "valor_asc":

        query = query.order_by(
            Venda.valor_total.asc()
        )

    elif ordenar == "responsavel":

        query = query.order_by(
            Venda.responsavel.asc()
        )

    else:

        # Mais recentes primeiro
        query = query.order_by(
            Venda.data_venda.desc()
        )

    # ========================================================
    # TOTAL DE VENDAS
    # ========================================================

    total_vendas = query.count()

    # ========================================================
    # TOTAL DE PÁGINAS
    # ========================================================

    total_paginas = max(
        1,
        (total_vendas + por_pagina - 1) // por_pagina
    )

    # ========================================================
    # CORRIGE PÁGINA INVÁLIDA
    # ========================================================

    if pagina > total_paginas:
        pagina = total_paginas

    # ========================================================
    # OFFSET
    # ========================================================

    offset = (pagina - 1) * por_pagina

    # ========================================================
    # BUSCA APENAS AS VENDAS DA PÁGINA
    # ========================================================

    vendas = (
        query
        .offset(offset)
        .limit(por_pagina)
        .all()
    )

    # ========================================================
    # PRODUTOS ATIVOS
    # ========================================================

    produtos_db = (
        db.query(Produto)
        .filter(Produto.ativo == True)
        .all()
    )

    produtos = []

    # ========================================================
    # PRODUTOS + VARIAÇÕES
    # ========================================================

    for p in produtos_db:

        variacoes = [
            {
                "id": v.id,
                "descricao": v.descricao,
                "preco": v.preco_efetivo,
                "estoque_atual": v.estoque_atual,
            }

            for v in p.variacoes

            if v.ativo
        ]

        # Só mostra produtos que possuem
        # pelo menos uma variação ativa

        if variacoes:

            produtos.append(
                {
                    "id": p.id,
                    "nome": p.nome,
                    "variacoes": variacoes
                }
            )

    # ========================================================
    # DATA ATUAL
    # ========================================================

    hoje = datetime.utcnow().date()

    # ========================================================
    # VENDAS DE HOJE
    # ========================================================

    vendas_hoje = (
        db.query(func.count(Venda.id))
        .filter(
            func.date(Venda.data_venda) == hoje
        )
        .scalar()
        or 0
    )

    # ========================================================
    # TOTAL DE VENDAS DO MÊS
    # ========================================================

    total_mes = (
        db.query(func.count(Venda.id))
        .filter(
            func.extract(
                "month",
                Venda.data_venda
            ) == hoje.month,

            func.extract(
                "year",
                Venda.data_venda
            ) == hoje.year
        )
        .scalar()
        or 0
    )

    # ========================================================
    # RECEITA DO MÊS
    # ========================================================

    receita_mes = (
        db.query(func.sum(Venda.valor_total))
        .filter(
            func.extract(
                "month",
                Venda.data_venda
            ) == hoje.month,

            func.extract(
                "year",
                Venda.data_venda
            ) == hoje.year
        )
        .scalar()
        or 0
    )

    # ========================================================
    # VENDAS PENDENTES
    # ========================================================

    pendentes = (
        db.query(func.count(Venda.id))
        .filter(
            Venda.status == "pendente"
        )
        .scalar()
        or 0
    )

    # ========================================================
    # ENVIA PARA O HTML
    # ========================================================

    return templates.TemplateResponse(
        request=request,
        name="vendas/index.html",
        context={

            # Usuário
            "usuario": usuario,

            # Dados
            "vendas": vendas,
            "produtos": produtos,

            # Dashboard
            "vendas_hoje": vendas_hoje,
            "total_mes": total_mes,
            "receita_mes": receita_mes,
            "pendentes": pendentes,

            # Paginação
            "pagina": pagina,
            "por_pagina": por_pagina,
            "total_vendas": total_vendas,
            "total_paginas": total_paginas,

            # Filtros
            "busca": busca,
            "status_filtro": status_filtro,
            "forma_pagamento": forma_pagamento,

            # Ordenação
            "ordenar": ordenar,
        },
    )


# ============================================================
# CRIAR VENDA
# ============================================================

@router.post("")
@router.post("/")
def criar_venda(
    request: Request,

    responsavel: str = Form(...),

    variacao_ids: List[int] = Form(...),

    quantidades: List[int] = Form(...),

    precos: List[float] = Form(...),

    forma_pagamento: str = Form(...),

    observacao: str = Form(""),

    status: str = Form("concluida"),

    db: Session = Depends(get_db),

    usuario=Depends(get_current_user),
):

    itens_validos = []

    # ========================================================
    # VALIDAR PRODUTOS
    # ========================================================

    for variacao_id, quantidade, preco in zip(
        variacao_ids,
        quantidades,
        precos
    ):

        variacao = (
            db.query(ProdutoVariacao)
            .filter(
                ProdutoVariacao.id == variacao_id
            )
            .first()
        )

        if not variacao:
            continue

        if quantidade <= 0:
            continue

        if variacao.estoque_atual < quantidade:
            continue

        itens_validos.append(
            (
                variacao,
                quantidade,
                preco
            )
        )

    # ========================================================
    # NENHUM ITEM VÁLIDO
    # ========================================================

    if not itens_validos:

        return RedirectResponse(
            url="/vendas?erro=estoque",
            status_code=303
        )

    # ========================================================
    # CALCULAR TOTAL
    # ========================================================

    valor_total = sum(
        quantidade * preco

        for _, quantidade, preco

        in itens_validos
    )

    # ========================================================
    # CRIAR VENDA
    # ========================================================

    venda = Venda(
        responsavel=responsavel,
        valor_total=valor_total,
        forma_pagamento=forma_pagamento,
        observacao=observacao,
        status=status,
    )

    db.add(venda)

    db.flush()

    # ========================================================
    # CRIAR ITENS DA VENDA
    # ========================================================

    for variacao, quantidade, preco in itens_validos:

        item = VendaItem(
            venda_id=venda.id,
            produto_variacao_id=variacao.id,
            quantidade=quantidade,
            preco_unitario=preco,
            valor_total=quantidade * preco,
        )

        db.add(item)

        # Baixa no estoque
        variacao.estoque_atual -= quantidade

    # ========================================================
    # SALVAR
    # ========================================================

    db.commit()

    return RedirectResponse(
        url="/vendas?sucesso=1",
        status_code=303
    )


# ============================================================
# DELETAR VENDA
# ============================================================

@router.post("/{venda_id}/deletar")
def deletar_venda(
    venda_id: int,

    db: Session = Depends(get_db),

    usuario=Depends(get_current_user),
):

    venda = (
        db.query(Venda)
        .filter(
            Venda.id == venda_id
        )
        .first()
    )

    if venda:

        db.delete(venda)

        db.commit()

    return RedirectResponse(
        url="/vendas",
        status_code=303
    )