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
3. Trabalhar sempre dentro do `tmux` (`tmux new -s af`; para voltar depois de uma queda: `tmux attach -t af`).

### 2. Instalação no servidor
```bash
sudo apt update
sudo apt install -y docker.io docker-compose-v2 git jq nmap tmux curl python3-venv
sudo usermod -aG docker "$USER"   # sair e entrar de novo no SSH para valer
sudo timedatectl set-timezone America/Sao_Paulo   # logs com horário de Brasília (-03:00)
```

Acesso do servidor ao repositório privado (deploy key com escrita, para enviar os logs):
```bash
ssh-keygen -t ed25519 -C "discorder-af" -f ~/.ssh/af_deploy -N ""
cat ~/.ssh/af_deploy.pub   # colar em GitHub > Settings > Deploy keys, marcando "Allow write access"
GIT_SSH_COMMAND="ssh -i ~/.ssh/af_deploy" git clone git@github.com:marcoss0ft/af-techacker.git ~/af-techacker
cd ~/af-techacker && git config core.sshCommand "ssh -i ~/.ssh/af_deploy"
```

### 3. Juice Shop
```bash
cd ~/af-techacker/lab
docker compose up -d
./restore.sh          # recria o container e confirma o estado inicial
```
O Juice Shop escuta só em `127.0.0.1:3000`. Para abrir no navegador de outra máquina do grupo:
```bash
ssh -L 3000:127.0.0.1:3000 discorder_adm@10.0.80.3
```
e acessar `http://localhost:3000`.

### 4. Ollama e modelo
```bash
curl -fsSL https://ollama.com/install.sh | sh   # instalador oficial; cria o serviço systemd
ollama pull qwen3:4b
ollama run qwen3:4b --verbose "Explique em uma frase o que é o OWASP Juice Shop."
```
O Ollama escuta por padrão só em `127.0.0.1:11434`. **Não** alterar `OLLAMA_HOST`: ele não tem autenticação e não deve ficar acessível pela rede.

Servidor medido em 03/11/2026: 15 GiB de RAM (14 GiB disponíveis), 20 núcleos, sem GPU dedicada; o modelo roda na CPU.

### 5. Agente
```bash
cd ~/af-techacker/agent
python3 -m venv .venv && . .venv/bin/activate
pip install -r requirements.txt
python -m unittest test_escopo        # 14 testes da trava de escopo (não acessam a rede)
```
Rodar uma investigação (dentro do `tmux`):
```bash
python agent.py --investigacao I1 --objetivo "Descrição do objetivo em uma frase."
```
A cada passo o modelo propõe uma ação e o grupo decide: **[A]utorizar / [M]odificar / [R]ejeitar / [F]inalizar**. Tudo é registrado em `logs/investigacao_<id>.jsonl`, e a saída completa de cada ferramenta em `logs/raw/`.

**Ferramentas integradas:** `login` (autentica com a conta de teste), `http_request` (requisições ao Juice Shop, usando o token da sessão) e `dir_enum` (descoberta de rotas por lista pré-definida). O alvo e as portas são fixos no `config.yaml`; a trava de escopo fica no código das ferramentas (`agent/tools/`). As credenciais ficam em `agent/credenciais.local.yaml` (fora do git).

**Rotina antes de cada investigação que usa login:**
```bash
# 1. feche o Juice Shop no navegador (aberto, ele re-dispara desafios)
~/af-techacker/lab/restore.sh          # 2. zera o Juice Shop
~/af-techacker/lab/seed_usuario.sh     # 3. recria a conta de teste (apagada pelo restore)
```
Para investigações sem login (ex.: I1), o passo 3 é dispensável.

### 6. Restauração do Juice Shop
```bash
~/af-techacker/lab/restore.sh
```
Recria o container (o banco do Juice Shop vive dentro dele), espera a aplicação responder e confirma que **0 desafios** estão resolvidos. Cada execução fica registrada em `logs/restores.log`. Rodar antes de cada investigação.

### 7. Verificação do ambiente
```bash
~/af-techacker/lab/check_env.sh | tee ~/af-techacker/logs/check_env_$(date +%Y%m%d_%H%M).txt
```
Confere ferramentas, Juice Shop, Ollama, modelo instalado e se as portas 3000 e 11434 escutam só em `127.0.0.1`.

## Versões registradas

| Item | Valor |
|---|---|
| Juice Shop (tag da imagem) | `bkimminich/juice-shop:v20.3.0` |
| Ollama | 0.40.14 |
| Modelo / digest | `qwen3:4b` / `359d7dd4bcda` |
| Quantização | _a preencher (`ollama show qwen3:4b`)_ |
| `num_ctx` / `temperature` / `seed` / thinking | _a definir na Fase 2_ |
| Desempenho medido (CPU, 03/11/2026) | 17 tokens/s de geração, 65 tokens/s de leitura do prompt. Com thinking ligado, uma resposta de uma frase gerou 1265 tokens e levou 1min16s |
