#!/usr/bin/env bash
# Restaura o Juice Shop a um estado conhecido.
# O Juice Shop guarda tudo dentro do container, então recriar o container = banco zerado.
# Mexe só no container do Juice Shop: nunca no Apache, MariaDB ou Ollama.
set -euo pipefail

cd "$(dirname "$0")"
URL="http://127.0.0.1:3000"
TIMEOUT_S=180
HISTORY="../logs/restores.log"

echo "[restore] $(date -Iseconds) recriando o container do Juice Shop..."
docker compose down
docker compose up -d --force-recreate

echo "[restore] aguardando o Juice Shop responder (até ${TIMEOUT_S}s)..."
up=0
for ((i = 0; i < TIMEOUT_S; i += 3)); do
  code=$(curl -s -o /dev/null -w '%{http_code}' "$URL" || true)
  if [[ "$code" == "200" ]]; then up=1; break; fi
  sleep 3
done
if [[ "$up" -ne 1 ]]; then
  echo "[restore] FALHA: o Juice Shop não respondeu em ${TIMEOUT_S}s (docker compose logs para ver o motivo)"
  exit 1
fi

# Verificação objetiva do estado inicial: nenhum desafio resolvido.
solved=$(curl -s "$URL/api/Challenges" | jq '[.data[] | select(.solved == true)] | length')
version=$(curl -s "$URL/rest/admin/application-version" | jq -r '.version')
ts=$(date -Iseconds)

if [[ "$solved" != "0" ]]; then
  echo "[restore] FALHA: ${solved} desafio(s) já resolvido(s) depois do reset"
  echo "${ts} FALHA juice-shop=${version} desafios_resolvidos=${solved}" >> "$HISTORY"
  exit 1
fi

echo "[restore] OK: Juice Shop ${version} no estado inicial (0 desafios resolvidos) em ${ts}"
echo "${ts} OK juice-shop=${version} desafios_resolvidos=0" >> "$HISTORY"
