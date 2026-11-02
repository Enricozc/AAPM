from sqlalchemy import Column, Integer, String, Boolean, DateTime, ForeignKey
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.config.database import Base


class Aluno(Base):
    __tablename__ = "alunos"

    id = Column(Integer, primary_key=True, autoincrement=True)
    nome = Column(String(100), nullable=False, index=True)
    ra = Column(String(30), nullable=True, unique=True, index=True)
    turma_curso = Column(String(100), nullable=True)
    criado_em = Column(DateTime, server_default=func.now())
    armario = relationship("Armario", back_populates="aluno", uselist=False)


class Armario(Base):
    __tablename__ = "armarios"
    id           = Column(Integer, primary_key=True, autoincrement=True, index=True)
    numero       = Column(String(20), nullable=False, unique=True, index=True)
    localizacao  = Column(String(100), nullable=True)
    ocupado      = Column(Boolean, default=False)
    ativo        = Column(Boolean, default=True)
    aluno_id     = Column(
        Integer,
        ForeignKey(
            "alunos.id",
            name="fk_armarios_aluno_id_alunos",
            ondelete="SET NULL",
        ),
        nullable=True,
        unique=True,
    )
    aluno        = relationship("Aluno", back_populates="armario", uselist=False)
    atribuido_em = Column(DateTime, nullable=True)
    criado_em    = Column(DateTime, server_default=func.now())
    historico    = relationship("ArmarioHistorico", back_populates="armario", cascade="all, delete-orphan")

class ArmarioHistorico(Base):
    __tablename__ = "armario_historico"
    id           = Column(Integer, primary_key=True, autoincrement=True)
    armario_id   = Column(Integer, ForeignKey("armarios.id", ondelete="CASCADE"), nullable=False)
    usuario_id   = Column(Integer, ForeignKey("usuarios.id", ondelete="SET NULL"), nullable=True)
    usuario_nome = Column(String(100), nullable=True)
    aluno_ra     = Column(String(30), nullable=True)
    aluno_turma_curso = Column(String(100), nullable=True)
    acao         = Column(String(20), nullable=False)
    feito_em     = Column(DateTime, server_default=func.now())
    armario      = relationship("Armario", back_populates="historico")
    usuario      = relationship("Usuario", foreign_keys=[usuario_id])