from sqlalchemy import Column, Integer, String, Boolean
from sqlalchemy.orm import relationship
from app.config.database import Base

class Categoria(Base):
    __tablename__ = "categorias"

    id = Column(Integer, primary_key=True, autoincrement=True, index=True)
    nome = Column(String(100), nullable=False, unique=True, index=True) # Adicionado index=True para busca rápida
    ativo = Column(Boolean, default=True)

    # Relacionamento com Produto
    # O lazy="select" é o padrão, mas deixá-lo explícito ajuda na legibilidade
    produtos = relationship(
        "Produto", 
        back_populates="categoria", 
        cascade="all, delete-orphan", # Garante que se a categoria for deletada, a integridade é mantida
        lazy="select"
    )