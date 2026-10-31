from sqlalchemy import Column, Integer, Float, DateTime, String, ForeignKey
from sqlalchemy.orm import relationship
from datetime import datetime
from app.config.database import Base

class Venda(Base):
    __tablename__ = "vendas"

    id              = Column(Integer, primary_key=True, index=True)
    responsavel     = Column(String(150), nullable=False)
    valor_subtotal  = Column(Float, nullable=False, default=0.0)
    desconto        = Column(Float, nullable=False, default=0.0)
    valor_total     = Column(Float, nullable=False)
    forma_pagamento = Column(String(50), nullable=False)
    valor_pagamento_1 = Column(Float, nullable=True)
    forma_pagamento_2 = Column(String(50), nullable=True)
    valor_pagamento_2 = Column(Float, nullable=True)
    observacao      = Column(String(500), nullable=True)
    status          = Column(String(30), default="concluida")
    data_venda      = Column(DateTime, default=datetime.utcnow)

    itens = relationship("VendaItem", back_populates="venda", cascade="all, delete")