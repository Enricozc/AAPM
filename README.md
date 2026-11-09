# AAPM - Sistema de Gestão Escolar e PDV

## 1. Visão geral

O projeto AAPM é um sistema de gestão para a escola, com módulos de:
- autenticação e usuários
- categorias e produtos
- controle de estoque
- armários e alunos
- dashboard e fechamento de caixa
- ponto de venda (PDV)

O objetivo principal deste trabalho foi evoluir o módulo de vendas para atender ao fluxo real do ponto de venda, incluindo múltiplas formas de pagamento e descontos manuais, além de validar a estabilidade do backend com testes de regressão.

## 2. Equipe

- Enrico Candido — Líder / Back-end
- Izabelly Esteves — Front-end / Product Owner
- Eduardo Furtado — Front-end
- Cauã Theodoro — Back-end

## 3. Funcionalidades implementadas

### PDV
- venda com duas formas de pagamento na mesma transação
- desconto manual em valor ou percentual
- validação do subtotal e total final
- controle de estoque ao registrar venda
- registro de vendas e histórico de pagamentos

### Gestão
- cadastro e controle de usuários
- cadastro de categorias e produtos
- gestão de variações de produto
- controle de armários e associação de alunos
- fechamento do dia com resumo financeiro
- dashboard com indicadores de vendas e receitas

### Segurança
- login e autenticação por token
- recuperação de senha
- controle de acesso por perfil de usuário

## 4. Requisitos

Python 3.10+

Instale as dependências:

```powershell
python -m pip install -r requirements.txt
python -m pip install -r requirements-test.txt
```

Se necessário, também pode instalar a versão correta do PyJWT:

```powershell
python -m pip uninstall jwt -y
python -m pip install PyJWT --upgrade --force-reinstall
```

## 5. Execução do projeto

Para iniciar a aplicação:

```powershell
python -m uvicorn main:app --reload
```

A aplicação ficará disponível em:
- http://127.0.0.1:8000

## 6. Banco de dados e migrations

Para aplicar as migrations do projeto:

```powershell
python -m alembic upgrade head
```

Se for necessário gerar uma nova migration:

```powershell
python -m alembic revision --autogenerate -m "Descrição da alteração"
```

## 7. Testes de regressão

O projeto possui testes automatizados com pytest para validar o funcionamento de rotas e fluxos principais do sistema.

Para executar a suíte completa:

```powershell
python -m pytest -q
```

Para executar apenas os testes de vendas:

```powershell
python -m pytest -q tests/test_vendas.py
```

Para executar a pasta de testes:

```powershell
python -m pytest -q tests
```

## 8. Casos de validação do PDV

Os principais cenários validados incluem:
- venda com pagamento dividido em duas formas
- desconto inválido acima do subtotal
- desconto percentual acima de 100%
- pagamento sem fechar o total
- estoque insuficiente
- exclusão de venda
- rotas e fluxos principais do backend

## 9. Resultado da validação

A suíte de testes foi executada com sucesso e o projeto passou na validação atual:

```powershell
python -m pytest -q
```

Resultado esperado:
- todos os testes aprovados
- sem falhas funcionais no fluxo principal

## 10. Observação final

Este projeto integra gestão escolar e operação de ponto de venda, com foco em funcionalidade, validação de regras de negócio e segurança da aplicação. Aumentamos a confiabilidade do sistema com testes automatizados e reforçamos o fluxo de vendas com funcionalidades que atendem ao uso real do PDV.

# Instalar o requirements.txt

pip install -r requirements.txt
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

## Cadastro de alunos nos armários

Na tela **Armários**, cadastre alunos e associe cada aluno a um armário. Esse
cadastro é independente das contas de acesso: não cria login, usuário ou
permissão para o aluno. Informe nome e RA único; turma/curso é opcional. O RA
ajuda a diferenciar alunos com nomes iguais e pode ser pesquisado na tela.
Cadastros antigos sem RA continuam preservados, mas pedem um RA ao serem
editados. Para remover um aluno, libere primeiro o armário associado.

Antes de iniciar uma base existente com esta versão, aplique a migration:

```powershell
python -m alembic upgrade head
```

Esta migration libera as atribuições antigas a contas do sistema. Os armários
permanecem cadastrados, mas precisarão ser associados novamente aos alunos.
As migrations seguintes adicionam RA e turma/curso, preservando os alunos e o
histórico já cadastrados.


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

## Testes de regressão

Instale as dependências de teste e execute a suíte:

```powershell
python -m pip install -r requirements-test.txt
python -m pytest
```

Os testes usam um banco SQLite temporário separado do banco da aplicação. Antes
de usar o PDV com a estrutura atualizada, aplique as migrations:

```powershell
python -m alembic upgrade head
```