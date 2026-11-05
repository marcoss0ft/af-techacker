"""Testes da trava de escopo. Não acessam a rede: tudo é recusado na validação.

Uso: python -m unittest test_escopo -v
"""

import unittest
from pathlib import Path

import yaml

from tools import ForaDeEscopo, ParametrosInvalidos, carregar_ferramentas

CFG = yaml.safe_load((Path(__file__).parent / "config.yaml").read_text(encoding="utf-8"))
FERRAMENTAS = carregar_ferramentas(CFG)
HTTP = FERRAMENTAS["http_request"]
DIR = FERRAMENTAS["dir_enum"]


class TestHttpRequest(unittest.TestCase):
    def test_caminho_normal_e_aceito(self):
        metodo, url, _, _ = HTTP.validar({"method": "get", "path": "/"})
        self.assertEqual((metodo, url), ("GET", "http://127.0.0.1:3000/"))

    def test_url_completa_externa_e_recusada(self):
        with self.assertRaises(ForaDeEscopo):
            HTTP.validar({"path": "http://example.com/"})

    def test_url_sem_esquema_e_recusada(self):
        with self.assertRaises(ForaDeEscopo):
            HTTP.validar({"path": "//example.com/"})

    def test_parametro_host_diferente_e_recusado(self):
        with self.assertRaises(ForaDeEscopo):
            HTTP.validar({"path": "/", "host": "10.0.80.1"})

    def test_truque_com_arroba_continua_no_alvo(self):
        _, url, _, _ = HTTP.validar({"path": "/@example.com"})
        self.assertTrue(url.startswith("http://127.0.0.1:3000/"))

    def test_cabecalho_host_e_descartado(self):
        _, _, headers, _ = HTTP.validar({"path": "/", "headers": {"Host": "example.com", "Accept": "*/*"}})
        self.assertEqual(headers, {"Accept": "*/*"})

    def test_metodo_desconhecido_e_recusado(self):
        with self.assertRaises(ParametrosInvalidos):
            HTTP.validar({"method": "CONNECT", "path": "/"})


class TestDirEnum(unittest.TestCase):
    def test_sem_parametro_usa_a_lista_toda(self):
        caminhos = DIR.validar({})
        self.assertEqual(caminhos, CFG["descoberta_rotas"]["wordlist"])

    def test_subconjunto_da_lista_e_aceito(self):
        self.assertEqual(DIR.validar({"caminhos": ["/ftp", "/metrics"]}), ["/ftp", "/metrics"])

    def test_caminho_fora_da_lista_e_recusado(self):
        with self.assertRaises(ForaDeEscopo):
            DIR.validar({"caminhos": ["/qualquer-coisa-inventada"]})

    def test_url_completa_e_recusada(self):
        # Recusada de um jeito ou de outro: não começa com '/', e nem está na lista.
        with self.assertRaises((ForaDeEscopo, ParametrosInvalidos)):
            DIR.validar({"caminhos": ["http://example.com/ftp"]})

    def test_url_disfarcada_com_barra_e_recusada(self):
        with self.assertRaises(ForaDeEscopo):
            DIR.validar({"caminhos": ["//example.com/ftp"]})

    def test_outro_alvo_e_recusado(self):
        with self.assertRaises(ForaDeEscopo):
            DIR.validar({"host": "10.0.80.1"})

    def test_caminho_sem_barra_e_recusado(self):
        with self.assertRaises(ParametrosInvalidos):
            DIR.validar({"caminhos": ["ftp"]})


if __name__ == "__main__":
    unittest.main()
