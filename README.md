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




## Troubleshooting: `AttributeError: module 'jwt' has no attribute 'encode'`

### Sintoma
Ao fazer login (`POST /auth/login`), a API retorna erro 500 com o seguinte traceback:

```
File "app/config/security.py", line 83, in create_access_token
    encoded_jwt = jwt.encode(
                  ^^^^^^^^^^
AttributeError: module 'jwt' has no attribute 'encode'
```

### Causa
Existem dois pacotes distintos no PyPI que se instalam sob o mesmo nome de módulo `jwt`:

- **`PyJWT`** → pacote correto, possui o método `.encode()` usado no projeto.
- **`jwt`** → pacote diferente (não é o que o projeto usa), não possui `.encode()`.

Como os dois usam a mesma pasta (`site-packages/jwt/`), instalar um por cima do outro pode deixar o ambiente com a versão errada, ou o servidor pode estar rodando em um Python/venv diferente do que foi usado para reinstalar o pacote.

### Solução

1. Desinstalar o pacote errado:
   ```
   pip uninstall jwt -y
   ```

2. Reinstalar o pacote correto, forçando a reinstalação:
   ```
   pip install PyJWT --upgrade --force-reinstall
   ```

3. Confirmar que a instalação está correta:
   ```
   python -c "import jwt; print(jwt.__version__)"
   python -c "import jwt; print(jwt.encode)"
   ```
   O segundo comando deve retornar algo como:
   ```
   <bound method PyJWT.encode of <jwt.api_jwt.PyJWT object at 0x...>>
   ```

4. **Importante:** garantir que o servidor (`uvicorn`) está rodando com o **mesmo Python/ambiente virtual** onde o PyJWT foi reinstalado. Se o projeto usa um `venv`, ativá-lo antes de instalar e antes de rodar o servidor:
   ```
   .venv\Scripts\activate
   pip install PyJWT --upgrade --force-reinstall
   uvicorn app.main:app --reload
   ```

5. Conferir no `requirements.txt` (ou `pyproject.toml`) se a dependência está listada como `PyJWT` (não `jwt`), para evitar que o problema volte a acontecer em outra máquina ou no deploy:
   ```
   PyJWT==2.13.0
   ```

### Verificação de qual Python está sendo usado
Caso o erro persista mesmo após reinstalar, verificar se o terminal está apontando para o Python certo:
```
where python
```
Comparar esse caminho com o Python usado dentro do ambiente virtual do projeto.