from sqlalchemy.orm import Session
from app.models.log_model import Log

def registrar_log(db: Session, acao: str, descricao: str = "", tipo: str = "info", usuario_id: int = None):
    db.add(Log(acao=acao, descricao=descricao, tipo=tipo, usuario_id=usuario_id))
    db.commit()

def ultimos_logs(db: Session, limite: int = 6):
    return db.query(Log).order_by(Log.feito_em.desc()).limit(limite).all()