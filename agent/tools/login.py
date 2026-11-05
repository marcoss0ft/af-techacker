"""Ferramenta de login: autentica com a conta de teste e guarda o token na sessão.

As credenciais vêm de credenciais.local.yaml (fora do git), não do modelo nem do log.
O modelo só decide QUANDO logar; o e-mail e a senha são fixos, como o host.
"""

from pathlib import Path

import requests
import yaml

from .base import ParametrosInvalidos, ResultadoFerramenta, Sessao

ARQ_CRED = Path(__file__).resolve().parent.parent / "credenciais.local.yaml"


class Login:
    nome = "login"
    descricao = (
        "Autentica no Juice Shop com a conta de teste do grupo e guarda o token de sessão, "
        "para que as requisições seguintes sejam feitas como esse usuário. Sem parâmetros: "
        "o e-mail e a senha são fixos (configurados fora do modelo)."
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

    def executar(self, p: dict) -> ResultadoFerramenta:
        email, senha = self._credenciais()
        resposta = requests.post(
            f"{self.base_url}/rest/user/login",
            json={"email": email, "password": senha},
            timeout=self.timeout,
        )
        if resposta.status_code != 200:
            # A senha nunca aparece na saída; só o status e um trecho do corpo.
            corpo = resposta.text[:300]
            self.sessao.token = None
            return ResultadoFerramenta(
                f"Falha no login como {email}: HTTP {resposta.status_code}\n{corpo}",
                {"email": email, "resultado": "falha"},
            )

        token = resposta.json().get("authentication", {}).get("token")
        if not token:
            self.sessao.token = None
            return ResultadoFerramenta(
                f"Login respondeu 200, mas sem token, para {email}.",
                {"email": email, "resultado": "sem_token"},
            )

        self.sessao.token = token
        self.sessao.usuario = email
        # No log/saída, só o início do token, para não vazar o token inteiro.
        return ResultadoFerramenta(
            f"Autenticado como {email}. Token obtido (início: {token[:12]}...). "
            "As próximas requisições usarão este token.",
            {"email": email, "resultado": "sucesso"},
        )
