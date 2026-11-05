# Plano de Ação — AF Tecnologias Hackers (26-2)

**Tema:** Testes de segurança ofensivos com apoio de IA (agente supervisionado + LLM local contra o OWASP Juice Shop)
**Caminho escolhido:** A — **tudo roda no servidor do kit (`discorder`)**; o grupo acessa por VPN + SSH, como no Roteiro 1.

> **Ideia central:** a nota **não** depende de quantas vulnerabilidades encontrarmos nem de quão autônomo o agente é. Depende de: (1) qualidade dos testes, (2) capacidade de **supervisionar** a IA e (3) **conclusões sustentadas por evidências**. Uma hipótese refutada com boas evidências vale tanto quanto uma vulnerabilidade confirmada.

---

## 0. Mapa: rubrica → o que entregamos

| Critério (peso) | O que o professor vai procurar | Onde está |
|---|---|---|
| Funcionamento e reprodução do lab (15%) | Juice Shop + LLM local + agente sobem **no kit** seguindo o README; isolamento; restauração verificada | Fase 1 |
| Desenvolvimento e integração do agente (20%) | ≥ 2 ferramentas, ≥ 1 no Juice Shop; loop propor → autorizar/modificar/rejeitar → executar → interpretar; decisões que **variam com os resultados**; limites no código | Fase 2 |
| Planejamento e qualidade técnica dos testes (20%) | Análise manual + plano **do grupo** antes do LLM, com hipóteses falseáveis e evidências que confirmam e refutam; revisão pelo LLM com tabela e justificativa técnica | Fase 3 |
| Qualidade das evidências e interpretação (20%) | 3 investigações distintas, 6 campos cada; logs que reconstroem tudo; conclusão ligada à evidência | Fases 4 e 5 |
| Análise crítica da IA (20%) | 7 perguntas da seção 6 com exemplos do log; ≥ 1 falha concreta (detecção e tratamento); comparação plano do grupo × agente | Fase 6 |
| Documentação e apresentação (5%) | Relatório de 4 a 6 páginas focado em interpretação; vídeo ≤ 10 min com 1 investigação completa | Fase 7 |

---

## O kit e o caminho A em uma figura

```
   Seu notebook (Windows) ── VPN (10.8.0.2) ──┐
                                               │
   Rede da sala 192.168.20.x ── pfSense (WAN 192.168.20.27 / LAN 10.0.80.1)
                                               │  sem NAT novo: nada da AF é exposto na WAN
                                               │
┌──────────────────── discorder 10.0.80.3 (Ubuntu 24.04) ───────────────────────┐
│  Do Roteiro 1 (FORA DO ESCOPO): Apache WordPress :80, Nextcloud :8000,         │
│                                 MariaDB :3306                                  │
│                                                                                │
│  Novo para a AF (tudo escutando só em 127.0.0.1, invisível na rede):           │
│    Juice Shop (Docker) ........ 127.0.0.1:3000   ← ALVO                        │
│    Ollama + qwen3:4b .......... 127.0.0.1:11434  ← IA                          │
│    Agente (Python) + nmap/curl  ← roda aqui, dentro de uma sessão tmux         │
│    logs/ (JSONL)                                                               │
└────────────────────────────────────────────────────────────────────────────────┘
```

**Por que o caminho A:**
- Juice Shop e Ollama escutam **só em `127.0.0.1`** (localhost). Ninguém na rede consegue acessá-los, nem os outros grupos, nem a VPN. O isolamento vem da configuração, sem regra de firewall nova e sem risco de perder o acesso ao servidor.
- O Ollama não tem senha. Em `127.0.0.1` isso deixa de ser problema.
- Vocês já sabem chegar ao servidor (VPN + SSH do Roteiro 1).
- **O que se perde:** os testes saem de dentro do próprio servidor, e não de uma máquina atacante separada. Isso entra como limitação no relatório (1 frase).

**E o Kali?** O enunciado só diz que o Juice Shop deve ser "acessível a partir do Kali" e que ferramentas do Kali "**poderão**" ser usadas. Ele não exige que o agente rode no Kali. No caminho A, qualquer máquina do grupo acessa o Juice Shop por **túnel SSH** (ver 1.2), inclusive um Kali, se houver. ✅ **Caminho A confirmado pelo professor em 03/11/2026.**

**De onde dá para trabalhar:** a VPN conecta em 192.168.20.27, que só existe dentro da rede do Insper. Funciona na rede da sala e na WannaCry (como no Roteiro 1); **de casa, não**. Testar cedo: na WannaCry fora da sala, ligar a VPN e rodar `ping 10.0.80.3`.

---

## Fase 0 — Organização (antes de tudo)

- [ ] **Perguntar ao professor, por escrito:**
  1. ✅ "Podemos rodar o agente direto no servidor do kit, sem Kali, acessando o Juice Shop por túnel SSH?" Confirmado em 03/11/2026.
  2. "Podemos usar IAs externas (ChatGPT, Claude) no código e nos documentos? Se sim, como declarar?"
- [x] **Ver se o servidor aguenta a IA.** Medido em 03/11/2026: **RAM total 15 GiB, disponível 14 GiB, 20 núcleos, 84 GB livres em disco**. Folga ampla para o Qwen3 4B (3–4 GB) junto com Apache, MariaDB e Juice Shop. Topologia A confirmada; a B não é necessária.
- [ ] **Repositório git privado** (GitHub privado). Vocês editam no notebook e fazem `git pull` no servidor.
  ```
  ├── README.md                    # como subir tudo no kit, passo a passo
  ├── lab/
  │   ├── docker-compose.yml       # Juice Shop (tag fixa, só em 127.0.0.1)
  │   ├── restore.sh               # recria o container e verifica o estado inicial
  │   ├── check_env.sh             # Juice Shop, Ollama, ferramentas, isolamento
  │   └── pfsense_regra_saida.md   # regra que corta a internet do servidor nos testes
  ├── agent/
  │   ├── agent.py                 # loop principal
  │   ├── config.yaml              # alvo, portas permitidas, modelo, temperature, seed, limites
  │   ├── tools/                   # wrappers das ferramentas (com trava de escopo)
  │   ├── prompts/                 # prompt de sistema e prompt de revisão, versionados
  │   ├── summarize_logs.py        # métricas para a Fase 6
  │   └── requirements.txt
  ├── planejamento/
  │   ├── observacoes_iniciais.md  # análise manual, datada
  │   ├── plano_testes_grupo.md    # feito SEM IA (Fase 3a)
  │   └── revisao_llm.md           # sugestões do modelo e decisões do grupo (Fase 3b)
  ├── logs/
  │   ├── investigacao_<id>.jsonl  # uma linha por turno; nunca editar à mão
  │   └── raw/                     # saídas completas das ferramentas
  ├── investigacoes/  I1.md  I2.md  I3.md
  ├── relatorio/
  └── video/
  ```
- [ ] Dividir as frentes entre os dois: **lab + ferramentas** e **agente + logs**. Os dois precisam conseguir **explicar a arquitetura**, porque o enunciado exige isso.
- [ ] Combinar a data de entrega e fazer um cronograma de trás para frente (ver o fim do documento).

---

## Fase 1 — Laboratório reproduzível (15%)

> ✅ **Status em 03/11/2026:** Juice Shop 20.3.0, Ollama 0.40.14 e `qwen3:4b` rodando no `discorder`; restore com verificação OK; `check_env.sh` TUDO OK; isolamento comprovado de dentro e de fora (`logs/check_env_20261103_1109.txt`, `logs/isolamento_notebook_20261103_1121.txt`). Pendente: regra de saída no pfSense (1.5), que só precisa estar pronta antes da Fase 4.

> **Regra do enunciado (seções 1 e 7):** o ambiente roda "no kit de laboratório". Alvo, modelo e agente ficam no `discorder`. Nada roda em nuvem nem usa API externa de LLM.

### 1.1 Preparar o servidor
- [ ] Entrar: notebook → VPN → `ssh discorder_adm@10.0.80.3`.
- [ ] Conferir se o IP fixo do Roteiro 1 continua valendo: `ip -br a` → `enp0s31f6 10.0.80.3/24`.
- [ ] Instalar o básico: `sudo apt install -y docker.io docker-compose-v2 tmux git python3-venv nmap curl jq` e adicionar o usuário ao grupo do Docker: `sudo usermod -aG docker discorder_adm` (sair e entrar de novo no SSH).
- [ ] **Usar sempre `tmux`.** Se a VPN ou o Wi-Fi cair, o agente continua rodando no servidor. Voltar com `tmux attach`.
- [ ] **Não** ligar o `ufw` nem mexer no firewall do servidor. No caminho A isso não é necessário, e um erro ali corta o SSH. Aí só indo fisicamente até o servidor para consertar.

### 1.2 Juice Shop
- [ ] `docker compose` com **tag fixa** (ex.: `bkimminich/juice-shop:<versão>`), anotada no README.
- [ ] Publicar **só no localhost**: `ports: ["127.0.0.1:3000:3000"]`.
- [ ] O container não pode ter montagem de volume do servidor, `network_mode: host` nem `privileged`. Assim um comprometimento do Juice Shop não alcança o Apache, o MariaDB nem os dados do Nextcloud.
- [ ] **Abrir o Juice Shop no navegador do notebook** (para a análise manual da Fase 3a), com um túnel SSH:
  ```bash
  ssh -L 3000:127.0.0.1:3000 discorder_adm@10.0.80.3
  ```
  e abrir `http://localhost:3000` no notebook. O mesmo comando funciona num Kali, se o grupo tiver um.

### 1.3 LLM local
- [ ] Instalar o Ollama (instalador oficial, serviço systemd) e `ollama pull qwen3:4b`. Por padrão ele já escuta só em `127.0.0.1:11434`, então **não mexer** no `OLLAMA_HOST`.
- [ ] Registrar no README: versão do Ollama, **digest** do modelo (`ollama list`), quantização, `num_ctx`, `temperature`, `seed`, thinking ligado/desligado.
- [ ] Medir o tempo por resposta e a RAM livre **com o Apache e o MariaDB rodando**: `ollama run qwen3:4b --verbose "teste"` mostra os tokens/s, e `free -h` mostra a RAM. Anotar, porque isso entra nas limitações. Se ficar lento: thinking desligado e `num_ctx` menor.
- [ ] **Se não couber na RAM:** falar com o professor antes de improvisar (por exemplo, rodar o modelo no notebook pode violar o "no kit").

### 1.4 Ferramentas de segurança (no `discorder`)
- `curl` / cliente HTTP em Python: interação direta com o Juice Shop (obrigatório).
- `nmap`: serviços e versões, **só na porta 3000 do localhost**.
- Opcionais, se as investigações pedirem: `ffuf` (wordlist pequena), decodificador de JWT (local, sem rede). `sqlmap` só com limites estritos e se o plano do grupo justificar.

### 1.5 Isolamento (simples no caminho A)
- [x] **Prova de que só o localhost escuta:** feita pelo `check_env.sh` (`logs/check_env_20261103_1109.txt`).
- [x] **Teste do lado de fora:** do notebook (VPN 10.8.0.2), as portas 3000 e 11434 recusam conexão; pelo túnel SSH, `http://localhost:3000` responde 200; o WordPress (controle) responde 200, provando que a VPN estava ativa (`logs/isolamento_notebook_20261103_1121.txt`).
- [ ] **Sem internet durante os testes:** no pfSense, uma regra na LAN com ação Block, origem `SRV_WEB`, destino *não* `REDES_LAB` (novo alias: 10.0.80.0/24 e 10.8.0.0/24), log ligado, **acima** de "Default allow LAN to any". Ligar só nas rodadas de teste; o `docker pull` e o `ollama pull` são feitos antes. As respostas do WordPress e do Nextcloud continuam funcionando, porque o pfSense é stateful. Essa regra impede que o Juice Shop busque URLs externas sugeridas pela IA. Documentar em `lab/pfsense_regra_saida.md`, com print analisado.
- [ ] **Não** criar port forward novo na WAN.

### 1.6 Restauração (`restore.sh`, no `discorder`)
- [ ] `docker compose down` seguido de `docker compose up -d --force-recreate`.
- [ ] Esperar o Juice Shop responder (laço com `curl` até HTTP 200, com timeout).
- [ ] **Verificação objetiva do estado inicial**, impressa pelo script: nenhum desafio resolvido em `/api/Challenges` e/ou um marcador criado antes do reset (ex.: um usuário de teste) não existe mais.
- [ ] Mexe **só** no container do Juice Shop: nunca `docker system prune`, nunca reiniciar o Apache ou o MariaDB.
- [ ] O restore **não** é ferramenta do agente: quem executa é o grupo. Rodar antes de cada investigação; o horário e a saída da verificação vão para o primeiro registro do log.

### 1.7 Verificação do ambiente
- [ ] `check_env.sh`: Juice Shop e Ollama respondem em `127.0.0.1`; ferramentas instaladas; versões impressas; `ss` mostrando só localhost.
- [ ] Teste final: o colega que não montou segue **só o README, no kit**, e sobe tudo.

---

## Fase 2 — Agente supervisionado (20%)

### 2.1 Arquitetura (simples e explicável)
Python com chamadas diretas à API do Ollama (`http://127.0.0.1:11434/api/chat`), sem framework pesado. Saída do modelo em JSON com schema fixo (via `format` com JSON Schema, ou via `tools` nativo — escolher um e justificar). O loop fica transparente e os dois conseguem explicá-lo.

```
Objetivo da investigação (só o objetivo, sem a estratégia do grupo)
   │
   ▼
LLM: {ferramenta, parâmetros, justificativa} ◄────────────────────────────┐
   │                                                                     │
   ▼                                                                     │
Humano: [A]utorizar / [M]odificar / [R]ejeitar / [F]inalizar (+ motivo)   │
   │            │                                                        │
   │            └─ M/R: decisão e motivo voltam ao modelo ───────────────┤
   ▼                                                                     │
Wrapper valida (alvo/porta do config, limites) ──► executa ──► saída     │
   │                                         (completa em logs/raw/,     │
   │                                          resumo truncado ao modelo) │
   ▼                                                                     │
LLM interpreta o resultado + atualiza "fatos observados" ────────────────┘
   │
Grupo registra a decisão após o resultado (e nova hipótese, se houver)
   │
Tudo gravado em logs/investigacao_<id>.jsonl, uma linha por turno
```

### 2.2 Ferramentas expostas ao modelo (≥ 2, ≥ 1 no Juice Shop)
As duas ferramentas saem das 3 investigações escolhidas (ver `planejamento/plano_testes_grupo.md`). nmap e leitor de JWT foram considerados e descartados: o alvo já é conhecido (nmap) e o I2 ficou com IDOR, não com o token (JWT).

| Ferramenta | Função | Limites (no código) |
|---|---|---|
| `http_request(method, path, headers, body)` | Interagir com o Juice Shop (I2 IDOR, I3 XSS, confirmações de I1) | Alvo fixo `http://127.0.0.1:3000` vindo do `config`; o modelo só escolhe **path**, método, headers e corpo; **não segue redirect** para fora; timeout; tamanho máximo de corpo |
| `dir_enum(caminhos)` | Descoberta de rotas (I1) | Só caminhos de uma **lista pré-definida** no `config`; teto de caminhos por execução; rate limit; **comparação com uma linha de base** (caminho inexistente), porque o Juice Shop é SPA e devolve 200 com o `index.html` para quase qualquer rota |

**Regras de segurança (obrigatórias pelo enunciado e ponto de nota):**
- A trava de escopo fica **no código dos wrappers**, não só no prompt. Pedido para outro host/porta → recusa + registro (`tags: ["fora_escopo"]`). Isso é essencial aqui, porque o alvo divide o servidor com o WordPress, o Nextcloud, o MariaDB e o próprio Ollama. Um "achado" neles não é um achado do Juice Shop.
- Teste negativo documentado: forçar uma proposta para outro host ou para a porta 80 e mostrar a recusa no log.
- O modelo **não** tem shell livre; os wrappers montam a linha de comando a partir de parâmetros validados (sem `shell=True`).
- Limite de turnos por investigação (ex.: 15) e timeout por ferramenta.
- URLs externas em parâmetros (ex.: campos que fazem o servidor buscar uma URL) são rejeitadas pelo grupo e marcadas `fora_escopo`.

### 2.3 Cuidados específicos com o Qwen3 4B
- **Thinking mode:** desligar (`"think": false` na API) ou separar o bloco `<think>` antes de validar. Guardar a resposta bruta mesmo assim.
- **Validação:** checar o JSON contra o schema. Se vier inválido, 1 nova tentativa com a mensagem de erro; se falhar de novo, o turno vai para o humano. **Registrar cada falha** (`json_invalido`).
- **Contexto curto:** saída ao modelo truncada/resumida (ex.: 3–4 mil caracteres); saída completa em `logs/raw/` com SHA-256 no log.
- **Memória da investigação:** lista curta de "fatos observados até agora", reenviada a cada turno, para que a próxima ação dependa dos resultados.
- **Feedback da decisão humana:** depois de Modificar/Rejeitar, o próximo prompt contém a decisão e o motivo. Sem isso, o modelo repete a proposta.
- **Reprodutibilidade:** `temperature` baixa e `seed` fixa em `options`; prompt de sistema versionado com hash no log.

### 2.4 Registro (JSONL, uma linha por turno, gravada na hora)
Os campos cobrem a lista da seção 5 do enunciado e o que a Fase 6 precisa:
```json
{
  "investigacao": "I2",
  "sessao": "I2-2026-11-05T14:02",
  "turno": 4,
  "timestamp": "2026-11-05T14:02:31-03:00",
  "objetivo": "...",
  "config": {"modelo": "qwen3:4b", "digest": "...", "temperature": 0.2, "seed": 42, "prompt_sha256": "..."},
  "resposta_bruta_modelo": "...",
  "json_valido": true,
  "tentativas": 1,
  "justificativa_modelo": "por que o modelo escolheu esta ação",
  "ferramenta_proposta": "http_request",
  "parametros_propostos": {"method": "GET", "path": "/..."},
  "decisao_humana": "AUTORIZADO | MODIFICADO | REJEITADO | FINALIZADO",
  "motivo_decisao": "...",
  "parametros_executados": {},
  "bloqueio_escopo": null,
  "saida_resumo": "...",
  "saida_arquivo": "logs/raw/I2_turno4.txt",
  "saida_sha256": "...",
  "duracao_ms": {"modelo": 0, "ferramenta": 0},
  "interpretacao_modelo": "...",
  "fatos_observados": ["..."],
  "decisao_grupo_pos_resultado": "o que o grupo concluiu e decidiu depois de ver o resultado",
  "nova_hipotese": null,
  "tags": ["boa_sugestao"]
}
```
- Turno REJEITADO: `parametros_executados`, `saida_*` e `interpretacao_modelo` ficam `null`, mas o motivo é registrado e enviado ao modelo.
- O primeiro registro de cada investigação é do tipo `restore` (horário + saída da verificação).
- Timestamps em ISO 8601 **com offset** (`-03:00`). Os logs do pfSense saem em UTC, como o Roteiro 1 já constatou.
- **Tags** (marcadas na hora): `falha_ia`, `alucinacao`, `json_invalido`, `repeticao`, `fora_escopo`, `interpretacao_errada`, `boa_sugestao`.
- `summarize_logs.py` gera as tabelas do relatório: contagem de A/M/R/F, falhas por tipo, repetições, tempo médio por turno.

### 2.5 Provar que não é uma sequência fixa
- Apontar no relatório turnos em que a proposta seguinte **cita explicitamente** um resultado anterior.
- Rodar **o mesmo objetivo duas vezes** após o restore, com uma mudança controlada no ambiente entre as duas, e mostrar que os caminhos divergiram.
- Seed e temperatura fixas **reduzem** a variação aleatória, mas o Ollama não garante determinismo total. Por isso, antes, rodar o mesmo objetivo duas vezes **sem** mudar o ambiente: se o caminho se repete, a divergência com o ambiente alterado fica atribuída ao resultado das ferramentas. Se não se repetir, registrar isso como limitação.

---

## Fase 3 — Planejamento dos testes (20%)

> ⚠️ **Regra do enunciado:** o plano inicial é feito **sem LLM**. Vale para o Qwen e, no espírito da regra, para qualquer outra IA. A Fase 6 compara o plano do grupo com o que o agente propôs; se a IA escrever o plano, a comparação perde o sentido. Por isso aqui há **só o template e perguntas-guia**. As hipóteses são do grupo.

### O que é "um teste" nesta AF
Um teste não é "rodar uma ferramenta". É uma **pergunta que pode dar errado**:

> **Hipótese:** "Acho que X acontece, porque observei Y."
> **Como testar:** "Vou fazer Z com a ferramenta W."
> **Confirma se:** "a resposta mostrar A."  **Refuta se:** "a resposta mostrar B."

Se não existir um resultado que **refute** a hipótese, ela não é testável. Reescrevam.

### 3a. Plano do grupo (sem IA)
**Passo 1 — Explorar o Juice Shop à mão (1 a 2 horas, os dois juntos).** Abrir pelo túnel SSH (1.2), usar o site como um cliente comum e, ao mesmo tempo, olhar a aba **Network** do DevTools do navegador (F12). Anotar com data em `planejamento/observacoes_iniciais.md` tudo o que parecer estranho ou interessante.

**Passo 2 — Responder às perguntas-guia de cada tema.** O enunciado sugere três temas; seguir essa linha é o caminho mais seguro.

- **I1 — Reconhecimento e enumeração.** O que a aplicação revela sobre si mesma sem login? Que páginas e rotas existem, e quais aparecem só no código JavaScript ou nas requisições, sem link visível? O servidor entrega arquivos ou informações que não deveria?
- **I2 — Autenticação ou autorização.** Como o site sabe quem você é depois do login? Onde essa informação fica guardada e o que tem dentro dela? O que acontece se você pedir uma coisa que pertence a outro usuário? Como o login trata o que você digita?
- **I3 — Tratamento de entradas, requisições ou acesso a recursos.** Onde o usuário consegue mandar dados para o servidor (busca, formulários, uploads, avaliações)? O que volta na resposta quando você manda algo inesperado? Dá para acessar um recurso mudando um número ou um caminho na requisição?

Usem também o que viram nas aulas da disciplina: cada aula é uma fonte de hipóteses.

**Passo 3 — Preencher `planejamento/plano_testes_grupo.md`**, para cada investigação:
1. **Aspecto investigado** e por que (ligado a uma observação do passo 1 e ao conteúdo da disciplina).
2. **Hipóteses iniciais:** 1 ou 2, cada uma no formato acima.
3. **Ferramentas:** qual ferramenta testa qual hipótese e por quê.
4. **Evidências:** o que **confirma** e o que **refuta** cada hipótese (código HTTP, conteúdo da resposta, token obtido, dado acessado etc.).
5. **Previsão sobre a IA:** onde o grupo acha que o agente vai ajudar e onde vai falhar.

- [ ] **Commitar e fazer push** do plano antes de mostrá-lo ao modelo. O horário do push no GitHub comprova a ordem exigida. Hash e horário entram no relatório.

### 3b. Revisão pelo LLM local
- [ ] Enviar o plano ao Qwen com um prompt fixo em `agent/prompts/revisao.md`, pela mesma integração do agente, para que a chamada fique em log. Pedir: lacunas, hipóteses alternativas, ferramentas não consideradas.
- [ ] Tabela em `planejamento/revisao_llm.md`:

| # | Sugestão do modelo | Decisão (aceita/modificada/rejeitada) | Justificativa técnica |
|---|---|---|---|

- Rejeitar com bons motivos também conta. Motivos típicos: fora do escopo, inseguro, tecnicamente errado, redundante, genérico demais.
- O que for aceito entra num **novo commit** do plano; o original fica intacto.

---

## Fase 4 — Execução das 3 investigações (20%)

**Antes:** uma investigação-piloto (`P0`) descartável para calibrar prompt e wrappers. Registrar o que mudou entre o piloto e a rodada oficial.

Para cada investigação:
1. Ligar a regra do pfSense que corta a internet do servidor; rodar `restore.sh` + verificação, registrados no log.
2. Dar ao agente **só o objetivo**, sem a hipótese nem a estratégia do grupo.
3. Supervisionar cada turno: autorizar, modificar ou rejeitar, **sempre com motivo**.
4. Quando o modelo concluir algo, **confirmar com evidência independente** (requisição reproduzida, conteúdo da resposta). Sugestão do modelo não é evidência.
5. Hipóteses que surgirem no meio vão em `nova_hipotese`.
6. Encerrar quando a hipótese for confirmada ou refutada, ou quando o limite de turnos for atingido. O resultado em cada caso é válido.

Preencher `investigacoes/Ix.md` com os **6 campos obrigatórios**:
1. Hipótese inicial (o que e por quê)
2. Estratégia proposta pelo grupo
3. Contribuição do agente (ações e ferramentas sugeridas)
4. Execução (o que de fato rodou e os resultados, com referência aos turnos do log)
5. Intervenção humana (aceitas, modificadas e rejeitadas, e por quê)
6. Conclusão: CONFIRMADA / REFUTADA / INCONCLUSIVA, o que as evidências permitem afirmar e quais limitações permanecem

---

## Fase 5 — Evidências (20%)

- [ ] Toda afirmação do relatório aponta para `investigacao_<id>.jsonl, turno N` ou para um arquivo em `logs/raw/`.
- [ ] Logs nunca editados à mão. Anotações posteriores vão em arquivo separado.
- [ ] Prints só acompanhados de análise (o enunciado penaliza "capturas de tela sem análise").
- [ ] Separar sempre o que foi **observado** (saída da ferramenta), o que foi **interpretado pelo modelo** e o que foi **concluído pelo grupo**.

---

## Fase 6 — Análise crítica da IA (20%)

Responder às 7 perguntas da seção 6, cada uma **com exemplos do log**:
1. Quando as sugestões foram tecnicamente adequadas?
2. As ferramentas escolhidas eram coerentes com o objetivo?
3. Os resultados influenciaram as decisões seguintes? (mostrar a cadeia de turnos e a execução dupla da 2.5)
4. Houve interpretações incorretas ou conclusões sem evidência?
5. Houve ações repetitivas, desnecessárias ou inadequadas?
6. Quando a intervenção humana foi necessária?
7. Quais limitações foram observadas no modelo **e na integração** (separadamente)?

**Falhas comuns em um modelo de 4B** (marcar com a tag na hora):
- endpoints ou parâmetros inventados (`alucinacao`);
- JSON malformado (`json_invalido`);
- leitura errada de 401/403/500, de respostas vazias ou dos 200 do SPA (`interpretacao_errada`);
- loop repetindo a mesma ação, inclusive depois de rejeitada (`repeticao`);
- declarar "vulnerável" sem evidência (`falha_ia`);
- tentar sair do escopo, o que mostra o wrapper bloqueando (`fora_escopo`).

**Obrigatório:** pelo menos **1 caso concreto em detalhe** (2 ou 3 é melhor): o que aconteceu, como o grupo percebeu, o que fez (rejeitou, corrigiu parâmetro, ajustou prompt ou wrapper) e o que isso ensina.

**Comparações:**
- Plano do grupo × agente: tabela com o que o plano previu, o que o agente propôs (igual / diferente / novo) e o resultado. Não é preciso mostrar que um ganhou do outro.
- Previsão do grupo sobre a IA (Fase 3a) × o que de fato aconteceu.
- Se a taxa de Modificar foi alta, dizer isso: mostra onde o agente contribuiu pouco.

---

## Fase 7 — Relatório (4 a 6 páginas) e vídeo (até 10 min)

**Relatório (estrutura e espaço):**
1. Introdução, escopo e ética: lab local, escopo restrito ao Juice Shop (o servidor também tem serviços do Roteiro 1), isolamento por localhost e regra de saída no pfSense (0,25 p)
2. Arquitetura do lab e do agente: diagrama, ferramentas, limites, log; por que o caminho A e o que ele deixa de fora (0,75 p)
3. Estratégia de testes: plano do grupo e revisão do LLM com a tabela (0,75 p)
4. Resultados das 3 investigações, focados em interpretação e evidência (2 p)
5. Análise crítica da IA: 7 perguntas, falha concreta, comparações (1,5 p)
6. Conclusão e limitações (0,25 p)
- Total previsto: 5,5 p. A meia página de folga absorve o diagrama e as tabelas sem passar do limite de 6.
- Instalação vai para o README, não para o relatório.
- Citar hash e horário do push do plano do grupo (Fase 3a) e do commit da revisão (Fase 3b).
- Declaração de uso de IA externa conforme a resposta do professor.

**Vídeo (até 10 min):**
- 0:00–1:00 Objetivo e arquitetura (diagrama)
- 1:00–2:00 Lab rodando, isolamento e restore com verificação
- 2:00–8:00 **Uma investigação completa**: hipótese, propostas do modelo, autorizações, modificações e rejeições, resultados e conclusão, com o log aparecendo
- 8:00–9:30 Uma falha da IA e como foi tratada; lições
- Gravar a tela do notebook com o terminal SSH. A IA pode levar minutos por turno: gravar a investigação inteira e **cortar as esperas, sinalizando os cortes na tela**. Ensaiar e cronometrar abaixo de 10 min.

---

## Checklist final de entrega

- [ ] Resposta do professor sobre o Kali e sobre IA externa
- [ ] README reproduzido **no kit** por quem não montou
- [ ] `lab/` com compose de tag fixa (só `127.0.0.1`), `restore.sh` com verificação, `check_env.sh`, saídas do teste de isolamento e regra de saída do pfSense documentada
- [ ] Versão do Ollama, digest do modelo, quantização, `num_ctx`, `temperature` e `seed` no README
- [ ] Código do agente com ≥ 2 ferramentas, trava de escopo no código, sem shell livre, teste negativo logado
- [ ] Plano do grupo (push anterior à revisão) e revisão do LLM com tabela de decisões
- [ ] Piloto registrado e diferenças para a rodada oficial anotadas
- [ ] 3 investigações com os 6 campos cada
- [ ] Logs JSONL completos, com respostas brutas do modelo e saídas em `logs/raw/`
- [ ] Execução dupla do mesmo objetivo mostrando divergência
- [ ] Análise crítica com as 7 perguntas, ≥ 1 falha concreta e as comparações
- [ ] Relatório com 4 a 6 páginas
- [ ] Vídeo com até 10 min, 1 investigação completa, cortes sinalizados
- [ ] WordPress, Nextcloud e SSH do Roteiro 1 continuam funcionando

---

## Ordem e esforço relativo

| Fase | Esforço | Depende de | Precisa estar no Insper? |
|---|---|---|---|
| 0 Organização | baixo | — | não (exceto `free -h`) |
| 1 Lab | médio | 0 | sim (VPN só funciona na rede do Insper) |
| 3a Plano do grupo | médio | 1 (exploração manual pelo túnel) | exploração: sim; escrita: não |
| 2 Agente | **alto** | 1 (em paralelo com a 3a) | escrever: não; testar: sim |
| 3b Revisão LLM | baixo | 2 e 3a (push feito) | sim |
| 4/5 Piloto + investigações | **alto** | 2, 3b | sim |
| 6 Análise crítica | médio | 4 | não |
| 7 Relatório e vídeo | médio | 4, 6 | gravação: sim |

> Deixar **pelo menos 30% do tempo** para as Fases 4 a 7. É comum gastar tempo demais no agente e fazer as investigações e a análise na correria, e essas fases somam 60% da nota. Como quase tudo que roda no kit exige estar no Insper, **marquem já os dias de laboratório**.
