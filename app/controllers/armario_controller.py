from datetime import datetime
from pathlib import Path

from fastapi import APIRouter, Depends, Request, Form, status
from fastapi.responses import RedirectResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session

from app.config.database import get_db
from app.config.security import get_current_user, require_admin
from app.models.armario_model import Armario, ArmarioHistorico
from app.models.user_model import Usuario

router = APIRouter(prefix="/armarios", tags=["Armários"])

BASE_DIR = Path(__file__).resolve().parent.parent
templates = Jinja2Templates(directory=str(BASE_DIR / "templates"))


def _usuario_obj(payload: dict):
    class U:
        id    = payload.get("id")
        nome  = payload.get("nome")
        email = payload.get("sub")
        role  = payload.get("role")
    return U()


# ─────────────────────────────────────────
# LISTAGEM
# ─────────────────────────────────────────
@router.get("/")
def listar_armarios(
    request: Request,
    payload=Depends(require_admin),
    db: Session = Depends(get_db)
):
    usuario  = _usuario_obj(payload)
    armarios = (
        db.query(Armario)
        .filter(Armario.ativo == True)
        .order_by(Armario.numero)
        .all()
    )
    usuarios = db.query(Usuario).filter(Usuario.ativo == True).all()

    total      = len(armarios)
    ocupados   = sum(1 for a in armarios if a.ocupado)
    livres     = total - ocupados

    return templates.TemplateResponse(
        request=request,
        name="armarios/index.html",
        context={
            "request":  request,
            "usuario":  usuario,
            "armarios": armarios,
            "usuarios": usuarios,
            "total":    total,
            "ocupados": ocupados,
            "livres":   livres,
        }
    )


# ─────────────────────────────────────────
# CRIAR ARMÁRIO
# ─────────────────────────────────────────
@router.post("/novo")
def criar_armario(
    request: Request,
    numero: str = Form(...),
    localizacao: str = Form(""),
    payload=Depends(require_admin),
    db: Session = Depends(get_db)
):
    existente = db.query(Armario).filter(Armario.numero == numero).first()
    if existente:
        return RedirectResponse(url="/armarios/?erro=numero_duplicado", status_code=status.HTTP_303_SEE_OTHER)

    armario = Armario(numero=numero, localizacao=localizacao or None)
    db.add(armario)
    db.commit()
    return RedirectResponse(url="/armarios/?sucesso=criado", status_code=status.HTTP_303_SEE_OTHER)


# ─────────────────────────────────────────
# ATRIBUIR ARMÁRIO A UM USUÁRIO
# ─────────────────────────────────────────
@router.post("/{armario_id}/atribuir")
def atribuir_armario(
    armario_id: int,
    usuario_id: int = Form(...),
    payload=Depends(require_admin),
    db: Session = Depends(get_db)
):
    armario = db.query(Armario).filter(Armario.id == armario_id).first()
    if not armario or armario.ocupado:
        return RedirectResponse(url="/armarios/?erro=indisponivel", status_code=status.HTTP_303_SEE_OTHER)

    usuario = db.query(Usuario).filter(Usuario.id == usuario_id).first()
    if not usuario:
        return RedirectResponse(url="/armarios/?erro=usuario_invalido", status_code=status.HTTP_303_SEE_OTHER)

    armario.ocupado      = True
    armario.usuario_id   = usuario.id
    armario.atribuido_em = datetime.utcnow()

    hist = ArmarioHistorico(
        armario_id   = armario.id,
        usuario_id   = usuario.id,
        usuario_nome = usuario.nome,
        acao         = "ATRIBUIDO"
    )
    db.add(hist)
    db.commit()
    return RedirectResponse(url="/armarios/?sucesso=atribuido", status_code=status.HTTP_303_SEE_OTHER)


# ─────────────────────────────────────────
# LIBERAR ARMÁRIO
# ─────────────────────────────────────────
@router.post("/{armario_id}/liberar")
def liberar_armario(
    armario_id: int,
    payload=Depends(require_admin),
    db: Session = Depends(get_db)
):
    armario = db.query(Armario).filter(Armario.id == armario_id).first()
    if not armario or not armario.ocupado:
        return RedirectResponse(url="/armarios/?erro=nao_ocupado", status_code=status.HTTP_303_SEE_OTHER)

    hist = ArmarioHistorico(
        armario_id   = armario.id,
        usuario_id   = armario.usuario_id,
        usuario_nome = armario.usuario.nome if armario.usuario else "—",
        acao         = "LIBERADO"
    )
    db.add(hist)

    armario.ocupado      = False
    armario.usuario_id   = None
    armario.atribuido_em = None

    db.commit()
    return RedirectResponse(url="/armarios/?sucesso=liberado", status_code=status.HTTP_303_SEE_OTHER)


# ─────────────────────────────────────────
# HISTÓRICO DE UM ARMÁRIO
# ─────────────────────────────────────────
@router.get("/{armario_id}/historico")
def historico_armario(
    armario_id: int,
    request: Request,
    payload=Depends(require_admin),
    db: Session = Depends(get_db)
):
    usuario = _usuario_obj(payload)
    armario = db.query(Armario).filter(Armario.id == armario_id).first()
    if not armario:
        return RedirectResponse(url="/armarios/")

    historico = (
        db.query(ArmarioHistorico)
        .filter(ArmarioHistorico.armario_id == armario_id)
        .order_by(ArmarioHistorico.feito_em.desc())
        .all()
    )

    return templates.TemplateResponse(
        request=request,
        name="armarios/historico.html",
        context={
            "request":   request,
            "usuario":   usuario,
            "armario":   armario,
            "historico": historico,
        }
    )


# ─────────────────────────────────────────
# DESATIVAR (exclusão lógica)
# ─────────────────────────────────────────
@router.post("/{armario_id}/desativar")
def desativar_armario(
    armario_id: int,
    payload=Depends(require_admin),
    db: Session = Depends(get_db)
):
    armario = db.query(Armario).filter(Armario.id == armario_id).first()
    if armario:
        armario.ativo    = False
        armario.ocupado  = False
        armario.usuario_id = None
        db.commit()
    return RedirectResponse(url="/armarios/?sucesso=desativado", status_code=status.HTTP_303_SEE_OTHER)