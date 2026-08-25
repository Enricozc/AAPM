import sys
sys.path.insert(0, '.')

# Importar os modelos na ordem correta para evitar erro de relacionamento
import app.models.categoria_model
import app.models.produto_model
import app.models.produto_variacao_model

from sqlalchemy.orm import Session
from app.config.database import SessionLocal
from app.models.produto_model import Produto
from app.models.produto_variacao_model import ProdutoVariacao

db = SessionLocal()

try:
    # Pegar todos os produtos
    produtos = db.query(Produto).all()
    
    print(f"Adicionando variações para {len(produtos)} produtos...\n")
    
    count = 0
    for produto in produtos:
        # Verificar se já tem variações
        if len(produto.variacoes) == 0:
            # Criar uma variação padrão para cada produto
            # Usando tamanho "Único" e cor "Padrão" para produtos simples
            variacao = ProdutoVariacao(
                produto_id=produto.id,
                tamanho="Único",
                cor="Padrão",
                preco=produto.preco,
                estoque_atual=10,  # Estoque padrão de 10 unidades
                ativo=True
            )
            db.add(variacao)
            count += 1
            print(f"✅ {produto.nome} — 10 unidades a R$ {produto.preco:.2f}")
    
    db.commit()
    print(f"\n✅ {count} variações criadas com sucesso!")
    
    # Verificar resultado
    result = db.query(ProdutoVariacao).filter(ProdutoVariacao.ativo == True).count()
    print(f"Total de variações ativas agora: {result}")
    
except Exception as e:
    print(f"❌ Erro: {e}")
    import traceback
    traceback.print_exc()
    db.rollback()
finally:
    db.close()
