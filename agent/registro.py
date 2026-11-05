"""Registro das investigações em JSONL: uma linha por turno, gravada na hora."""

import hashlib
import json
import os
from datetime import datetime
from pathlib import Path


def agora_iso() -> str:
    """Horário local com offset (ex.: 2026-11-05T14:02:31-03:00)."""
    return datetime.now().astimezone().isoformat(timespec="seconds")


def sha256_texto(texto: str) -> str:
    return hashlib.sha256(texto.encode("utf-8")).hexdigest()


class RegistroJSONL:
    def __init__(self, dir_logs: str, investigacao: str):
        self.investigacao = investigacao
        self.sessao = f"{investigacao}-{datetime.now().astimezone():%Y%m%dT%H%M%S}"
        self.dir = Path(dir_logs)
        self.dir_raw = self.dir / "raw"
        self.dir_raw.mkdir(parents=True, exist_ok=True)
        # Um arquivo por investigação; várias sessões se acumulam nele, separadas pelo campo "sessao".
        self.caminho = self.dir / f"investigacao_{investigacao}.jsonl"

    def registrar(self, registro: dict) -> None:
        linha = {
            "investigacao": self.investigacao,
            "sessao": self.sessao,
            "timestamp": agora_iso(),
            **registro,
        }
        with open(self.caminho, "a", encoding="utf-8") as f:
            f.write(json.dumps(linha, ensure_ascii=False) + "\n")
            f.flush()
            os.fsync(f.fileno())  # se o processo cair, o turno já está no disco

    def salvar_saida_bruta(self, turno: int, texto: str) -> tuple[str, str]:
        """Guarda a saída completa da ferramenta e devolve (caminho relativo, sha256)."""
        nome = f"{self.sessao}_turno{turno:02d}.txt"
        caminho = self.dir_raw / nome
        caminho.write_text(texto, encoding="utf-8")
        return f"logs/raw/{nome}", sha256_texto(texto)
