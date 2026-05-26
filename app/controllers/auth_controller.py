from fastapi import APIRouter, Request, Form
from fastapi.templating import Jinja2Templates
from fastapi.responses import RedirectResponse

router = APIRouter()

templates = Jinja2Templates(
    directory="app/templates"
)


# ABRIR LOGIN
@router.get("/login")
async def login_page(request: Request):

    return templates.TemplateResponse(
        request,
        "login.html",
        {
            "request": request
        }
    )


# FAZER LOGIN
@router.post("/login")
async def fazer_login(
    request: Request,
    email: str = Form(...),
    senha: str = Form(...)
):

    return RedirectResponse(
        "/dashboard",
        status_code=302
    )


# DASHBOARD
@router.get("/dashboard")
async def dashboard(request: Request):

    return templates.TemplateResponse(
        request,
        "dashboard.html",
        {
            "request": request
        }
    )

# EXIBIR TELA DE USUÁRIOS (PROTEGIDA PARA ADMIN)
@router.get("/usuarios")
async def gerenciar_usuarios(request: Request, nome: str = "Usuário", perfil: str = "FUNCIONARIO"):
    # REGRA CRUCIAL: Se não for ADMIN, barra o acesso imediatamente
    if perfil != "ADMIN":
        return RedirectResponse(url="/dashboard?nome=" + nome + "&perfil=" + perfil, status_code=303)
        
    return templates.TemplateResponse(
        request,
        "usuarios.html",
        {
            "request": request,
            "nome": nome,
            "perfil": perfil
        }
    )

# AÇÃO DE CRIAR USUÁRIO
@router.post("/usuarios/criar")
async def criar_usuario(
    nome: str = Form(...),
    email_novo: str = Form(...),
    role: str = Form(...),
    status: str = Form(...)
):
    # Aqui o seu backend salvaria os dados no banco de dados.
    # Por enquanto, redirecionamos de volta para manter o fluxo funcionando.
    return RedirectResponse(url="/usuarios?nome=Ricardo+Silva&perfil=ADMIN", status_code=303)

# AÇÃO DE ATIVAR/DESATIVAR
@router.post("/usuarios/alterar-status")
async def alterar_status(email_usuario: str = Form(...)):
    # Lógica para inverter o status do usuário no banco de dados.
    return RedirectResponse(url="/usuarios?nome=Ricardo+Silva&perfil=ADMIN", status_code=303)