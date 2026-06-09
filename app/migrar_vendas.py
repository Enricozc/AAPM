import sqlite3

conn = sqlite3.connect("aapm.db")
cursor = conn.cursor()

try:
    cursor.execute("ALTER TABLE vendas ADD COLUMN responsavel VARCHAR")
    conn.commit()
    print("✓ Coluna 'responsavel' adicionada com sucesso!")
except Exception as e:
    if "duplicate column" in str(e).lower():
        print("⚠ Coluna já existe, nada a fazer.")
    else:
        print(f"Erro: {e}")
finally:
    conn.close()