from fastapi import APIRouter, Request, Form
from fastapi.responses import RedirectResponse
from fastapi.templating import Jinja2Templates

router = APIRouter()
templates = Jinja2Templates(directory="app/templates")

# 1. TELA DE LOGIN (Acessível via /login ou apenas /)
@router.get("/login")
@router.get("/")
async def login_page(request: Request, erro: str = None):
    return templates.TemplateResponse("login.html", {"request": request, "erro": erro})

# 2. PROCESSAMENTO DO LOGIN (Com envio correto dos dados para o Dashboard)
@router.post("/login")
async def fazer_login(email: str = Form(...), senha: str = Form(...)):
    # Validação do Administrador
    if email == "admin@email.com" and senha == "123456":
        return RedirectResponse(url="/dashboard?nome=Eduardo&perfil=ADMIN", status_code=303)
    
    # Validação de um Funcionário comum (para testes)
    elif email == "user@email.com" and senha == "123456":
        return RedirectResponse(url="/dashboard?nome=Carlos+Souza&perfil=FUNCIONARIO", status_code=303)
    
    # Se errar os dados, volta para o login com a mensagem de erro
    return RedirectResponse(url="/login?erro=E-mail+ou+senha+incorretos.", status_code=303)

# 3. SAÍDA DO SISTEMA (LOGOUT)
@router.get("/logout")
async def logout():
    return RedirectResponse(url="/login", status_code=303)

