from sqlalchemy import Column, Integer, String, DateTime, ForeignKey
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.config.database import Base

class Log(Base):
    __tablename__ = "logs"
    id         = Column(Integer, primary_key=True, autoincrement=True)
    acao       = Column(String(100), nullable=False)
    descricao  = Column(String(255), nullable=True)
    tipo       = Column(String(20), nullable=False, default="info")  # info | sucesso | alerta
    usuario_id = Column(Integer, ForeignKey("usuarios.id", ondelete="SET NULL"), nullable=True)
    feito_em   = Column(DateTime, server_default=func.now())
    usuario    = relationship("Usuario", foreign_keys=[usuario_id])