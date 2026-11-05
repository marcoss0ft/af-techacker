# Revisão do plano pelo LLM local (Fase 3b)

> O plano do grupo (`plano_testes_grupo.md`) foi enviado ao Qwen3 4B **depois** de registrado,
> pela integração do agente (`agent/revisar_plano.py`), ficando a resposta salva em log.

**Commit/push do plano original:** hash `________`, horário `________` _(preencher com `git log` do commit do plano)_
**Log da revisão:** `logs/revisao_llm_20261105_1334.txt`

## Observações gerais sobre a revisão
- O modelo leu o plano e fez críticas **específicas** ao nosso caso (citou `/rest/basket/<id>`, o HTML cru nas descrições, o XSS refletido na busca), não genéricas. Bom sinal de uso de contexto.
- As sugestões, no entanto, em sua maioria ampliam escopo; coube ao grupo filtrar o que agrega sem desviar dos objetivos.

## Decisões

| # | Sugestão do modelo | Decisão | Justificativa técnica |
|---|---|---|---|
| 1a / 2a | I1: enumerar também endpoints de API que exigem autenticação (ex.: `/api/users`) | Modificada | Ampliamos a wordlist da `dir_enum` com alguns endpoints de API, mas sem focar em "exigir autenticação", que foge do objetivo de I1 (rotas/recursos não listados). |
| 1b | I1: testar arquivos sensíveis (`.env`, backups, configs) | Aceita | Baixo custo e aderente a I1. Reforçamos a wordlist com arquivos de backup/config além do `/ftp` que já tínhamos. |
| 1c / 2c / 4a | I3: investigar XSS **armazenado** nas descrições de produto, além do refletido | Rejeitada | Escolha deliberada. Mantivemos só o XSS **refletido** justamente para observar a limitação do agente (não renderiza a tela), que é objeto da análise crítica. O armazenado seria confirmável pelo agente e redundante com I2, diluindo o contraste entre as três investigações. |
| 2b / 4b | I2: ampliar o IDOR para outros endpoints (`/user`, `/profile`) além do carrinho | Aceita (modificada) | Incluímos **um** recurso a mais além do carrinho, para testar se a falha de autorização é um padrão da aplicação. Limitado a um endpoint extra para manter a investigação focada. |
| 2b (JWT) | I2: falhas de autorização via JWT em vez de IDOR | Rejeitada | JWT é outra técnica, não IDOR; já havíamos descartado o JWT ao escolher o IDOR no I2. Fica como possível trabalho futuro. |
| 3a | Usar OWASP ZAP (scanner automático) | Rejeitada | O enunciado pede um agente supervisionado com um conjunto **limitado** de ferramentas; um scanner automático foge da proposta e tira a supervisão humana do centro. |
| 3b | Usar Selenium (navegador automatizado) para renderizar a tela no I3 | Rejeitada | Isso contornaria a limitação do agente na I3 — e é exatamente essa limitação que queremos **observar e documentar**, não eliminar. |

## Ajustes aplicados ao plano após a revisão
- I2: adicionado um segundo endpoint para o teste de IDOR (ver `plano_testes_grupo.md`).
- I1: wordlist da `dir_enum` reforçada com arquivos sensíveis/backup (ver `agent/config.yaml`).
