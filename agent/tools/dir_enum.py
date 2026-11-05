"""Descoberta de rotas: testa uma lista pré-definida de caminhos no Juice Shop.

Problema específico do Juice Shop: é uma SPA. Para quase qualquer caminho de página
ele devolve 200 com o mesmo index.html, o que geraria falso positivo. Por isso a
ferramenta compara cada resposta com a de um caminho que sabidamente não existe
(uma "linha de base") e só destaca o que difere dela.
"""

import time
from urllib.parse import urlsplit

import requests

from .base import ForaDeEscopo, ParametrosInvalidos, ResultadoFerramenta, recusar_destino_diferente


class DirEnum:
    nome = "dir_enum"
    descricao = (
        "Testa caminhos de uma lista pré-definida no Juice Shop e informa, para cada um, "
        "o código de resposta e o tamanho do corpo, destacando os que diferem da linha de base "
        "(resposta de um caminho inexistente). Parâmetro opcional: caminhos (subconjunto da "
        "lista configurada). O endereço do servidor e a lista são fixos."
    )

    def __init__(self, cfg_alvo: dict, cfg_limites: dict, cfg_dir: dict):
        self.base_url = cfg_alvo["base_url"].rstrip("/")
        self.host = cfg_alvo["host"]
        self.portas_permitidas = set(cfg_alvo["portas_permitidas"])
        self.timeout = cfg_limites["timeout_ferramenta_s"]
        self.wordlist = list(cfg_dir["wordlist"])
        self.max_caminhos = cfg_dir["max_caminhos"]
        self.intervalo = cfg_dir["intervalo_ms"] / 1000

    def validar(self, p: dict) -> list[str]:
        """Confere escopo e monta a lista de caminhos a testar, sem acessar a rede."""
        recusar_destino_diferente(p, self.host)

        caminhos = p.get("caminhos")
        if caminhos is None:
            caminhos = list(self.wordlist)
        elif not isinstance(caminhos, list):
            raise ParametrosInvalidos("'caminhos' deve ser uma lista")

        validados = []
        for caminho in caminhos:
            if not isinstance(caminho, str) or not caminho.startswith("/"):
                raise ParametrosInvalidos(f"caminho inválido: {caminho!r} (deve começar com '/')")
            if "://" in caminho or caminho.startswith("//"):
                raise ForaDeEscopo(f"caminho com endereço completo: {caminho!r}")
            # O caminho só pode ser escolhido da lista pré-definida.
            if caminho not in self.wordlist:
                raise ForaDeEscopo(f"caminho fora da lista pré-definida: {caminho!r}")
            destino = urlsplit(self.base_url + caminho)
            if destino.hostname != self.host or destino.port not in self.portas_permitidas:
                raise ForaDeEscopo(f"destino resultante fora do escopo: {caminho!r}")
            validados.append(caminho)

        if len(validados) > self.max_caminhos:
            raise ParametrosInvalidos(f"{len(validados)} caminhos pedidos; o máximo é {self.max_caminhos}")
        return validados

    def _medir(self, caminho: str) -> tuple[int, int]:
        r = requests.get(self.base_url + caminho, allow_redirects=False, timeout=self.timeout)
        return r.status_code, len(r.content)

    def executar(self, p: dict) -> ResultadoFerramenta:
        caminhos = self.validar(p)

        # Linha de base: caminho aleatório que quase certamente não existe.
        base_status, base_tam = self._medir("/caminho-inexistente-linha-de-base-af")

        linhas = [f"linha de base (caminho inexistente): HTTP {base_status}, {base_tam} bytes", ""]
        destaques = 0
        for caminho in caminhos:
            status, tam = self._medir(caminho)
            difere = (status != base_status) or (abs(tam - base_tam) > 64)
            marca = "  <-- difere da base" if difere else ""
            if difere:
                destaques += 1
            linhas.append(f"{caminho:<45} HTTP {status}  {tam} bytes{marca}")
            time.sleep(self.intervalo)

        linhas.append("")
        linhas.append(f"{destaques} de {len(caminhos)} caminhos diferem da linha de base.")
        return ResultadoFerramenta("\n".join(linhas), {"caminhos": caminhos})
