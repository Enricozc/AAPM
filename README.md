# AAPM

Enrico Candido - (LIDER) RESPONSAVEL POR BACK-END E PRODUCT MASTER

Izabelly Esteves- RESPONSAVEL POR FRONT-END, E PRODUCT OWNER 

Eduardo Furtado - RESPONSAVEL POR FRONT-END

Cauã Theodoro - RESPONSAVEL POR BACK- END



# Instalar o requirements.txt

pip install -r requirements.txt
pip install jwt
python -m pip install pydantic-settings

# Instalar esses dois juntos 
python -m pip uninstall bcrypt -y
python -m pip install bcrypt==4.3.0

#Inicializar o alembic
python -m alembic init migrations

# Gerar a migration
python -m alembic revision --autogenerate -m "Criar tabela usuario"


# Aplicar a migration
python -m alembic upgrade head


#Rodar o código
python -m uvicorn main:app --reload