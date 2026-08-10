# AAPM

Enrico Candido - (LIDER) RESPONSAVEL POR BACK-END E PRODUCT MASTER

Izabelly Esteves- RESPONSAVEL POR FRONT-END, E PRODUCT OWNER 

Eduardo Furtado - RESPONSAVEL POR FRONT-END

Cauã Theodoro - RESPONSAVEL POR BACK- END



# Instalar o requirements.txt

python -m pip install fastapi uvicorn sqlalchemy alembic pydantic pydantic-settings PyJWT passlib bcrypt jinja2 python-multipart


#Inicializar o alembic
python -m alembic init migrations

# Gerar a migration
python -m alembic revision --autogenerate -m "Criar tabela usuario"


# Aplicar a migration
python -m alembic upgrade head


#Rodar o código
python -m uvicorn app.main:app --reload