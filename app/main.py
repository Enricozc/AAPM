from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from app.routes import register_routes # Importa a função do seu __init__.py
from app.config.database import engine, Base

# Cria as tabelas no banco
Base.metadata.create_all(bind=engine)

app = FastAPI(title="Sistema AAPM")

app.mount("/static", StaticFiles(directory="app/static"), name="static")

# CHAME A FUNÇÃO ASSIM:
register_routes(app)

@app.get("/")
async def root():
    return {"message": "API rodando com sucesso!"}