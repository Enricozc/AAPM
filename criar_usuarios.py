# ⚙️ AJUSTADO: Importações corrigidas para os caminhos reais do seu projeto
from app.config.database import SessionLocal 
from app.models.user_model import Usuario     
from app.config.security import hash_password 

# ✅ CORRIGIDO: Gabriel inserido corretamente dentro da lista de USUARIOS
# ✅ CORRIGIDO: Roles mudados para 'ADMIN' (maiúsculo) para bater com seu dashboard.html
USUARIOS = [
    {
        "nome": "Admin",
        "email": "adimin@teste.com",
        "senha": "admin123",
        "role": "ADMIN",
    },
    {
        "nome": "Gabriel",
        "email": "adimingabriel@teste.com",
        "senha": "admin123",
        "role": "ADMIN",
    },
]

def criar_usuarios():
    db = SessionLocal() # Usando o seu banco
    try:
        for user in USUARIOS:
            # Verifica se o e-mail já existe para não quebrar o banco
            existente = db.query(Usuario).filter_by(email=user["email"]).first()
            if existente:
                print(f"Esse e-mail {user['email']} já está cadastrado no db")
                continue
            else:
                # ⚙️ AJUSTADO: senha_hash mudado para hashed_password (o nome real da sua coluna)
                novo_usuario = Usuario(
                    nome=user["nome"],
                    email=user["email"],
                    hashed_password=hash_password(user["senha"]), 
                    role=user["role"],
                    ativo=True
                )
                db.add(novo_usuario)
                print(f"Usuario cadastrado com sucesso: {user['nome']}")
        db.commit()

    except Exception as erro:
        db.rollback()
        print(f"Erro detectado: {erro}")
    finally:
        db.close()

if __name__ == "__main__":
    criar_usuarios()