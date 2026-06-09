from sqlalchemy import Column, Integer, Float, DateTime, String
from datetime import datetime
from app.config.database import Base

class Fechamento(Base):
    __tablename__ = "fechamentos"

    id              = Column(Integer, primary_key=True, index=True)
    data_fechamento = Column(DateTime, default=datetime.utcnow)
    total_vendas    = Column(Integer, nullable=False, default=0)
    receita_total   = Column(Float, nullable=False, default=0.0)
    receita_pix     = Column(Float, nullable=False, default=0.0)
    receita_cartao  = Column(Float, nullable=False, default=0.0)
    receita_dinheiro= Column(Float, nullable=False, default=0.0)
    observacao      = Column(String(500), nullable=True)
    usuario         = Column(String(150), nullable=True)