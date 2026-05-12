from fastapi import APIRouter
from app.controllers.auth_controller import login, login_page, logout

router = APIRouter() # <--- ESSA LINHA É A QUE ESTÁ FALTANDO OU COM NOME ERRADO

router.get("/login")(login_page)
router.post("/login")(login)
router.get("/logout")(logout)