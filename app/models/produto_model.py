from sqlalchemy import Column, Integer, String, Float, Boolean, ForeignKey
from sqlalchemy.orm import relationship
from app.config.database import Base

class Produto(Base):
    __tablename__ = "produtos"

    id = Column(Integer, primary_key=True, autoincrement=True, index=True)
    nome = Column(String(150), nullable=False, index=True)
    preco = Column(Float, nullable=False, default=0.0)
    estoque_atual = Column(Integer, nullable=False, default=0)
    ativo = Column(Boolean, default=True)

    # Caminho do arquivo salvo no servidor
    imagem_path = Column(String(255), nullable=True)

    # Relacionamento com Categoria
    categoria_id = Column(Integer, ForeignKey("categorias.id", ondelete="SET NULL"), nullable=True)
    categoria = relationship("Categoria", back_populates="produtos")

    @property
    def imagem_url(self):
        """Retorna o caminho completo para o template ou o placeholder padrão."""
        if self.imagem_path:
            # Garante que o caminho seja tratado como um arquivo estático
            return f"/static/{self.imagem_path}"
        return "/static/img/produto-placeholder.png"