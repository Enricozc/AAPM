from fastapi import APIRouter, Request, Depends
from fastapi.templating import Jinja2Templates

from app.config.security import get_current_user

router = APIRouter()
templates = Jinja2Templates(directory="app/templates")


@router.get("/dashboard")
async def dashboard(
    request: Request,
    user=Depends(get_current_user)
):
    usuario = {
        "nome": user.get("email"),
        "role": user.get("role")
    }

    return templates.TemplateResponse(
        request=request,
        name="dashboard.html",
        context={
            "request": request,
            "usuario": usuario,
            "erro": None
        }
    )