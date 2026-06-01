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

    return templates.TemplateResponse(
        "dashboard.html",
        {
            "request": request,
            "nome": user.get("email"),
            "perfil": user.get("role")
        }
    )