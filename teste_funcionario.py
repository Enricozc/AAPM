from app.config.database import SessionLocal
from app.models.user_model import Usuario
from app.config.security import hash_password

def criar_usuario_comum():
    db = SessionLocal()
    
    # 🔍 Verifica se o e-mail de teste já existe para não duplicar
    existe = db.query(Usuario).filter(Usuario.email == "comum@aapm.com").first()
    if existe:
        print("ℹ️ O usuário comum@aapm.com já existe no banco.")
        db.close()
        return

    # 🛠️ Criando apenas com as colunas padrão confirmadas no seu controller
    usuario_comum = Usuario(
        nome="João Caixa",
        email="comum@aapm.com",
        hashed_password=hash_password("123456"),
        role="FUNCIONARIO"  # Garante o nível comum para testar o bloqueio
    )
    
    try:
        db.add(usuario_comum)
        db.commit()
        print("✅ Usuário comum (FUNCIONARIO) criado com sucesso!")
        print("📧 E-mail: comum@aapm.com | 🔑 Senha: 123456")
    except Exception as e:
        db.rollback()
        print(print(f"❌ Erro ao salvar no banco: {e}"))
    finally:
        db.close()

if __name__ == "__main__":
    criar_usuario_comum()