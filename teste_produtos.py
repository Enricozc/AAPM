import sys
sys.path.insert(0, '.')

from sqlalchemy import create_engine, inspect, text
from app.config.settings import settings

engine = create_engine(settings.database_url)

with engine.connect() as conn:
    inspector = inspect(engine)
    
    # Verificar se as tabelas existem
    tables = inspector.get_table_names()
    print(f"Tabelas no banco: {tables}\n")
    
    if 'produtos' in tables:
        # Contar produtos
        result = conn.execute(text("SELECT COUNT(*) FROM produtos WHERE ativo = 1"))
        count = result.scalar()
        print(f"Produtos ativos: {count}")
        
        # Total de variações
        result = conn.execute(text("SELECT COUNT(*) FROM produto_variacoes"))
        total_vars = result.scalar()
        print(f"Total de variações: {total_vars}")
        
        # Variações ativas
        result = conn.execute(text("SELECT COUNT(*) FROM produto_variacoes WHERE ativo = 1"))
        ativas = result.scalar()
        print(f"Variações ativas: {ativas}")
        
        # Variações inativas
        result = conn.execute(text("SELECT COUNT(*) FROM produto_variacoes WHERE ativo = 0"))
        inativas = result.scalar()
        print(f"Variações inativas: {inativas}\n")
        
        if ativas == 0:
            print("⚠️  PROBLEMA: Nenhuma variação está ativa!")
            print("Solução: Ativar as variações dos produtos para que apareçam no catálogo de vendas")

