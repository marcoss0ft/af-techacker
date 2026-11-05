"""Ferramenta de login/preparação: deixa a sessão pronta para a investigação.

Faz, de uma vez, o que seria feito à mão no navegador:
  1. registra a conta de teste se ela não existir (o restore apaga o banco);
  2. autentica e guarda o token;
  3. descobre o id do carrinho do usuário (bid) e guarda na sessão;
  4. coloca um item no carrinho, para ele ter conteúdo identificável.

As credenciais vêm de credenciais.local.yaml (fora do git), não do modelo nem do log.
"""

from pathlib import Path

import requests
import yaml

from .base import ParametrosInvalidos, ResultadoFerramenta, Sessao

ARQ_CRED = Path(__file__).resolve().parent.parent / "credenciais.local.yaml"
PRODUTO_PADRAO = 1   # Apple Juice, existe no seed do Juice Shop


class Login:
    nome = "login"
    descricao = (
        "Prepara a sessão autenticada: registra a conta de teste se preciso, autentica, "
        "descobre o id do carrinho do próprio usuário e adiciona um item a ele. Guarda o token "
        "para as requisições seguintes. Sem parâmetros: e-mail e senha são fixos (fora do modelo). "
        "Informa no resultado o id do carrinho do usuário, para a investigação saber qual é o 'nosso'."
    )

    def __init__(self, cfg_alvo: dict, cfg_limites: dict, sessao: Sessao):
        self.base_url = cfg_alvo["base_url"].rstrip("/")
        self.timeout = cfg_limites["timeout_ferramenta_s"]
        self.sessao = sessao

    def _credenciais(self) -> tuple[str, str]:
        if not ARQ_CRED.exists():
            raise ParametrosInvalidos(
                f"arquivo de credenciais não encontrado: {ARQ_CRED.name}. "
                "Copie credenciais.exemplo.yaml para credenciais.local.yaml e preencha."
            )
        dados = yaml.safe_load(ARQ_CRED.read_text(encoding="utf-8"))
        return dados["email"], dados["senha"]

    def _login(self, email: str, senha: str) -> requests.Response:
        return requests.post(
            f"{self.base_url}/rest/user/login",
            json={"email": email, "password": senha}, timeout=self.timeout,
        )

    def _registrar(self, email: str, senha: str) -> requests.Response:
        return requests.post(
            f"{self.base_url}/api/Users",
            json={"email": email, "password": senha, "passwordRepeat": senha,
                  "securityQuestion": {"id": 1}, "securityAnswer": "teste"},
            timeout=self.timeout,
        )

    def executar(self, p: dict) -> ResultadoFerramenta:
        email, senha = self._credenciais()
        passos = []

        # 1. login; se falhar, tenta registrar e logar de novo.
        resp = self._login(email, senha)
        if resp.status_code != 200:
            reg = self._registrar(email, senha)
            if reg.status_code not in (200, 201):
                self.sessao.token = None
                return ResultadoFerramenta(
                    f"Falha ao registrar {email}: HTTP {reg.status_code}\n{reg.text[:300]}",
                    {"email": email, "resultado": "falha_registro"},
                )
            passos.append("conta não existia; registrei")
            resp = self._login(email, senha)

        if resp.status_code != 200:
            self.sessao.token = None
            return ResultadoFerramenta(
                f"Falha no login como {email}: HTTP {resp.status_code}\n{resp.text[:300]}",
                {"email": email, "resultado": "falha_login"},
            )

        auth = resp.json().get("authentication", {})
        token = auth.get("token")
        bid = auth.get("bid")
        if not token:
            self.sessao.token = None
            return ResultadoFerramenta(
                f"Login respondeu 200 sem token, para {email}.", {"email": email, "resultado": "sem_token"})

        self.sessao.token = token
        self.sessao.usuario = email
        self.sessao.basket_id = bid
        passos.append(f"autenticado; token obtido (início {token[:10]}...)")

        # 2. coloca um item no carrinho, para ele ter conteúdo identificável.
        if bid is not None:
            try:
                add = requests.post(
                    f"{self.base_url}/api/BasketItems",
                    headers={"Authorization": f"Bearer {token}"},
                    json={"ProductId": PRODUTO_PADRAO, "BasketId": bid, "quantity": 1},
                    timeout=self.timeout,
                )
                passos.append("adicionei 1 item ao carrinho" if add.status_code in (200, 201)
                              else "carrinho já tinha item (ou add recusado)")
            except requests.RequestException:
                passos.append("não consegui adicionar item ao carrinho")

        resumo = f"Sessão pronta para {email}. " + "; ".join(passos) + "."
        if bid is not None:
            resumo += f"\nO carrinho DESTE usuário é /rest/basket/{bid}."
        resumo += ("\nO token autentica QUALQUER requisição seguinte (não só a do carrinho): "
                   "o objetivo pode incluir outros recursos indexados por id.")
        return ResultadoFerramenta(resumo, {"email": email, "basket_id": bid, "resultado": "sucesso"})
