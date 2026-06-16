from datetime import datetime
from pathlib import Path
from fastapi import APIRouter, Depends, Request, Form, status
from fastapi.responses import RedirectResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session
from app.config.database import get_db
from app.config.security import get_current_user
from app.models.armario_model import Armario, ArmarioHistorico
from app.models.user_model import Usuario
from app.services.log_service import registrar_log

router = APIRouter(prefix="/armarios", tags=["Armários"])
BASE_DIR = Path(__file__).resolve().parent.parent
templates = Jinja2Templates(directory=str(BASE_DIR / "templates"))

def _obj(p):
    class U:
        id=p.get("id"); nome=p.get("nome"); email=p.get("sub"); role=p.get("role")
    return U()

@router.get("/")
def listar(request: Request, payload=Depends(get_current_user), db: Session=Depends(get_db)):
    u = _obj(payload)
    armarios = db.query(Armario).filter(Armario.ativo==True).order_by(Armario.numero).all()
    usuarios = db.query(Usuario).filter(Usuario.ativo==True).all()
    total=len(armarios); ocupados=sum(1 for a in armarios if a.ocupado)
    return templates.TemplateResponse(request=request, name="armarios/index.html",
        context={"request":request,"usuario":u,"armarios":armarios,"usuarios":usuarios,
                 "total":total,"ocupados":ocupados,"livres":total-ocupados})

@router.post("/novo")
def criar(numero: str=Form(...), localizacao: str=Form(""), payload=Depends(get_current_user), db: Session=Depends(get_db)):
    ul = _obj(payload)
    if db.query(Armario).filter(Armario.numero==numero).first():
        return RedirectResponse(url="/armarios/?erro=numero_duplicado", status_code=status.HTTP_303_SEE_OTHER)
    db.add(Armario(numero=numero, localizacao=localizacao or None)); db.commit()
    registrar_log(db, f"Armário criado: {numero}", f"Por: {ul.nome}", "sucesso", ul.id)
    return RedirectResponse(url="/armarios/?sucesso=criado", status_code=status.HTTP_303_SEE_OTHER)

@router.post("/{aid}/atribuir")
def atribuir(aid: int, usuario_id: int=Form(...), payload=Depends(get_current_user), db: Session=Depends(get_db)):
    ul = _obj(payload)
    a = db.query(Armario).filter(Armario.id==aid).first()
    u = db.query(Usuario).filter(Usuario.id==usuario_id).first()
    if not a or a.ocupado or not u:
        return RedirectResponse(url="/armarios/?erro=indisponivel", status_code=status.HTTP_303_SEE_OTHER)
    a.ocupado=True; a.usuario_id=u.id; a.atribuido_em=datetime.utcnow()
    db.add(ArmarioHistorico(armario_id=a.id,usuario_id=u.id,usuario_nome=u.nome,acao="ATRIBUIDO"))
    db.commit()
    registrar_log(db, f"Armário {a.numero} atribuído a {u.nome}", f"Por: {ul.nome}", "sucesso", ul.id)
    return RedirectResponse(url="/armarios/?sucesso=atribuido", status_code=status.HTTP_303_SEE_OTHER)

@router.post("/{aid}/liberar")
def liberar(aid: int, payload=Depends(get_current_user), db: Session=Depends(get_db)):
    ul = _obj(payload)
    a = db.query(Armario).filter(Armario.id==aid).first()
    if not a or not a.ocupado:
        return RedirectResponse(url="/armarios/?erro=nao_ocupado", status_code=status.HTTP_303_SEE_OTHER)
    nome_u = a.usuario.nome if a.usuario else "—"
    db.add(ArmarioHistorico(armario_id=a.id,usuario_id=a.usuario_id,usuario_nome=nome_u,acao="LIBERADO"))
    a.ocupado=False; a.usuario_id=None; a.atribuido_em=None; db.commit()
    registrar_log(db, f"Armário {a.numero} liberado (era de {nome_u})", f"Por: {ul.nome}", "alerta", ul.id)
    return RedirectResponse(url="/armarios/?sucesso=liberado", status_code=status.HTTP_303_SEE_OTHER)

@router.get("/{aid}/historico")
def historico(aid: int, request: Request, payload=Depends(get_current_user), db: Session=Depends(get_db)):
    a = db.query(Armario).filter(Armario.id==aid).first()
    if not a: return RedirectResponse(url="/armarios/")
    hist = db.query(ArmarioHistorico).filter(ArmarioHistorico.armario_id==aid).order_by(ArmarioHistorico.feito_em.desc()).all()
    return templates.TemplateResponse(request=request, name="armarios/historico.html",
        context={"request":request,"usuario":_obj(payload),"armario":a,"historico":hist})

@router.post("/{aid}/desativar")
def desativar(aid: int, payload=Depends(get_current_user), db: Session=Depends(get_db)):
    ul = _obj(payload)
    # Apenas ADMIN pode desativar
    if ul.role != "ADMIN":
        return RedirectResponse(url="/armarios/?erro=sem_permissao", status_code=status.HTTP_303_SEE_OTHER)
    a = db.query(Armario).filter(Armario.id==aid).first()
    if a:
        a.ativo=False; a.ocupado=False; a.usuario_id=None; db.commit()
        registrar_log(db, f"Armário {a.numero} desativado", f"Por: {ul.nome}", "alerta", ul.id)
    return RedirectResponse(url="/armarios/?sucesso=desativado", status_code=status.HTTP_303_SEE_OTHER)