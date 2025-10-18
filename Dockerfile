FROM python:3.13-slim

SHELL ["/bin/bash", "-euo", "pipefail", "-c"]

# Não gerar arquivos .pyc e forçar buffer de logs
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

WORKDIR /app

# Instalar dependências do sistema necessárias para compilação e psycopg2
ENV BUILD_LOG_DIR=/var/log/docker-build
COPY scripts/run-build-step.sh /usr/local/bin/run-build-step.sh
RUN chmod +x /usr/local/bin/run-build-step.sh
RUN run-build-step.sh "system-deps" "apt-get update && apt-get install -y --no-install-recommends gcc libpq-dev build-essential"
RUN run-build-step.sh "apt-clean" "rm -rf /var/lib/apt/lists/*"

# Copiar metadados do projeto primeiro (cache do Docker)
COPY pyproject.toml ./
# Poetry espera encontrar os metadados do projeto (ex: README). Copiamos README para
# permitir que o projeto seja instalado durante `poetry install`
COPY README.md ./

# Copiar arquivos essenciais para Alembic (migrations)
COPY alembic.ini ./
COPY migrations/ migrations/

# Copiar o pacote (código fonte)
COPY unificado/ unificado/

# Copiar entrypoint que aplica migrations automaticamente quando configurado
COPY docker-entrypoint.sh ./
RUN chmod +x docker-entrypoint.sh

# Atualizar pip e instalar Poetry; usar Poetry para instalar dependências do projeto
RUN run-build-step.sh "poetry-install" "python -m pip install --upgrade pip setuptools wheel && python -m pip install --no-cache-dir poetry && poetry config virtualenvs.create false && poetry install --no-interaction --only main"

# Expor porta (a App Runner permite configurar qual porta o container escuta)
EXPOSE 8000

# Usamos um entrypoint que pode aplicar migrations automaticamente antes de iniciar
ENTRYPOINT ["./docker-entrypoint.sh"]
# Comando padrão para iniciar a aplicação
CMD ["uvicorn", "unificado.app:app", "--host", "0.0.0.0", "--port", "8000", "--log-level", "debug"]
