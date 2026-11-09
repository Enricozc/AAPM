import pytest

from app.models.venda_item_model import VendaItem
from app.models.venda_model import Venda
from app.models.produto_variacao_model import ProdutoVariacao


def sale_data(variation_id, **overrides):
    data = {
        "responsavel": "Operador",
        "variacao_ids": str(variation_id),
        "quantidades": "2",
        "precos": "25.00",
        "forma_pagamento": "pix",
    }
    data.update(overrides)
    return data


def test_venda_com_pagamento_dividido_e_desconto_em_percentual(
    client, db, product_variation
):
    response = client.post(
        "/vendas/",
        data=sale_data(
            product_variation.id,
            desconto="10",
            tipo_desconto="percentual",
            valor_pagamento_1="30",
            forma_pagamento_2="dinheiro",
            valor_pagamento_2="15",
        ),
        follow_redirects=False,
    )

    assert response.status_code == 303
    assert response.headers["location"] == "/vendas?sucesso=1"
    venda = db.query(Venda).one()
    assert venda.valor_subtotal == 50
    assert venda.desconto == 5
    assert venda.valor_total == 45
    assert venda.forma_pagamento == "pix"
    assert venda.valor_pagamento_1 == 30
    assert venda.forma_pagamento_2 == "dinheiro"
    assert venda.valor_pagamento_2 == 15
    assert db.query(VendaItem).one().valor_total == 50
    db.expire_all()
    assert db.query(ProdutoVariacao).one().estoque_atual == 8


def test_venda_simples_legada_sem_campos_novos_continua_funcionando(
    client, db, product_variation
):
    response = client.post(
        "/vendas",
        data=sale_data(product_variation.id),
        follow_redirects=False,
    )

    assert response.status_code == 303
    venda = db.query(Venda).one()
    assert venda.valor_total == 50
    assert venda.desconto == 0
    assert venda.forma_pagamento_2 is None
    assert venda.valor_pagamento_1 == 50


@pytest.mark.parametrize(
    ("fields", "error"),
    [
        ({"desconto": "50.01"}, "desconto"),
        ({"desconto": "1e308"}, "desconto"),
        ({"desconto": "101", "tipo_desconto": "percentual"}, "desconto"),
        ({"valor_pagamento_1": "49"}, "pagamento"),
        (
            {
                "valor_pagamento_1": "30",
                "forma_pagamento_2": "pix",
                "valor_pagamento_2": "20",
            },
            "pagamento",
        ),
        (
            {
                "valor_pagamento_1": "30",
                "forma_pagamento_2": "dinheiro",
                "valor_pagamento_2": "19.99",
            },
            "pagamento",
        ),
        (
            {
                "valor_pagamento_1": "50",
                "forma_pagamento_2": "dinheiro",
                "valor_pagamento_2": "0",
            },
            "pagamento",
        ),
        ({"forma_pagamento": "cheque"}, "pagamento"),
    ],
)
def test_venda_invalida_nao_grava_nem_reduz_estoque(
    client, db, product_variation, fields, error
):
    response = client.post(
        "/vendas/",
        data=sale_data(product_variation.id, **fields),
        follow_redirects=False,
    )

    assert response.status_code == 303
    assert f"erro={error}" in response.headers["location"]
    assert db.query(Venda).count() == 0
    assert db.query(VendaItem).count() == 0
    assert db.query(ProdutoVariacao).one().estoque_atual == 10


def test_venda_sem_estoque_suficiente_e_cancelada(client, db, product_variation):
    response = client.post(
        "/vendas/",
        data=sale_data(product_variation.id, quantidades="11"),
        follow_redirects=False,
    )

    assert response.status_code == 303
    assert "erro=estoque" in response.headers["location"]
    assert db.query(Venda).count() == 0
    assert db.query(ProdutoVariacao).one().estoque_atual == 10


def test_venda_arredonda_desconto_e_total_em_centavos(client, db, product_variation):
    product_variation.preco = 0.1
    db.commit()
    response = client.post(
        "/vendas/",
        data=sale_data(
            product_variation.id,
            quantidades="1",
            precos="0.10",
            desconto="5",
            tipo_desconto="percentual",
            valor_pagamento_1="0.09",
        ),
        follow_redirects=False,
    )

    assert response.status_code == 303
    venda = db.query(Venda).one()
    assert venda.valor_subtotal == 0.1
    assert venda.desconto == 0.01
    assert venda.valor_total == 0.09


def test_lista_de_vendas_exibe_opcoes_de_pagamento_e_desconto(
    client, product_variation
):
    response = client.get("/vendas")

    assert response.status_code == 200
    assert 'name="forma_pagamento_2"' in response.text
    assert 'name="valor_pagamento_2"' in response.text
    assert 'name="desconto"' in response.text
    assert "Saldo restante" in response.text


def test_venda_pode_ser_excluida(client, db, product_variation):
    client.post(
        "/vendas/",
        data=sale_data(product_variation.id),
        follow_redirects=False,
    )
    venda = db.query(Venda).one()

    response = client.post(
        f"/vendas/{venda.id}/deletar", follow_redirects=False
    )

    assert response.status_code == 303
    db.expire_all()
    assert db.query(Venda).count() == 0
    assert db.query(VendaItem).count() == 0


def test_desconto_percentual_de_100_porcento_reduz_total_ao_zero(client, db, product_variation):
    response = client.post(
        "/vendas/",
        data=sale_data(
            product_variation.id,
            quantidades="1",
            precos="19.99",
            desconto="100",
            tipo_desconto="percentual",
            valor_pagamento_1="0.00",
        ),
        follow_redirects=False,
    )

    assert response.status_code == 303
    venda = db.query(Venda).one()
    assert venda.valor_subtotal == 19.99
    assert venda.desconto == 19.99
    assert venda.valor_total == 0
    assert venda.valor_pagamento_1 == 0


def test_desconto_percentual_de_10_porcento_aplica_2_reais(client, db, product_variation):
    response = client.post(
        "/vendas/",
        data=sale_data(
            product_variation.id,
            quantidades="1",
            precos="19.99",
            desconto="10",
            tipo_desconto="percentual",
            valor_pagamento_1="17.99",
        ),
        follow_redirects=False,
    )

    assert response.status_code == 303
    venda = db.query(Venda).one()
    assert venda.valor_subtotal == 19.99
    assert venda.desconto == 2.0
    assert venda.valor_total == 17.99
    assert venda.valor_pagamento_1 == 17.99


def test_desconto_percentual_acima_de_100_e_rejeitado(client, db, product_variation):
    response = client.post(
        "/vendas/",
        data=sale_data(
            product_variation.id,
            quantidades="1",
            precos="19.99",
            desconto="150",
            tipo_desconto="percentual",
            valor_pagamento_1="19.99",
        ),
        follow_redirects=False,
    )

    assert response.status_code == 303
    assert "erro=desconto" in response.headers["location"]
    assert db.query(Venda).count() == 0
