#!/usr/bin/env bash
# Recria a conta de teste no Juice Shop. Necessário após cada restore, porque o reset
# apaga o banco (a conta é efêmera). As credenciais vêm do mesmo arquivo que o agente usa.
# Rodar no servidor, com o Juice Shop no ar.
set -euo pipefail

cd "$(dirname "$0")"
URL="http://127.0.0.1:3000"
CRED="../agent/credenciais.local.yaml"

if [[ ! -f "$CRED" ]]; then
  echo "[seed] FALHA: $CRED não existe. Crie-o a partir de agent/credenciais.exemplo.yaml."
  exit 1
fi

# Lê email/senha do YAML sem depender de libs (linhas simples 'chave: \"valor\"').
email=$(grep -E '^\s*email\s*:' "$CRED" | sed -E 's/^[^:]*:\s*"?([^"]*)"?\s*$/\1/')
senha=$(grep -E '^\s*senha\s*:' "$CRED" | sed -E 's/^[^:]*:\s*"?([^"]*)"?\s*$/\1/')

if [[ -z "$email" || -z "$senha" ]]; then
  echo "[seed] FALHA: não consegui ler email/senha de $CRED."
  exit 1
fi

body=$(jq -n --arg e "$email" --arg s "$senha" \
  '{email:$e, password:$s, passwordRepeat:$s, securityQuestion:{id:1}, securityAnswer:"teste"}')

code=$(curl -s -o /tmp/seed_resp.json -w '%{http_code}' \
  -X POST "$URL/api/Users" -H "Content-Type: application/json" -d "$body")

if [[ "$code" == "201" ]]; then
  echo "[seed] OK: conta de teste '$email' criada."
elif grep -qi "already" /tmp/seed_resp.json 2>/dev/null; then
  echo "[seed] OK: conta '$email' já existia (nada a fazer)."
else
  echo "[seed] FALHA ao criar '$email' (HTTP $code):"
  cat /tmp/seed_resp.json; echo
  exit 1
fi
