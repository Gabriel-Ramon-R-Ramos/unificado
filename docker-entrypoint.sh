#!/usr/bin/env bash
set -e

# Entry-point que opcionalmente roda alembic antes de iniciar a aplicação
# Controle via variável de ambiente RUN_MIGRATIONS ("true" para rodar)

if [ "${RUN_MIGRATIONS:-false}" = "true" ]; then
  echo "RUN_MIGRATIONS=true -> executando alembic upgrade head"
  # espera o banco estar disponível (simples loop com timeout)
  MAX_RETRIES=30
  RETRY=0
  until alembic current >/dev/null 2>&1; do
    RETRY=$((RETRY+1))
    if [ "$RETRY" -ge "$MAX_RETRIES" ]; then
      echo "Timeout esperando alembic. Saindo."
      exit 1
    fi
    echo "Aguardando banco... (tentativa $RETRY/$MAX_RETRIES)"
    sleep 2
  done
  alembic upgrade head
else
  echo "RUN_MIGRATIONS!=true -> pulando alembic"
fi

# Se o primeiro arg começa com '-', adiciona o CMD padrão
if [ "${1#-}" != "$1" ]; then
  set -- "$@"
fi

# Exec do comando fornecido no CMD
exec "$@"
