# 🎓 Unificado - Rede de Conhecimento

Uma API REST moderna para gerenciamento de cursos e disciplinas com sistema de pré-requisitos, construída com **FastAPI** e **SQLAlchemy**.

## 📋 Visão Geral

O projeto **Unificado** é uma aplicação para organizar cursos e suas disciplinas, permitindo definir pré-requisitos entre disciplinas de forma inteligente. A API oferece funcionalidades para:

- ✅ **Gerenciamento de Cursos**: Criar, listar, buscar e atualizar cursos
- ✅ **Gerenciamento de Disciplinas**: CRUD completo com validação de pré-requisitos
- ✅ **Sistema de Pré-requisitos**: Relacionamento muitos-para-muitos entre disciplinas
- ✅ **Sistema de Usuários**: Autenticação e autorização (estudantes, professores, admin)
- ✅ **Validação Automática**: Detecção de dependências circulares
- ✅ **Migrations Automáticas**: Versionamento de banco via Alembic
- ✅ **API Documentada**: Swagger UI automático via FastAPI

### 🏗️ Arquitetura

```
unificado/
├── app.py          # Aplicação FastAPI com rotas
├── models.py       # Modelos SQLAlchemy (Course, Discipline)
├── schemas.py      # Esquemas Pydantic para validação
├── database.py     # Configuração do banco de dados
└── settings.py     # Configurações da aplicação
```

### 🛠️ Stack Tecnológica

- **[FastAPI](https://fastapi.tiangolo.com/)**: Framework web moderno e rápido
- **[SQLAlchemy 2.0](https://www.sqlalchemy.org/)**: ORM com suporte a relacionamentos complexos
- **[Pydantic](https://docs.pydantic.dev/)**: Validação de dados e serialização
- **[PostgreSQL](https://www.postgresql.org/)**: Banco de dados relacional
- **[Poetry](https://python-poetry.org/)**: Gerenciamento de dependências

## 🚀 Configuração do Ambiente

### 1. Instalar o pipx (Gerenciador de Aplicações Python)

```powershell
# Windows (PowerShell)
python -m pip install --user pipx
python -m pipx ensurepath

# Reiniciar o terminal após a instalação
```

### 2. Instalar o Poetry via pipx

```powershell
pipx install poetry
pipx inject poetry poetry-plugin-shell

# Verificar instalação
poetry --version
```

### 3. Configurar o Poetry (Opcional)

```powershell
# Baixar o python pelo gerenciador do poetry
poetry python install 3.13

# Criar .venv na pasta do projeto (recomendado)
poetry env use 3.13

# Verificar configuração
poetry config --list
```

## 📦 Instalação e Configuração

### 1. Clonar e Acessar o Projeto

```bash
git clone <seu-repositorio>
cd Unificado
```

### 2. Criar e Ativar Ambiente Virtual

```powershell
# Instalar dependências e criar ambiente virtual
poetry install

# Ativar o shell do Poetry
poetry shell
```

### 3. Configurar Variáveis de Ambiente

Crie um arquivo `.env` na raiz do projeto:

```env
# .env
DATABASE_URL=postgresql://usuario:senha@localhost:5432/unificado_db
DATABASE_URL_TEST=sqlite:///./test.db
ADMIN_EMAIL=admin@local
ADMIN_PASSWORD=senhaSegura123
```

**Exemplo com PostgreSQL local:**
```env
DATABASE_URL=postgresql://postgres:suasenha@localhost:5432/unificado
DATABASE_URL_TEST=sqlite:///./test.db
ADMIN_EMAIL=admin@dominio.com
ADMIN_PASSWORD=minhasenha456
```

**Para desenvolvimento com SQLite:**
```env
DATABASE_URL=sqlite:///./unificado.db
```

### 4. Configurar Banco de Dados (Migrations)

O projeto usa **Alembic** para gerenciar migrações de banco de dados. Siga os passos para criar/atualizar o esquema:

```powershell
# Verificar estado atual das migrations
alembic current

# Aplicar todas as migrations (criar/atualizar tabelas)
alembic upgrade head

# Verificar se aplicou corretamente
alembic current
```

**Para desenvolvimento com dados iniciais:**

Defina as credenciais do admin no `.env` para criar automaticamente um usuário administrador:

```env
# Adicionar ao .env
ADMIN_EMAIL=admin@local
ADMIN_PASSWORD=senhaSegura123
```

**Comandos úteis do Alembic:**

```powershell
# Ver histórico de migrations
alembic history --verbose

# Ver diferenças entre DB atual e models (para debug)
alembic current
alembic heads

# Para teste em SQLite separado
$env:DATABASE_URL_TEST = "sqlite:///./test.db"
alembic upgrade head
```

## 🏃‍♂️ Executando o Projeto

### Usando Poetry + Taskipy (Recomendado)

```powershell
# Executar servidor de desenvolvimento
poetry run task run

# Ou se já estiver no poetry shell
task run
```

### Usando FastAPI diretamente

```powershell
# Com Poetry
poetry run fastapi dev unificado/app.py --reload

# Ou no poetry shell
fastapi dev unificado/app.py --reload
```

### 🌐 Acessar a Aplicação

- **API**: http://localhost:8000
- **Documentação Interativa (Swagger)**: http://localhost:8000/docs
- **Documentação Alternativa (ReDoc)**: http://localhost:8000/redoc

## 🧪 Testes e Qualidade de Código

```powershell
# Executar todos os testes
poetry run task test

# Linting e verificação de código
poetry run task lint

# Formatação automática
poetry run task format

# Executar comandos individuais
poetry run pytest
poetry run ruff check
poetry run ruff format
```

## 📚 Uso da API

### Exemplos de Requisições

#### Criar um Curso
```bash
curl -X POST "http://localhost:8000/courses/" \
     -H "Content-Type: application/json" \
     -d '{"name": "Ciência da Computação"}'
```

#### Criar uma Disciplina
```bash
curl -X POST "http://localhost:8000/disciplines/" \
     -H "Content-Type: application/json" \
     -d '{
       "name": "Algoritmos e Estruturas de Dados",
       "course_id": 1,
       "prerequisites": [2, 3]
     }'
```

#### Listar Disciplinas com Pré-requisitos
```bash
curl "http://localhost:8000/disciplines/"
```

### Estrutura de Dados

**Course (Curso)**
```json
{
  "id": 1,
  "name": "Ciência da Computação"
}
```

**Discipline (Disciplina)**
```json
{
  "id": 1,
  "name": "Algoritmos e Estruturas de Dados",
  "course_id": 1,
  "prerequisites": [2, 3],
  "warnings": []
}
```

## 🔧 Comandos Úteis do Poetry

```powershell
# Adicionar nova dependência
poetry add fastapi

# Adicionar dependência de desenvolvimento
poetry add --group dev pytest

# Atualizar dependências
poetry update

# Mostrar dependências
poetry show

# Sair do shell do poetry
exit
```

## 📁 Estrutura Completa do Projeto

```
Unificado/
├── README.md                 # Este arquivo
├── pyproject.toml           # Configurações Poetry + ferramentas
├── poetry.lock              # Lock das versões das dependências
├── alembic.ini              # Configuração do Alembic
├── .env                     # Variáveis de ambiente (criar)
├── exemplo_uso.py           # Exemplo de uso dos models
├── migrations/              # Migrações do banco de dados
│   ├── env.py              # Configuração do Alembic
│   └── versions/           # Arquivos de migração
│       ├── 339dbadfaddc_create_discipline_and_courses_tables.py
│       └── 0001_create_users_and_profiles_and_admin.py
├── tests/                   # Testes automatizados
│   └── __init__.py
└── unificado/              # Código principal
    ├── __init__.py
    ├── app.py              # FastAPI app + rotas
    ├── models.py           # Modelos SQLAlchemy
    ├── schemas.py          # Esquemas Pydantic
    ├── database.py         # Configuração do DB
    ├── security.py         # Funções de segurança/hash
    └── settings.py         # Settings da aplicação
```

## 🗃️ Gerenciamento do Banco de Dados

### Migrations com Alembic

O projeto utiliza **Alembic** para versionamento do esquema do banco. As migrations são aplicadas automaticamente na ordem correta:

1. **339dbadfaddc** - Cria tabelas `courses`, `disciplines` e `discipline_prerequisites`
2. **0001** - Cria tabelas `users`, `student_profiles`, `teacher_profiles` + usuário admin

### Comandos de Desenvolvimento

```powershell
# Resetar banco para estado inicial (cuidado: remove dados!)
alembic downgrade base

# Aplicar migrations uma por uma (para debug)
alembic upgrade 339dbadfaddc
alembic upgrade 0001

# Ver SQL que será executado (sem aplicar)
alembic upgrade head --sql

# Marcar banco como atualizado sem executar (se criou tabelas manualmente)
alembic stamp head
```

### Estrutura das Tabelas

Após aplicar as migrations, o banco terá:

- **courses**: Cursos disponíveis
- **disciplines**: Disciplinas de cada curso  
- **discipline_prerequisites**: Relacionamento de pré-requisitos
- **users**: Usuários do sistema (estudantes, professores, admin)
- **student_profiles**: Perfis específicos de estudantes
- **teacher_profiles**: Perfis específicos de professores

### Usuário Admin Padrão

A migration `0001` cria automaticamente um usuário administrador se `ADMIN_PASSWORD` estiver definido no `.env`:

```env
ADMIN_EMAIL=admin@dominio.com
ADMIN_PASSWORD=suaSenhaSegura
```

**Credenciais padrão:**
- Username: `admin`
- Role: `admin`
- Email e senha: conforme definido no `.env`

## 🤝 Contribuindo

1. Fork o projeto
2. Crie uma branch para sua feature (`git checkout -b feature/nova-feature`)
3. Commit suas mudanças (`git commit -am 'Adiciona nova feature'`)
4. Push para a branch (`git push origin feature/nova-feature`)
5. Abra um Pull Request

## 📝 Licença

Este projeto está sob a licença MIT. Veja o arquivo `LICENSE` para mais detalhes.

## 👨‍💻 Autor

**Gabriel Ramon** - [garamon97@gmail.com](mailto:garamon97@gmail.com)

---

⭐ Se este projeto foi útil, considere dar uma estrela no repositório!
