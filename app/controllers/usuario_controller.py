from pathlib import Path
from fastapi import APIRouter, Depends, Request, Form, status
from fastapi.responses import RedirectResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session
from app.config.database import get_db
from app.config.security import require_admin, hash_password
from app.models.user_model import Usuario
from app.services.log_service import registrar_log

router = APIRouter(prefix="/usuarios", tags=["Usuários"])
BASE_DIR = Path(__file__).resolve().parent.parent
templates = Jinja2Templates(directory=str(BASE_DIR / "templates"))

def _obj(p):
    class U:
        id=p.get("id"); nome=p.get("nome"); email=p.get("sub"); role=p.get("role")
    return U()

@router.get("/")
def listar(request: Request, payload=Depends(require_admin), db: Session=Depends(get_db)):
    u = _obj(payload)
    associados = db.query(Usuario).order_by(Usuario.nome).all()
    total = len(associados); ativos = sum(1 for x in associados if x.ativo)
    return templates.TemplateResponse(request=request, name="usuarios/index.html",
        context={"request":request,"usuario":u,"associados":associados,"total":total,"ativos":ativos,"inativos":total-ativos})

@router.get("/novo")
def tela_novo(request: Request, payload=Depends(require_admin)):
    return templates.TemplateResponse(request=request, name="usuarios/form.html",
        context={"request":request,"usuario":_obj(payload),"editando":None})

@router.post("/novo")
def criar(request: Request, nome: str=Form(...), email: str=Form(...), matricula: str=Form(""),
          cargo: str=Form(""), senha: str=Form(...), role: str=Form("operador"),
          payload=Depends(require_admin), db: Session=Depends(get_db)):
    ul = _obj(payload)
    if db.query(Usuario).filter(Usuario.email==email).first():
        return templates.TemplateResponse(request=request, name="usuarios/form.html",
            context={"request":request,"usuario":ul,"editando":None,"erro":"E-mail já cadastrado."})
    if matricula and db.query(Usuario).filter(Usuario.matricula==matricula).first():
        return templates.TemplateResponse(request=request, name="usuarios/form.html",
            context={"request":request,"usuario":ul,"editando":None,"erro":"Matrícula já em uso."})
    novo = Usuario(nome=nome,email=email,matricula=matricula or None,cargo=cargo or None,
                   hashed_password=hash_password(senha),role=role,ativo=True)
    db.add(novo); db.commit()
    registrar_log(db, f"Novo associado cadastrado: {nome}", f"Por: {ul.nome}", "sucesso", ul.id)
    return RedirectResponse(url="/usuarios/?sucesso=criado", status_code=status.HTTP_303_SEE_OTHER)

@router.get("/{uid}/editar")
def tela_editar(uid: int, request: Request, payload=Depends(require_admin), db: Session=Depends(get_db)):
    e = db.query(Usuario).filter(Usuario.id==uid).first()
    if not e: return RedirectResponse(url="/usuarios/")
    return templates.TemplateResponse(request=request, name="usuarios/form.html",
        context={"request":request,"usuario":_obj(payload),"editando":e})

@router.post("/{uid}/editar")
def salvar(uid: int, nome: str=Form(...), email: str=Form(...), matricula: str=Form(""),
           cargo: str=Form(""), senha: str=Form(""), role: str=Form("operador"),
           payload=Depends(require_admin), db: Session=Depends(get_db)):
    ul = _obj(payload); u = db.query(Usuario).filter(Usuario.id==uid).first()
    if not u: return RedirectResponse(url="/usuarios/")
    u.nome=nome; u.email=email; u.matricula=matricula or None; u.cargo=cargo or None; u.role=role
    if senha: u.hashed_password=hash_password(senha)
    db.commit()
    registrar_log(db, f"Associado editado: {nome}", f"Por: {ul.nome}", "info", ul.id)
    return RedirectResponse(url="/usuarios/?sucesso=editado", status_code=status.HTTP_303_SEE_OTHER)

@router.post("/{uid}/toggle")
def toggle(uid: int, payload=Depends(require_admin), db: Session=Depends(get_db)):
    ul = _obj(payload); u = db.query(Usuario).filter(Usuario.id==uid).first()
    if u:
        u.ativo = not u.ativo; db.commit()
        registrar_log(db, f"Associado {'ativado' if u.ativo else 'desativado'}: {u.nome}", f"Por: {ul.nome}", "alerta", ul.id)
    return RedirectResponse(url="/usuarios/?sucesso=atualizado", status_code=status.HTTP_303_SEE_OTHER)