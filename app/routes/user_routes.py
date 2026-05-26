from fastapi import APIRouter, Request, Form
from fastapi.responses import RedirectResponse
from fastapi.templating import Jinja2Templates

router = APIRouter()
templates = Jinja2Templates(directory="app/templates")

# 1. ROTA QUE EXIBE A TELA (O que você já tinha, agora com mensagem de erro na URL)
@router.get("/usuarios")
async def listar_usuarios(request: Request, nome: str = "Eduardo", perfil: str = "ADMIN"):
    # REQUISITO: Usuários comuns não devem acessar a funcionalidade
    if perfil != "ADMIN":
        # REQUISITO: Redirecionamento com mensagem de erro explicativa
        return RedirectResponse(
            url=f"/dashboard?nome={nome}&perfil={perfil}&erro=Acesso+Negado!+Apenas+Administradores+podem+cadastrar+usuarios.", 
            status_code=303
        )
        
    return templates.TemplateResponse(
        "users.html", 
        {
            "request": request, 
            "nome": nome, 
            "perfil": perfil
        }
    )

# 2. A ROTA QUE FALTA: RECEBE E SALVA O CADASTRO COM TRAVA DE SEGURANÇA
@router.post("/usuarios/criar")
async def criar_usuario(
    nome_novo: str = Form(...),
    email_novo: str = Form(...),
    role_nova: str = Form(...),
    status_novo: str = Form(...),
    admin_nome: str = Form(...),   # Nome de quem está logado operando o sistema
    admin_perfil: str = Form(...) # Perfil de quem está logado operando o sistema
):
    # REQUISITO: Garantir segurança total no back-end bloqueando invasões por fora do sistema
    if admin_perfil != "ADMIN":
        return RedirectResponse(
            url=f"/dashboard?nome={admin_nome}&perfil={admin_perfil}&erro=Operacao+bloqueada+por+seguranca.", 
            status_code=303
        )
        
    # [O seu Banco de Dados vai salvar as variáveis aqui futuramente]
    print(f"Usuário criado com sucesso: {nome_novo} ({role_nova})")
    
    # Após salvar, retorna para a página de usuários mantendo o Admin logado
    return RedirectResponse(url=f"/usuarios?nome={admin_nome}&perfil={admin_perfil}", status_code=303)