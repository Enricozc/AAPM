# controllers/categoria_controller.py
# Categorias são gerenciadas apenas por admins.
# Operadores apenas visualizam (via select no form de produto).
# ============================================================

from fastapi import APIRouter, Depends, Request, Form, status
from fastapi.responses import RedirectResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session

from app.config.database import get_db
from app.models.categoria_model import Categoria
from app.config.security import require_admin

router = APIRouter(prefix="/categorias", tags=["Categorias"])

templates = Jinja2Templates(directory="app/templates")


# ============================================================
# LISTAGEM
# ============================================================

@router.get("/")
def listar_categorias(
    request: Request,
    db: Session = Depends(get_db),
    admin = Depends(require_admin)
):
    """
    Lista todas as categorias ordenadas por nome.
    """
    categorias = db.query(Categoria).order_by(Categoria.nome).all()

    return templates.TemplateResponse(
        request,
        "categorias/index.html",  # ✅ CORRIGIDO: Apontando para index.html existente
        {
            "request":    request,
            "usuario":    admin,
            "categorias": categorias,
        }
    )


# ============================================================
# CADASTRO
# ============================================================

@router.get("/nova")
def form_nova_categoria(
    request: Request,
    admin = Depends(require_admin)
):
    """Exibe o formulário de cadastro de categoria."""
    return templates.TemplateResponse(
        request,
        "categorias/form.html",  # ✅ CORRIGIDO: Apontando para form.html existente
        {
            "request":  request,
            "usuario":  admin,
            "editando": None,  # Indica que é um formulário de criação
        }
    )


@router.post("/nova")
def criar_categoria(
    request: Request,
    nome: str = Form(...),
    db: Session = Depends(get_db),
    admin = Depends(require_admin)
):
    """Cria uma nova categoria verificando duplicidade de nome."""
    existente = db.query(Categoria).filter(
        Categoria.nome.ilike(nome.strip())
    ).first()

    if existente:
        return templates.TemplateResponse(
            request,
            "categorias/form.html",  # ✅ CORRIGIDO: Retorna para form.html em caso de erro
            {
                "request":  request,
                "usuario":  admin,
                "editando": None,
                "erro":     "Já existe uma categoria com este nome.",
                "valores":  {"nome": nome},
            },
            status_code=400
        )

    nova_cat = Categoria(nome=nome.strip())
    db.add(nova_cat)
    db.commit()

    return RedirectResponse(url="/categorias?criado=ok", status_code=status.HTTP_303_SEE_OTHER)


# ============================================================
# EDIÇÃO
# ============================================================

@router.get("/{categoria_id}/editar")
def form_editar_categoria(
    categoria_id: int,
    request: Request,
    db: Session = Depends(get_db),
    admin = Depends(require_admin)
):
    """Exibe o formulário preenchido com os dados da categoria."""
    editando = db.query(Categoria).filter(
        Categoria.id == categoria_id
    ).first()

    if not editando:
        return RedirectResponse(url="/categorias", status_code=status.HTTP_303_SEE_OTHER)

    return templates.TemplateResponse(
        request,
        "categorias/form.html",  # ✅ CORRIGIDO: Apontando para form.html existente
        {
            "request":  request,
            "usuario":  admin,
            "editando": editando,  # Passa o objeto para preencher os campos
        }
    )


@router.post("/{categoria_id}/editar")
def editar_categoria(
    categoria_id: int,
    request: Request,
    nome: str = Form(...),
    db: Session = Depends(get_db),
    admin = Depends(require_admin)
):
    """Atualiza os dados da categoria."""
    editando = db.query(Categoria).filter(
        Categoria.id == categoria_id
    ).first()

    if not editando:
        return RedirectResponse(url="/categorias", status_code=status.HTTP_303_SEE_OTHER)

    conflito = db.query(Categoria).filter(
        Categoria.nome.ilike(nome.strip()),
        Categoria.id != categoria_id
    ).first()

    if conflito:
        return templates.TemplateResponse(
            request,
            "categorias/form.html",  # ✅ CORRIGIDO: Retorna para form.html em caso de erro
            {
                "request":  request,
                "usuario":  admin,
                "editando": editando,
                "erro":     "Já existe outra categoria com este nome.",
            },
            status_code=400
        )

    editando.nome = nome.strip()
    db.commit()

    return RedirectResponse(url="/categorias?editado=ok", status_code=status.HTTP_303_SEE_OTHER)


# ============================================================
# TOGGLE ATIVO (ESTADO ATIVO/INATIVO NO BANCO)
# ============================================================

@router.post("/{categoria_id}/toggle-ativo")
def toggle_ativo(
    categoria_id: int,
    db: Session = Depends(get_db),
    admin = Depends(require_admin)
):
    """
    Ativa ou desativa uma categoria de forma segura.
    """
    # 🛠️ CORRIGIDO: Categoria.id com "C" maiúsculo para referenciar a classe do SQLAlchemy corretamente
    categoria = db.query(Categoria).filter(
        Categoria.id == categoria_id 
    ).first()

    if not categoria:
        return RedirectResponse(url="/categorias", status_code=status.HTTP_303_SEE_OTHER)

    if categoria.ativo:
        produtos_ativos = [p for p in categoria.produtos if p.ativo]

        if produtos_ativos:
            return RedirectResponse(
                url=f"/categorias?erro=produtos_vinculados&categoria={categoria.nome}",
                status_code=status.HTTP_303_SEE_OTHER
            )

    categoria.ativo = not categoria.ativo
    db.commit()

    return RedirectResponse(url="/categorias", status_code=status.HTTP_303_SEE_OTHER)