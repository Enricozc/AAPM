from sqlalchemy import Column, Integer, String, Float, Boolean, ForeignKey
from sqlalchemy.orm import relationship
from app.config.database import Base


class Produto(Base):
    __tablename__ = "produtos"

    id           = Column(Integer, primary_key=True, autoincrement=True, index=True)
    nome         = Column(String(150), nullable=False, index=True)
    preco        = Column(Float, nullable=False, default=0.0)
    ativo        = Column(Boolean, default=True)
    imagem_path  = Column(String(255), nullable=True)

    categoria_id = Column(Integer, ForeignKey("categorias.id", ondelete="SET NULL"), nullable=True)
    categoria    = relationship("Categoria", back_populates="produtos")

    variacoes    = relationship("ProdutoVariacao", back_populates="produto", cascade="all, delete-orphan")

    @property
    def estoque_total(self):
        return sum(v.estoque_atual for v in self.variacoes if v.ativo)

    @property
    def imagem_url(self):
        if self.imagem_path:
            return f"/static/{self.imagem_path}"
        return None