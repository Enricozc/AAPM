from sqlalchemy import Column, Integer, Float, ForeignKey
from sqlalchemy.orm import relationship
from app.config.database import Base

class VendaItem(Base):
    __tablename__ = "venda_itens"

    id             = Column(Integer, primary_key=True, index=True)
    venda_id       = Column(Integer, ForeignKey("vendas.id", ondelete="CASCADE"), nullable=False)
    produto_id     = Column(Integer, ForeignKey("produtos.id", ondelete="SET NULL"), nullable=True)
    quantidade     = Column(Integer, nullable=False)
    preco_unitario = Column(Float, nullable=False)
    valor_total    = Column(Float, nullable=False)

    venda   = relationship("Venda", back_populates="itens")
    produto = relationship("Produto")
    