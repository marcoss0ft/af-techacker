"""Peças comuns às ferramentas do agente."""

from dataclasses import dataclass


class ForaDeEscopo(Exception):
    """Pedido para um host ou porta fora do escopo. É recusado antes de qualquer acesso à rede."""


class ParametrosInvalidos(Exception):
    """Parâmetros com formato errado ou opção não permitida."""


@dataclass
class ResultadoFerramenta:
    saida: str                   # texto completo produzido pela ferramenta
    parametros_executados: dict  # o que de fato foi executado, depois da validação


# Nomes de parâmetro com que o modelo poderia tentar trocar o destino.
CAMPOS_DE_DESTINO = ("host", "alvo", "target", "url", "ip")


def recusar_destino_diferente(parametros: dict, host_permitido: str) -> None:
    """O destino vem do config.yaml. Se o modelo tentar informar outro, a chamada é recusada."""
    for campo in CAMPOS_DE_DESTINO:
        valor = parametros.get(campo)
        if valor is not None and str(valor) != host_permitido:
            raise ForaDeEscopo(f"o parâmetro '{campo}' aponta para {valor!r}; o único alvo permitido é {host_permitido}")
