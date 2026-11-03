#!/usr/bin/env bash
# Verifica se o laboratório está pronto: Juice Shop, Ollama, ferramentas e isolamento.
# Uso: ./check_env.sh | tee ../logs/check_env_$(date +%Y%m%d_%H%M).txt
set -uo pipefail

JUICE="http://127.0.0.1:3000"
OLLAMA="http://127.0.0.1:11434"
MODEL="qwen3:4b"
fails=0

ok()   { echo "  [OK]    $*"; }
fail() { echo "  [FALHA] $*"; fails=$((fails + 1)); }

echo "== Verificação do ambiente — $(date -Iseconds) — $(hostname)"

echo "-- Ferramentas"
for t in docker nmap curl jq python3 tmux git; do
  flag="--version"; [[ "$t" == "tmux" ]] && flag="-V"
  if command -v "$t" >/dev/null; then ok "$t: $("$t" "$flag" 2>&1 | head -1)"; else fail "$t não instalado"; fi
done
if docker compose version >/dev/null 2>&1; then ok "$(docker compose version)"; else fail "docker compose não instalado"; fi

echo "-- Juice Shop"
code=$(curl -s -o /dev/null -w '%{http_code}' "$JUICE" || true)
if [[ "$code" == "200" ]]; then
  ok "responde em $JUICE (versão $(curl -s "$JUICE/rest/admin/application-version" | jq -r '.version'))"
else
  fail "não responde em $JUICE (HTTP $code)"
fi

echo "-- Ollama"
if curl -s "$OLLAMA/api/version" >/dev/null; then
  ok "responde em $OLLAMA (versão $(curl -s "$OLLAMA/api/version" | jq -r '.version'))"
  if curl -s "$OLLAMA/api/tags" | jq -e --arg m "$MODEL" '.models[] | select(.name == $m)' >/dev/null; then
    ok "modelo $MODEL instalado (digest $(curl -s "$OLLAMA/api/tags" | jq -r --arg m "$MODEL" '.models[] | select(.name == $m) | .digest[:12]'))"
  else
    fail "modelo $MODEL não encontrado (ollama pull $MODEL)"
  fi
else
  fail "não responde em $OLLAMA"
fi

echo "-- Isolamento (portas 3000 e 11434 só em 127.0.0.1)"
for port in 3000 11434; do
  binds=$(ss -tln | awk -v p=":$port" '$4 ~ p"$" {print $4}')
  if [[ -z "$binds" ]]; then
    fail "nada escutando na porta $port"
  elif echo "$binds" | grep -qvE '^127\.0\.0\.1:'; then
    fail "porta $port exposta além do localhost: $(echo $binds)"
  else
    ok "porta $port só em localhost: $(echo $binds)"
  fi
done

echo "-- Recursos"
free -h | awk 'NR<=2'
echo "  núcleos: $(nproc)"

echo
if [[ "$fails" -eq 0 ]]; then echo "== TUDO OK"; else echo "== ${fails} FALHA(S)"; exit 1; fi
