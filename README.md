# AF — Testes ofensivos com apoio de IA (Grupo 7)

Agente supervisionado que integra um LLM local (Qwen3 4B via Ollama) a ferramentas de segurança para investigar o OWASP Juice Shop, no kit de laboratório da disciplina Tecnologias Hackers (Insper, 26-2).

## Arquitetura

Tudo roda no servidor do kit (`discorder`, Ubuntu 24.04, 10.0.80.3), atrás do pfSense do Roteiro 1. Juice Shop e Ollama escutam apenas em `127.0.0.1`, então não ficam acessíveis pela rede. O grupo acessa o servidor por VPN + SSH.

| Componente | Endereço | Observação |
|---|---|---|
| Juice Shop (Docker) | `127.0.0.1:3000` | Alvo dos testes |
| Ollama + `qwen3:4b` | `127.0.0.1:11434` | LLM local |
| Agente (Python) | — | Roda no servidor, dentro do `tmux` |
| WordPress / Nextcloud / MariaDB | `:80` / `:8000` / `:3306` | Do Roteiro 1; **fora do escopo** |

## Como reproduzir

> Em construção. Cada seção é preenchida conforme o laboratório é montado.

### 1. Acesso ao servidor
1. Conectar a VPN do pfSense (só funciona na rede do Insper).
2. `ssh discorder_adm@10.0.80.3`

### 2. Instalação no servidor
_A preencher (Fase 1)._

### 3. Juice Shop
_A preencher (Fase 1)._

### 4. Ollama e modelo
_A preencher (Fase 1)._

### 5. Agente
_A preencher (Fase 2)._

### 6. Restauração do Juice Shop
_A preencher (Fase 1)._

## Versões registradas

| Item | Valor |
|---|---|
| Juice Shop (tag da imagem) | _a preencher_ |
| Ollama | _a preencher_ |
| Modelo / digest | _a preencher_ |
| Quantização | _a preencher_ |
| `num_ctx` / `temperature` / `seed` / thinking | _a preencher_ |
