from app.models.armario_model import Aluno, Armario, ArmarioHistorico
from app.models.categoria_model import Categoria
from app.models.fechamento_model import Fechamento
from app.models.produto_model import Produto
from app.models.produto_variacao_model import ProdutoVariacao
from app.models.user_model import Usuario


def test_login_logout_e_protecao_de_credenciais_invalidas(client, db, admin_user):
    assert client.get("/auth/login").status_code == 200
    failed = client.post(
        "/auth/login",
        data={"email": admin_user.email, "senha": "incorreta"},
    )
    assert failed.status_code == 401
    logged_in = client.post(
        "/auth/login",
        data={"email": admin_user.email, "senha": "senha-segura"},
        follow_redirects=False,
    )
    assert logged_in.status_code == 303
    assert "access_token" in logged_in.cookies
    assert client.get("/auth/logout", follow_redirects=False).status_code == 303


def test_rotas_de_recuperacao_de_senha(client, admin_user, monkeypatch):
    enviados = []
    monkeypatch.setattr(
        "app.controllers.auth_controller.enviar_email_recuperacao",
        lambda **dados: enviados.append(dados),
    )
    assert client.post(
        "/auth/forgot-password", data={"email": "naoexiste@aapm.test"}
    ).status_code == 200
    assert client.post(
        "/auth/forgot-password", data={"email": admin_user.email}
    ).status_code == 200
    assert len(enviados) == 1

    token = enviados[0]["link"].split("token=", 1)[1]
    assert client.get(f"/auth/reset-password?token={token}").status_code == 200
    invalid_password = client.post(
        "/auth/reset-password",
        data={
            "token": token,
            "nova_senha": "123",
            "confirmar_senha": "123",
        },
    )
    assert invalid_password.status_code == 400
    reset = client.post(
        "/auth/reset-password",
        data={
            "token": token,
            "nova_senha": "senha-nova",
            "confirmar_senha": "senha-nova",
        },
        follow_redirects=False,
    )
    assert reset.status_code == 303


def test_rotas_publicas_dashboard_e_paginas_de_listagem(client):
    assert client.get("/").status_code == 200
    assert client.get("/dashboard").status_code == 200
    assert client.get("/categorias/").status_code == 200
    assert client.get("/usuarios/").status_code == 200
    assert client.get("/armarios/").status_code == 200
    assert client.get("/produtos/").status_code == 200
    assert client.get("/produtos/desativados/listar").status_code == 200
    assert client.get("/fechamento/").status_code == 200


def test_crud_categoria_e_validacao_de_duplicidade(client, db):
    assert client.get("/categorias/nova").status_code == 200
    created = client.post(
        "/categorias/nova", data={"nome": "Bebidas"}, follow_redirects=False
    )
    assert created.status_code == 303
    duplicate = client.post("/categorias/nova", data={"nome": "bebidas"})
    assert duplicate.status_code == 400
    category = db.query(Categoria).one()
    assert client.get(f"/categorias/{category.id}/editar").status_code == 200
    updated = client.post(
        f"/categorias/{category.id}/editar",
        data={"nome": "Alimentos"},
        follow_redirects=False,
    )
    assert updated.status_code == 303
    assert client.post(
        f"/categorias/{category.id}/toggle-ativo", follow_redirects=False
    ).status_code == 303


def test_crud_usuario_e_bloqueio_de_email_duplicado(client, db, admin_user):
    assert client.get("/usuarios/novo").status_code == 200
    payload = {
        "nome": "Operador",
        "email": "operador@aapm.test",
        "senha": "senha123",
        "role": "operador",
    }
    assert client.post(
        "/usuarios/novo", data=payload, follow_redirects=False
    ).status_code == 302
    assert client.post("/usuarios/novo", data=payload).status_code == 200
    user = db.query(Usuario).filter_by(email=payload["email"]).one()
    assert client.get(f"/usuarios/{user.id}/editar").status_code == 200
    assert client.post(
        f"/usuarios/{user.id}/editar",
        data={"nome": "Operador 2", "email": payload["email"], "role": "operador"},
        follow_redirects=False,
    ).status_code == 302
    assert client.post(
        f"/usuarios/{user.id}/deletar", follow_redirects=False
    ).status_code == 302


def test_crud_produto_estoque_desativacao_e_reativacao(client, db):
    assert client.get("/produtos/novo").status_code == 200
    created = client.post(
        "/produtos/novo",
        data={"nome": "Boné", "preco": "30", "categoria_id": "0"},
        follow_redirects=False,
    )
    assert created.status_code == 302
    product = db.query(Produto).one()
    variation = ProdutoVariacao(
        produto_id=product.id,
        tamanho="U",
        cor="Preto",
        estoque_atual=2,
    )
    db.add(variation)
    db.commit()
    assert client.get(f"/produtos/{product.id}/editar").status_code == 200
    assert client.post(
        f"/produtos/{product.id}/editar",
        data={"nome": "Boné ajustado", "preco": "32", "categoria_id": "0"},
        follow_redirects=False,
    ).status_code == 302
    assert client.post(
        f"/produtos/{product.id}/variacao/{variation.id}/estoque",
        data={"estoque_atual": "5"},
        follow_redirects=False,
    ).status_code == 302
    assert client.post(
        f"/produtos/{product.id}/desativar", follow_redirects=False
    ).status_code == 302
    assert client.post(
        f"/produtos/{product.id}/ativar", follow_redirects=False
    ).status_code == 302


def test_armario_atribuicao_historico_liberacao_e_desativacao(client, db, admin_user):
    created = client.post(
        "/armarios/novo",
        data={"numero": "A1", "localizacao": "Bloco A"},
        follow_redirects=False,
    )
    assert created.status_code == 303
    locker = db.query(Armario).one()
    assert client.post(
        "/armarios/alunos/novo",
        data={
            "nome": "Aluno de teste",
            "ra": "20260001",
            "turma_curso": "2º ano - Informática",
        },
        follow_redirects=False,
    ).status_code == 303
    student = db.query(Aluno).one()
    assert client.post(
        f"/armarios/{locker.id}/atribuir",
        data={"aluno_id": student.id},
        follow_redirects=False,
    ).status_code == 303
    db.refresh(locker)
    assert locker.aluno_id == student.id
    history_page = client.get(f"/armarios/{locker.id}/historico")
    assert history_page.status_code == 200
    assert "20260001" in history_page.text
    assert "2º ano - Informática" in history_page.text
    assert client.post(
        f"/armarios/{locker.id}/liberar", follow_redirects=False
    ).status_code == 303
    history = (
        db.query(ArmarioHistorico)
        .filter_by(armario_id=locker.id)
        .order_by(ArmarioHistorico.id)
        .all()
    )
    assert [entry.usuario_nome for entry in history] == [
        "Aluno de teste",
        "Aluno de teste",
    ]
    assert history[0].aluno_ra == "20260001"
    assert history[0].aluno_turma_curso == "2º ano - Informática"
    assert client.post(
        f"/armarios/{locker.id}/desativar", follow_redirects=False
    ).status_code == 303


def test_paginacao_busca_e_ordenacao_de_armarios(client, db):
    db.add_all(
        [
            Armario(numero=f"B{numero}", localizacao="Bloco B")
            for numero in range(1, 7)
        ]
    )
    db.commit()
    response = client.get(
        "/armarios/?busca=B&pagina=2&por_pagina=5&ordenar=numero_desc"
    )

    assert response.status_code == 200
    assert "B1" in response.text
    assert "B6" not in response.text


def test_cadastro_de_alunos_independente_e_regras_de_atribuicao(client, db):
    assert client.post(
        "/armarios/alunos/novo",
        data={"nome": "Aluno sem RA"},
        follow_redirects=False,
    ).status_code == 422
    assert db.query(Aluno).count() == 0

    assert client.post(
        "/armarios/alunos/novo",
        data={"nome": "   ", "ra": "RA-1"},
        follow_redirects=False,
    ).status_code == 303
    assert db.query(Aluno).count() == 0

    assert client.post(
        "/armarios/alunos/novo",
        data={
            "nome": "Marina Souza",
            "ra": " ab-123 ",
            "turma_curso": "3º ano - Redes",
        },
        follow_redirects=False,
    ).status_code == 303
    student = db.query(Aluno).one()
    assert student.ra == "AB-123"
    assert student.turma_curso == "3º ano - Redes"
    duplicate_ra = client.post(
        "/armarios/alunos/novo",
        data={"nome": "Outra aluna", "ra": "ab-123"},
        follow_redirects=False,
    )
    assert duplicate_ra.status_code == 303
    assert "ra_duplicado" in duplicate_ra.headers["location"]
    assert db.query(Aluno).count() == 1
    another_student = Aluno(nome="Outro aluno", ra="AB-999")
    db.add(another_student)
    db.commit()
    duplicate_edit = client.post(
        f"/armarios/alunos/{another_student.id}/editar",
        data={"nome": "Outro aluno", "ra": "ab-123"},
        follow_redirects=False,
    )
    assert duplicate_edit.status_code == 303
    assert "ra_duplicado" in duplicate_edit.headers["location"]
    assert db.query(Usuario).count() == 0
    first_locker = Armario(numero="C1")
    second_locker = Armario(numero="C2")
    db.add_all([first_locker, second_locker])
    db.commit()
    db.refresh(first_locker)
    db.refresh(second_locker)

    page = client.get("/armarios/")
    assert page.status_code == 200
    assert "Cadastro independente" in page.text
    assert "Marina Souza" in page.text
    assert "AB-123" in page.text
    assert "3º ano - Redes" in page.text
    assert client.post(
        f"/armarios/{first_locker.id}/atribuir",
        data={"aluno_id": student.id},
        follow_redirects=False,
    ).status_code == 303
    searched = client.get("/armarios/?busca=AB-123")
    assert "Armário C1" in searched.text
    assert "Armário C2" not in searched.text
    assert client.post(
        f"/armarios/{second_locker.id}/atribuir",
        data={"aluno_id": student.id},
        follow_redirects=False,
    ).status_code == 303
    db.refresh(second_locker)
    assert second_locker.ocupado is False

    assert client.post(
        f"/armarios/alunos/{student.id}/excluir",
        follow_redirects=False,
    ).status_code == 303
    assert db.query(Aluno).filter_by(id=student.id).one()

    assert client.post(
        f"/armarios/alunos/{student.id}/editar",
        data={
            "nome": "Marina Silva",
            "ra": "AB-456",
            "turma_curso": "3º ano - Desenvolvimento",
        },
        follow_redirects=False,
    ).status_code == 303
    db.refresh(student)
    assert student.nome == "Marina Silva"
    assert student.ra == "AB-456"
    assert student.turma_curso == "3º ano - Desenvolvimento"

    assert client.post(
        f"/armarios/{first_locker.id}/liberar",
        follow_redirects=False,
    ).status_code == 303
    assert client.post(
        f"/armarios/alunos/{student.id}/excluir",
        follow_redirects=False,
    ).status_code == 303
    assert db.query(Aluno).filter_by(id=student.id).first() is None


def test_fechamento_registrado_e_token_reset_invalido(client, db):
    assert client.post(
        "/fechamento/confirmar",
        data={"observacao": "Fechamento de teste"},
        follow_redirects=False,
    ).status_code == 303
    fechamento = db.query(Fechamento).one()
    assert fechamento.usuario == "Administrador"
    assert client.get("/auth/reset-password?token=invalido").status_code == 400
    assert client.post(
        "/auth/reset-password",
        data={
            "token": "invalido",
            "nova_senha": "senha123",
            "confirmar_senha": "senha123",
        },
    ).status_code == 400


def test_busca_ordenacao_paginacao_e_filtros_de_produto(client, db, product_variation):
    product_variation.produto.nome = "Camiseta azul"
    db.add_all(
        [
            Produto(nome=f"Produto {numero}", preco=10)
            for numero in range(7)
        ]
    )
    db.commit()
    response = client.get(
        "/produtos/?busca=azul&pagina=1&por_pagina=6&ordenar=nome&direcao=desc"
    )
    assert response.status_code == 200
    assert "Camiseta azul" in response.text
    assert client.get("/produtos/?pagina=0&por_pagina=7&ordenar=invalid").status_code == 200
    pagina_dois = client.get("/produtos/?pagina=2&por_pagina=6&ordenar=nome")
    assert pagina_dois.status_code == 200
    assert "Produto 6" in pagina_dois.text
