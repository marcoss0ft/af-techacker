"""Ferramentas disponíveis ao agente. Só o que está registrado aqui pode ser escolhido pelo modelo."""

from .base import ForaDeEscopo, ParametrosInvalidos, ResultadoFerramenta
from .dir_enum import DirEnum
from .http_request import HttpRequest


def carregar_ferramentas(cfg: dict) -> dict:
    ferramentas = [
        HttpRequest(cfg["alvo"], cfg["limites"]),
        DirEnum(cfg["alvo"], cfg["limites"], cfg["descoberta_rotas"]),
    ]
    return {f.nome: f for f in ferramentas}


__all__ = ["carregar_ferramentas", "ForaDeEscopo", "ParametrosInvalidos", "ResultadoFerramenta"]
