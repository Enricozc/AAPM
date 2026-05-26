from fastapi import APIRouter, Request, Depends, Form
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session

from app.config.database import get_db
from app.services.auth_service import authenticate_user
from app.config.security import create_access_token

# ESTA LINHA É O QUE ESTAVA FALTANDO
router = APIRouter()

templates = Jinja2Templates(
    directory="app/templates"
)


@router.get("/login", response_class=HTMLResponse)
def login_page(request: Request):

    return templates.TemplateResponse(
        request,
        "login.html",
        {"request": request}
    )


@router.post("/login")
def login(
    request: Request,
    email: str = Form(...),
    password: str = Form(...),
    db: Session = Depends(get_db)
):

    user = authenticate_user(
        db,
        email,
        password
    )

    if not user:

        return templates.TemplateResponse(
            request,
            "login.html",
            {
                "request": request,
                "erro": "E-mail ou senha inválidos"
            }
        )

    token = create_access_token({
        "sub": user.email,
        "role": user.role
    })

    response = RedirectResponse(
        url="/dashboard",
        status_code=302
    )

    response.set_cookie(
        key="access_token",
        value=token,
        httponly=True
    )

    return response


@router.get("/logout")
def logout():

    response = RedirectResponse(
        url="/login",
        status_code=302
    )

    response.delete_cookie(
        "access_token"
    )

    return response