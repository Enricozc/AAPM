from sqlalchemy import Column, Integer, Float, DateTime
from datetime import datetime
from app.config.database import Base

class Venda(Base):
    __tablename__ = "vendas"

    id = Column(Integer, primary_key=True, index=True)
    valor_total = Column(Float, nullable=False)
    data_venda = Column(DateTime, default=datetime.utcnow)