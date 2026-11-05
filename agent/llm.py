"""Cliente do Ollama: envia a conversa e devolve a proposta do modelo já validada."""

import json
import re
import time
from dataclasses import dataclass, field

import requests


class RespostaInvalida(Exception):
    pass


@dataclass
class ResultadoModelo:
    proposta: dict | None          # None quando o modelo não acertou o formato em nenhuma tentativa
    resposta_bruta: str            # última resposta recebida, sem nenhum tratamento
    tentativas: int
    duracao_ms: int
    erros_formato: list[str] = field(default_factory=list)
    tokens_gerados: int = 0


class LLM:
    def __init__(self, cfg_modelo: dict, cfg_limites: dict, nomes_ferramentas: list[str]):
        self.cfg = cfg_modelo
        self.max_tentativas = cfg_limites["max_tentativas_json"]
        self.nomes_ferramentas = nomes_ferramentas
        self.schema = self._montar_schema()

    def _montar_schema(self) -> dict:
        """Formato que o modelo é obrigado a seguir (o Ollama restringe a saída a este JSON Schema)."""
        return {
            "type": "object",
            "properties": {
                "interpretacao": {"type": "string"},
                "fatos_observados": {"type": "array", "items": {"type": "string"}},
                "justificativa": {"type": "string"},
                "acao": {"type": "string", "enum": ["usar_ferramenta", "finalizar"]},
                "ferramenta": {"type": "string", "enum": self.nomes_ferramentas},
                "parametros": {"type": "object"},
                "conclusao": {"type": "string"},
            },
            "required": ["interpretacao", "fatos_observados", "justificativa", "acao"],
        }

    def config_para_log(self, prompt_sistema_sha256: str) -> dict:
        return {
            "modelo": self.cfg["nome"],
            "think": self.cfg["think"],
            "temperature": self.cfg["temperature"],
            "seed": self.cfg["seed"],
            "num_ctx": self.cfg["num_ctx"],
            "prompt_sha256": prompt_sistema_sha256,
        }

    def propor(self, mensagens: list[dict]) -> ResultadoModelo:
        """Pede a próxima ação. Se o JSON vier inválido, avisa o modelo do erro e tenta de novo."""
        msgs = list(mensagens)
        erros: list[str] = []
        bruta = ""
        tokens = 0
        inicio = time.monotonic()

        for tentativa in range(1, self.max_tentativas + 1):
            bruta, tokens_resposta = self._chat(msgs)
            tokens += tokens_resposta
            try:
                proposta = self._validar(bruta)
                return ResultadoModelo(proposta, bruta, tentativa, self._ms_desde(inicio), erros, tokens)
            except RespostaInvalida as e:
                erros.append(str(e))
                msgs = msgs + [
                    {"role": "assistant", "content": bruta},
                    {"role": "user", "content": f"Sua resposta não seguiu o formato exigido: {e}. "
                                                "Responda novamente apenas com o JSON pedido."},
                ]

        return ResultadoModelo(None, bruta, self.max_tentativas, self._ms_desde(inicio), erros, tokens)

    def _chat(self, mensagens: list[dict]) -> tuple[str, int]:
        resposta = requests.post(
            f"{self.cfg['url']}/api/chat",
            json={
                "model": self.cfg["nome"],
                "messages": mensagens,
                "stream": False,
                "think": self.cfg["think"],
                "format": self.schema,
                "options": {
                    "temperature": self.cfg["temperature"],
                    "seed": self.cfg["seed"],
                    "num_ctx": self.cfg["num_ctx"],
                },
            },
            timeout=self.cfg["timeout_s"],
        )
        resposta.raise_for_status()
        dados = resposta.json()
        return dados["message"]["content"], dados.get("eval_count", 0)

    def _validar(self, bruta: str) -> dict:
        # Garantia extra caso algum bloco de "pensamento" escape para o conteúdo.
        texto = re.sub(r"<think>.*?</think>", "", bruta, flags=re.DOTALL).strip()
        try:
            proposta = json.loads(texto)
        except json.JSONDecodeError as e:
            raise RespostaInvalida(f"JSON malformado ({e.msg})")

        if not isinstance(proposta, dict):
            raise RespostaInvalida("a resposta não é um objeto JSON")
        for campo in ("interpretacao", "justificativa"):
            if not isinstance(proposta.get(campo), str):
                raise RespostaInvalida(f"campo '{campo}' ausente ou não é texto")
        if not isinstance(proposta.get("fatos_observados"), list):
            raise RespostaInvalida("campo 'fatos_observados' ausente ou não é lista")

        acao = proposta.get("acao")
        if acao == "usar_ferramenta":
            if proposta.get("ferramenta") not in self.nomes_ferramentas:
                raise RespostaInvalida(f"ferramenta inexistente: {proposta.get('ferramenta')!r}")
            if not isinstance(proposta.get("parametros"), dict):
                raise RespostaInvalida("campo 'parametros' ausente ou não é objeto")
        elif acao == "finalizar":
            if not isinstance(proposta.get("conclusao"), str):
                raise RespostaInvalida("ao finalizar, o campo 'conclusao' é obrigatório")
        else:
            raise RespostaInvalida(f"ação desconhecida: {acao!r}")

        return proposta

    @staticmethod
    def _ms_desde(inicio: float) -> int:
        return int((time.monotonic() - inicio) * 1000)
