"""Ferramenta que interage diretamente com o Juice Shop por HTTP."""

from urllib.parse import urlsplit

import requests

from .base import ForaDeEscopo, ParametrosInvalidos, ResultadoFerramenta, recusar_destino_diferente

METODOS = {"GET", "POST", "PUT", "PATCH", "DELETE", "HEAD", "OPTIONS"}


class HttpRequest:
    nome = "http_request"
    descricao = (
        "Faz uma requisição HTTP ao Juice Shop e devolve status, cabeçalhos e corpo da resposta. "
        "Parâmetros: method (GET, POST, PUT, PATCH, DELETE, HEAD ou OPTIONS); "
        "path (caminho começando com '/'); headers (objeto, opcional); "
        "body (texto ou objeto JSON, opcional). O endereço do servidor é fixo: informe só o caminho."
    )

    def __init__(self, cfg_alvo: dict, cfg_limites: dict):
        self.base_url = cfg_alvo["base_url"].rstrip("/")
        self.host = cfg_alvo["host"]
        self.portas_permitidas = set(cfg_alvo["portas_permitidas"])
        self.timeout = cfg_limites["timeout_ferramenta_s"]
        self.max_bytes = cfg_limites["max_bytes_resposta_http"]

    def validar(self, p: dict) -> tuple[str, str, dict, object]:
        """Confere escopo e formato sem tocar na rede. Devolve (método, url, headers, body)."""
        recusar_destino_diferente(p, self.host)

        metodo = str(p.get("method", "GET")).upper()
        if metodo not in METODOS:
            raise ParametrosInvalidos(f"método não permitido: {metodo!r}")

        caminho = p.get("path")
        if not isinstance(caminho, str) or not caminho:
            raise ParametrosInvalidos("o parâmetro 'path' é obrigatório")
        if "://" in caminho or caminho.startswith("//"):
            raise ForaDeEscopo(f"'path' contém um endereço completo ({caminho!r}); só caminhos do Juice Shop são aceitos")
        if not caminho.startswith("/"):
            raise ParametrosInvalidos("'path' deve começar com '/'")

        # Confere o destino final já montado, e não só o texto do parâmetro.
        url = self.base_url + caminho
        destino = urlsplit(url)
        if destino.hostname != self.host or destino.port not in self.portas_permitidas:
            raise ForaDeEscopo(f"destino resultante {destino.hostname}:{destino.port} fora do escopo")

        headers = p.get("headers") or {}
        if not isinstance(headers, dict):
            raise ParametrosInvalidos("'headers' deve ser um objeto")
        headers = {str(k): str(v) for k, v in headers.items() if str(k).lower() != "host"}

        return metodo, url, headers, p.get("body")

    def executar(self, p: dict) -> ResultadoFerramenta:
        metodo, url, headers, body = self.validar(p)

        envio = {}
        if isinstance(body, (dict, list)):
            envio["json"] = body
        elif body is not None:
            envio["data"] = str(body).encode("utf-8")

        resposta = requests.request(
            metodo, url, headers=headers, allow_redirects=False,  # redirecionamento não é seguido
            timeout=self.timeout, stream=True, **envio,
        )
        conteudo = resposta.raw.read(self.max_bytes + 1, decode_content=True)
        resposta.close()
        truncado = len(conteudo) > self.max_bytes
        corpo = conteudo[: self.max_bytes].decode("utf-8", errors="replace")

        linhas = [f"HTTP {resposta.status_code} {resposta.reason}"]
        linhas += [f"{k}: {v}" for k, v in resposta.headers.items()]
        linhas += ["", corpo]
        if truncado:
            linhas.append(f"[... corpo truncado em {self.max_bytes} bytes ...]")

        executados = {"method": metodo, "path": url[len(self.base_url):], "headers": headers}
        if body is not None:
            executados["body"] = body
        return ResultadoFerramenta("\n".join(linhas), executados)
