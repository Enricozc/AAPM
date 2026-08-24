from datetime import datetime
from pathlib import Path

from fastapi import APIRouter, Depends, Request, Form, status
from fastapi.responses import RedirectResponse
from fastapi.templating import Jinja2Templates

from sqlalchemy.orm import Session
from sqlalchemy import or_

from app.config.database import get_db
from app.config.security import get_current_user
from app.models.armario_model import Armario, ArmarioHistorico
from app.models.user_model import Usuario
from app.services.log_service import registrar_log


router = APIRouter(
    prefix="/armarios",
    tags=["Armários"]
)

BASE_DIR = Path(__file__).resolve().parent.parent

templates = Jinja2Templates(
    directory=str(BASE_DIR / "templates")
)


# ============================================================
# USUÁRIO DO TOKEN
# ============================================================

def _obj(p):

    class U:
        id = p.get("id")
        nome = p.get("nome")
        email = p.get("sub")
        role = p.get("role")

    return U()


# ============================================================
# LISTAR ARMÁRIOS
# PAGINAÇÃO + PESQUISA + FILTRO + ORDENAÇÃO
# ============================================================

@router.get("/")
def listar(
    request: Request,

    # Pesquisa
    busca: str = "",

    # Filtro
    situacao: str = "",

    # Ordenação
    ordenar: str = "numero_asc",

    # Paginação
    pagina: int = 1,
    por_pagina: int = 10,

    payload=Depends(get_current_user),

    db: Session = Depends(get_db)
):

    usuario = _obj(payload)

    # --------------------------------------------------------
    # PAGINAÇÃO
    # --------------------------------------------------------

    if pagina < 1:
        pagina = 1

    if por_pagina not in [5, 10, 20, 50]:
        por_pagina = 10

    # --------------------------------------------------------
    # QUERY
    # --------------------------------------------------------

    query = (
        db.query(Armario)
        .filter(Armario.ativo == True)
    )

    # --------------------------------------------------------
    # PESQUISA
    # --------------------------------------------------------

    if busca:

        query = query.filter(
            or_(
                Armario.numero.ilike(f"%{busca}%"),
                Armario.localizacao.ilike(f"%{busca}%")
            )
        )

    # --------------------------------------------------------
    # FILTRO DE SITUAÇÃO
    # --------------------------------------------------------

    if situacao == "livre":

        query = query.filter(
            Armario.ocupado == False
        )

    elif situacao == "ocupado":

        query = query.filter(
            Armario.ocupado == True
        )

    # --------------------------------------------------------
    # ORDENAÇÃO
    # --------------------------------------------------------

    if ordenar == "numero_desc":

        query = query.order_by(
            Armario.numero.desc()
        )

    elif ordenar == "localizacao":

        query = query.order_by(
            Armario.localizacao.asc()
        )

    elif ordenar == "ocupados":

        query = query.order_by(
            Armario.ocupado.desc(),
            Armario.numero.asc()
        )

    elif ordenar == "livres":

        query = query.order_by(
            Armario.ocupado.asc(),
            Armario.numero.asc()
        )

    else:

        query = query.order_by(
            Armario.numero.asc()
        )

    # --------------------------------------------------------
    # TOTAL
    # --------------------------------------------------------

    total_armarios = query.count()

    # --------------------------------------------------------
    # TOTAL DE PÁGINAS
    # --------------------------------------------------------

    total_paginas = max(
        1,
        (total_armarios + por_pagina - 1)
        // por_pagina
    )

    # --------------------------------------------------------
    # CORRIGIR PÁGINA
    # --------------------------------------------------------

    if pagina > total_paginas:
        pagina = total_paginas

    # --------------------------------------------------------
    # OFFSET
    # --------------------------------------------------------

    offset = (pagina - 1) * por_pagina

    # --------------------------------------------------------
    # BUSCAR ARMÁRIOS DA PÁGINA
    # --------------------------------------------------------

    armarios = (
        query
        .offset(offset)
        .limit(por_pagina)
        .all()
    )

    # --------------------------------------------------------
    # USUÁRIOS ATIVOS
    # --------------------------------------------------------

    usuarios = (
        db.query(Usuario)
        .filter(
            Usuario.ativo == True
        )
        .order_by(
            Usuario.nome.asc()
        )
        .all()
    )

    # --------------------------------------------------------
    # ESTATÍSTICAS
    # --------------------------------------------------------

    # Total geral de armários ativos
    total = (
        db.query(Armario)
        .filter(
            Armario.ativo == True
        )
        .count()
    )

    # Total ocupados
    ocupados = (
        db.query(Armario)
        .filter(
            Armario.ativo == True,
            Armario.ocupado == True
        )
        .count()
    )

    # Total livres
    livres = total - ocupados

    # --------------------------------------------------------
    # TEMPLATE
    # --------------------------------------------------------

    return templates.TemplateResponse(
        request=request,
        name="armarios/index.html",
        context={
            "request": request,

            "usuario": usuario,

            "armarios": armarios,

            "usuarios": usuarios,

            # Estatísticas
            "total": total,
            "ocupados": ocupados,
            "livres": livres,

            # Paginação
            "pagina": pagina,
            "por_pagina": por_pagina,
            "total_armarios": total_armarios,
            "total_paginas": total_paginas,

            # Pesquisa
            "busca": busca,

            # Filtro
            "situacao": situacao,

            # Ordenação
            "ordenar": ordenar,
        }
    )


# ============================================================
# CRIAR ARMÁRIO
# ============================================================

@router.post("/novo")
def criar(
    numero: str = Form(...),

    localizacao: str = Form(""),

    payload=Depends(get_current_user),

    db: Session = Depends(get_db)
):

    usuario = _obj(payload)

    # Verifica duplicidade

    if (
        db.query(Armario)
        .filter(
            Armario.numero == numero
        )
        .first()
    ):

        return RedirectResponse(
            url="/armarios/?erro=numero_duplicado",
            status_code=status.HTTP_303_SEE_OTHER
        )

    # Cria armário

    armario = Armario(
        numero=numero,
        localizacao=localizacao or None
    )

    db.add(armario)

    db.commit()

    # Log

    registrar_log(
        db,
        f"Armário criado: {numero}",
        f"Por: {usuario.nome}",
        "sucesso",
        usuario.id
    )

    return RedirectResponse(
        url="/armarios/?sucesso=criado",
        status_code=status.HTTP_303_SEE_OTHER
    )


# ============================================================
# ATRIBUIR ARMÁRIO
# ============================================================

@router.post("/{aid}/atribuir")
def atribuir(
    aid: int,

    usuario_id: int = Form(...),

    payload=Depends(get_current_user),

    db: Session = Depends(get_db)
):

    usuario_logado = _obj(payload)

    armario = (
        db.query(Armario)
        .filter(
            Armario.id == aid
        )
        .first()
    )

    usuario = (
        db.query(Usuario)
        .filter(
            Usuario.id == usuario_id
        )
        .first()
    )

    # Validação

    if (
        not armario
        or armario.ocupado
        or not usuario
    ):

        return RedirectResponse(
            url="/armarios/?erro=indisponivel",
            status_code=status.HTTP_303_SEE_OTHER
        )

    # Atualiza armário

    armario.ocupado = True

    armario.usuario_id = usuario.id

    armario.atribuido_em = datetime.utcnow()

    # Histórico

    historico = ArmarioHistorico(
        armario_id=armario.id,
        usuario_id=usuario.id,
        usuario_nome=usuario.nome,
        acao="ATRIBUIDO"
    )

    db.add(historico)

    db.commit()

    # Log

    registrar_log(
        db,
        f"Armário {armario.numero} atribuído a {usuario.nome}",
        f"Por: {usuario_logado.nome}",
        "sucesso",
        usuario_logado.id
    )

    return RedirectResponse(
        url="/armarios/?sucesso=atribuido",
        status_code=status.HTTP_303_SEE_OTHER
    )


# ============================================================
# LIBERAR ARMÁRIO
# ============================================================

@router.post("/{aid}/liberar")
def liberar(
    aid: int,

    payload=Depends(get_current_user),

    db: Session = Depends(get_db)
):

    usuario_logado = _obj(payload)

    armario = (
        db.query(Armario)
        .filter(
            Armario.id == aid
        )
        .first()
    )

    if (
        not armario
        or not armario.ocupado
    ):

        return RedirectResponse(
            url="/armarios/?erro=nao_ocupado",
            status_code=status.HTTP_303_SEE_OTHER
        )

    # Nome do usuário anterior

    nome_usuario = (
        armario.usuario.nome
        if armario.usuario
        else "—"
    )

    # Histórico

    historico = ArmarioHistorico(
        armario_id=armario.id,
        usuario_id=armario.usuario_id,
        usuario_nome=nome_usuario,
        acao="LIBERADO"
    )

    db.add(historico)

    # Libera armário

    armario.ocupado = False

    armario.usuario_id = None

    armario.atribuido_em = None

    db.commit()

    # Log

    registrar_log(
        db,
        f"Armário {armario.numero} liberado (era de {nome_usuario})",
        f"Por: {usuario_logado.nome}",
        "alerta",
        usuario_logado.id
    )

    return RedirectResponse(
        url="/armarios/?sucesso=liberado",
        status_code=status.HTTP_303_SEE_OTHER
    )


# ============================================================
# HISTÓRICO DO ARMÁRIO
# ============================================================

@router.get("/{aid}/historico")
def historico(
    aid: int,

    request: Request,

    payload=Depends(get_current_user),

    db: Session = Depends(get_db)
):

    armario = (
        db.query(Armario)
        .filter(
            Armario.id == aid
        )
        .first()
    )

    if not armario:

        return RedirectResponse(
            url="/armarios/"
        )

    historico = (
        db.query(ArmarioHistorico)
        .filter(
            ArmarioHistorico.armario_id == aid
        )
        .order_by(
            ArmarioHistorico.feito_em.desc()
        )
        .all()
    )

    return templates.TemplateResponse(
        request=request,
        name="armarios/historico.html",
        context={
            "request": request,

            "usuario": _obj(payload),

            "armario": armario,

            "historico": historico,
        }
    )


# ============================================================
# DESATIVAR ARMÁRIO
# ============================================================

@router.post("/{aid}/desativar")
def desativar(
    aid: int,

    payload=Depends(get_current_user),

    db: Session = Depends(get_db)
):

    usuario = _obj(payload)

    # Apenas ADMIN

    if usuario.role != "ADMIN":

        return RedirectResponse(
            url="/armarios/?erro=sem_permissao",
            status_code=status.HTTP_303_SEE_OTHER
        )

    armario = (
        db.query(Armario)
        .filter(
            Armario.id == aid
        )
        .first()
    )

    if armario:

        numero = armario.numero

        armario.ativo = False

        armario.ocupado = False

        armario.usuario_id = None

        db.commit()

        registrar_log(
            db,
            f"Armário {numero} desativado",
            f"Por: {usuario.nome}",
            "alerta",
            usuario.id
        )

    return RedirectResponse(
        url="/armarios/?sucesso=desativado",
        status_code=status.HTTP_303_SEE_OTHER
    )