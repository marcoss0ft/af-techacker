"""Ferramentas disponíveis ao agente. Só o que está registrado aqui pode ser escolhido pelo modelo."""

from .base import ForaDeEscopo, ParametrosInvalidos, ResultadoFerramenta, Sessao
from .dir_enum import DirEnum
from .http_request import HttpRequest
from .login import Login


def carregar_ferramentas(cfg: dict) -> dict:
    sessao = Sessao()  # estado compartilhado: o token definido pelo login é usado pelo http_request
    ferramentas = [
        Login(cfg["alvo"], cfg["limites"], sessao),
        HttpRequest(cfg["alvo"], cfg["limites"], sessao),
        DirEnum(cfg["alvo"], cfg["limites"], cfg["descoberta_rotas"]),
    ]
    return {f.nome: f for f in ferramentas}


__all__ = ["carregar_ferramentas", "ForaDeEscopo", "ParametrosInvalidos", "ResultadoFerramenta", "Sessao"]
