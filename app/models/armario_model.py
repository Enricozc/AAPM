from sqlalchemy import Column, Integer, String, Boolean, DateTime, ForeignKey
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.config.database import Base

class Armario(Base):
    __tablename__ = "armarios"
    id           = Column(Integer, primary_key=True, autoincrement=True, index=True)
    numero       = Column(String(20), nullable=False, unique=True, index=True)
    localizacao  = Column(String(100), nullable=True)
    ocupado      = Column(Boolean, default=False)
    ativo        = Column(Boolean, default=True)
    usuario_id   = Column(Integer, ForeignKey("usuarios.id", ondelete="SET NULL"), nullable=True)
    usuario      = relationship("Usuario", foreign_keys=[usuario_id])
    atribuido_em = Column(DateTime, nullable=True)
    criado_em    = Column(DateTime, server_default=func.now())
    historico    = relationship("ArmarioHistorico", back_populates="armario", cascade="all, delete-orphan")

class ArmarioHistorico(Base):
    __tablename__ = "armario_historico"
    id           = Column(Integer, primary_key=True, autoincrement=True)
    armario_id   = Column(Integer, ForeignKey("armarios.id", ondelete="CASCADE"), nullable=False)
    usuario_id   = Column(Integer, ForeignKey("usuarios.id", ondelete="SET NULL"), nullable=True)
    usuario_nome = Column(String(100), nullable=True)
    acao         = Column(String(20), nullable=False)
    feito_em     = Column(DateTime, server_default=func.now())
    armario      = relationship("Armario", back_populates="historico")
    usuario      = relationship("Usuario", foreign_keys=[usuario_id])