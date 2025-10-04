# Template Backend FastAPI + Postgres

Este repositório é um template de backend utilizando FastAPI integrado ao PostgreSQL
O objetivo é fornecer uma estrutura base pronta para uso, acelerando o desenvolvimento de novas APIs.

O gerenciamento de dependências e ambientes é feito com Poetry, e o projeto suporta execução local ou totalmente conteinerizada via Docker.

## Dependências

Para rodar o projeto, você precisará das seguintes dependências instaladas:

- **Python**: Versão 3.12 ou superior
- **Poetry**: Gerenciador de pacotes e ambientes virtuais
- **Docker**: Plataforma para conteinerizar e isolar a aplicação e seus serviços

Caso não tenha o Poetry instalado:

 ```bash
 pipx install poetry
 pipx inject poetry poetry-plugin-shell
 ```

## Estrutura do Projeto

Abaixo está a organização das pastas e arquivos, juntamente com a explicação de suas responsabilidades:

```
.
├── migrations/               
├── src/                      
│   ├── background/           
│   ├── core/                 
│   ├── database/             
│   ├── routes/               
│   ├── utils/                
│   ├── app.py                
│   └── container.py          
├── test/                                   
```

### Descrição das pastas principais

- **`migrations/`**  
  Contém os arquivos gerados pelo alembic, responsáveis por versionar alterações no banco de dados (migrações).  
  Cada alteração na estrutura dos modelos deve gerar uma nova versão aqui.

- **`src/`**  
  Diretório principal do código-fonte da aplicação. É onde estão os módulos da API.

  - **`background/`**  
    Implementa tarefas assíncronas e agendamentos de processos em background, utilizando APScheduler.

  - **`core/`**  
    Camada de “núcleo” que agrupa:
    - **`schemas/`**: define os *schemas* com pydantic, usados para validação de entrada e saída de dados.  
    - **`services/`**: contém as regras de negócio da aplicação, separando a lógica do acesso ao banco e das rotas.

  - **`database/`**  
    Gerencia a persistência dos dados.  
    - **`models/`**: define os modelos das tabelas do banco com SQLAlchemy.  
    - **`repositories/`**: responsável pelas consultas e interações com o banco.  
    - **`query.py`**:

  - **`routes/`**  
    Define os endpoints da API.

  - **`utils/`**  
    Funções e utilitários de uso geral

  - **`app.py`**  
    Ponto de entrada do FastAPI. Aqui é configurada a aplicação, middlewares, rotas e eventos.

  - **`container.py`**  
    Gerencia injeção de dependências, facilitando a comunicação entre serviços, repositórios e rotas.

- **`test/`**  
  Estrutura organizada para testes unitários e de integração:
  - **`fixtures/`** → criação de dados e contexto para testes.  
  - **`mocks/`** → simulações de objetos/serviços para isolar dependências.  
  - **`repositories/`**, **`services/`**, **`routes/`** → testes específicos para cada camada.  
  - **`utils/`** → utilitários de suporte para os testes (ex.: contexto da aplicação, criação de modelos de teste).


---

## Tecnologias Utilizadas

Este template utiliza o seguinte conjunto de tecnologias:

- FastAPI → Framework moderno e rápido para criação de APIs REST.  
- Poetry → Gerenciador de dependências e build system para Python.
- SQLAlchemy (asyncio) → ORM para acesso assíncrono ao banco de dados.  
- Alembic → Controle de versões e migrações do banco.  
- Pydantic / Pydantic Settings → Validação de dados e gerenciamento de configurações via `.env`.  
- PostgreSQL → Banco de dados relacional.  
- Uvicorn → Servidor ASGI de alta performance.  
- APScheduler → Agendamento de tarefas e jobs em background.  

---


## Como executar

1. **Clone o repositório:**

   ```bash
   git clone <url-do-repositorio>
   cd rm-backend
   ```

2. **Defina as variáveis de ambiente**
   
   As configurações do aplicativo são definidas por variáveis de ambiente. Para definir as configurações, faça uma cópia do arquivo `.env.example`, nomeando-o como `.env`. Em seguida, abra e edite as configurações conforme necessário. As seguintes variáveis de ambiente estão disponíveis:

| VARIÁVEL | DESCRIÇÃO  | VALOR |
|-----|-----|-----| 
| `DATABASE_URL` | URL de conexão com o postgres | `postgresql+asyncpg://postgres:postgres@localhost:5432/template_db` |

4. **Suba o banco de dados através de container docker**

   O projeto já possui um `docker-compose.yml` configurado.

   ```bash
   docker compose up -d --build postgres
   ```

6. **Instale as dependências do projeto:**

   ```bash
   poetry install
   ```

7. **Ative o ambiente virtual:**

   ```bash
   poetry shell
   ```

8. **Inicie o servidor local:**

   ```bash
   task run
   ```

A api estará disponível em: [http://localhost:8000](http://localhost:8000)

---

## 🐳 Como executar com Docker

Você pode rodar toda a aplicação usando apenas Docker, incluindo o backend e o banco de dados.

1. **Clone o repositório:**

   ```bash
   git clone <url-do-repositorio>
   cd rm-backend
   ```

2. **Preencha o arquivo `.env` com as variáveis de ambiente.**


3. **Suba os containers da aplicação e do postgres:**

   ```bash
   docker compose up -d --build
   ```

  A api estará disponível em: [http://localhost:8000](http://localhost:8000)

## Migrações com Alembic

As migrações permitem versionar alterações na estrutura do banco de dados.  
No projeto, o Alembic já está configurado.

### Criar uma nova migração
Sempre que você modificar ou adicionar modelos em `src/database/models/`, crie uma nova migração com:

```bash
alembic revision --autogenerate -m "descrição_da_mudança"
```

Isso vai gerar um arquivo dentro da pasta `migrations/versions/`.

### Aplicar as migrações no banco
Para atualizar o banco de dados com as alterações pendentes:

```bash
alembic upgrade head
```

### Voltar uma migração (rollback)
Se for necessário desfazer a última migração:

```bash
alembic downgrade -1
```

---

## Testes, Lint e Formatação

O template utiliza o pytest como framework de testes, além de ferramentas de lint e formatação via ruff.

Para rodar os comandos abaixo, certifique-se de estar com o ambiente virtual ativado:  
```bash
poetry shell
```

### Comandos

Execução dos Testes
```bash
task test
```

Análise de código e estilo (Lint)
```bash
task lint
```

Formatação automática de código
```bash
task format
```
---

