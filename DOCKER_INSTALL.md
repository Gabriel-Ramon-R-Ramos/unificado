Como construir e distribuir a imagem Docker (README de instalação)

Este arquivo descreve como qualquer pessoa pode construir a imagem (a partir do `Dockerfile`) e executar localmente com Docker ou Docker Compose. Também explica como usar a variável `RUN_MIGRATIONS` para aplicar migrations automaticamente.

1) Build da imagem local

Windows (PowerShell):

```powershell
cd C:\Users\garam\.projetos\unificado
# Build da imagem
docker build -t unificado:latest .
```

2) Rodar a imagem isolada (sem Compose)

- Rodar sem executar migrations (útil quando já aplicou migrations via Compose):

```powershell
docker run --rm -p 8000:8000 \
  --env-file ".env" \
  -e RUN_MIGRATIONS=false \
  unificado:latest
```

- Rodar e executar migrations automaticamente antes de iniciar (o entrypoint fará retry esperando o banco):

```powershell
# Se o DATABASE_URL aponta para um Postgres remoto/serviço acessível
docker run --rm -p 8000:8000 \
  --env-file ".env" \
  -e RUN_MIGRATIONS=true \
  unificado:latest
```

3) Usando Docker Compose (recomendado para desenvolvimento local)

- Subir DB + web:

```powershell
# Build e subir
docker-compose up --build
```

- Rodar migrations via serviço migrations (one-shot):

```powershell
docker-compose run --rm migrations
```

- Rodar web e permitir que o entrypoint aplique automaticamente as migrations (se preferir):

```powershell
# no docker-compose.yml, defina environment: RUN_MIGRATIONS=true no serviço web
# ou passe como variável de ambiente antes do docker-compose up
$env:RUN_MIGRATIONS = "true"
docker-compose up --build
```

4) Publicar no Docker Hub / Registry

- Tag e push para um registry público/privado:

```powershell
# taguear
docker tag unificado:latest <your-registry>/unificado:latest
# push
docker push <your-registry>/unificado:latest
```

Observações
- O entrypoint (`docker-entrypoint.sh`) espera que o comando `alembic` esteja disponível na imagem — isso depende de `alembic` estar nas dependências (seu `pyproject.toml` já lista alembic). 
- Se preferir não rodar migrations automaticamente, mantenha `RUN_MIGRATIONS=false` (padrão).
- Não comite arquivos sensíveis (`.env`) em repositórios públicos. Use secrets no ambiente de produção.
