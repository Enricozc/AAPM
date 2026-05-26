from fastapi import APIRouter, Request
from fastapi.templating import Jinja2Templates

router = APIRouter()
templates = Jinja2Templates(directory="app/templates")

@router.get("/dashboard")
async def dashboard(request: Request, nome: str = "Eduardo", perfil: str = "ADMIN"):
    return templates.TemplateResponse(
        "dashboard.html", 
        {
            "request": request, 
            "nome": nome,      # Repassa o nome pro HTML
            "perfil": perfil   # Repassa o perfil pro HTML
        }
    )