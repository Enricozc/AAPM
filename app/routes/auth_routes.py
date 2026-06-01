from fastapi import APIRouter, Request, Form
from fastapi.responses import RedirectResponse
from fastapi.templating import Jinja2Templates

router = APIRouter()

templates = Jinja2Templates(
    directory="app/templates"
)

# TELA DE LOGIN
@router.get("/")
@router.get("/login")
async def login_page(
    request: Request,
    erro: str = None
):
    return templates.TemplateResponse(
        "login.html",                             # 1º argumento: O arquivo HTML
        {"request": request, "erro": erro},       # 2º argumento: O contexto (dicionário)
        request=request                           # 3º argumento: O request explícito exigido pela nova versão!
    )
# PROCESSAR LOGIN
@router.post("/login")
async def fazer_login(
    email: str = Form(...),
    senha: str = Form(...)
):
    if email == "admin@email.com" and senha == "123456":
        return RedirectResponse(
            url="/dashboard?nome=Eduardo&perfil=ADMIN",
            status_code=303
        )

    elif email == "user@email.com" and senha == "123456":
        return RedirectResponse(
            url="/dashboard?nome=Carlos+Souza&perfil=FUNCIONARIO",
            status_code=303
        )

    return RedirectResponse(
        url="/login?erro=E-mail+ou+senha+incorretos.",
        status_code=303
    )

# LOGOUT
@router.get("/logout")
async def logout():
    return RedirectResponse(
        url="/login",
        status_code=303
    )