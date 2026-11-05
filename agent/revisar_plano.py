"""Fase 3b: envia o plano de testes do grupo ao LLM local para revisão e salva o resultado.

A conversa é registrada em logs/, como evidência de que a revisão foi feita pela IA.
O grupo lê a resposta e preenche a tabela de decisões em planejamento/revisao_llm.md.

Uso: python revisar_plano.py
"""

import json
from datetime import datetime
from pathlib import Path

import requests
import yaml

BASE = Path(__file__).parent
PLANO = BASE.parent / "planejamento" / "plano_testes_grupo.md"


def main() -> None:
    cfg = yaml.safe_load((BASE / "config.yaml").read_text(encoding="utf-8"))["modelo"]
    prompt_sistema = (BASE / "prompts" / "revisao.md").read_text(encoding="utf-8")
    plano = PLANO.read_text(encoding="utf-8")

    print(f"Enviando o plano ({len(plano)} caracteres) ao modelo {cfg['nome']}...")
    print("A inferência na CPU pode levar alguns minutos. Aguarde.\n")

    resposta = requests.post(
        f"{cfg['url']}/api/chat",
        json={
            "model": cfg["nome"],
            "messages": [
                {"role": "system", "content": prompt_sistema},
                {"role": "user", "content": f"Plano de testes do grupo:\n\n{plano}"},
            ],
            "stream": False,
            "think": cfg["think"],
            "options": {"temperature": cfg["temperature"], "seed": cfg["seed"], "num_ctx": cfg["num_ctx"]},
        },
        timeout=cfg["timeout_s"],
    )
    resposta.raise_for_status()
    dados = resposta.json()
    texto = dados["message"]["content"]

    carimbo = datetime.now().astimezone()
    destino = BASE.parent / "logs" / f"revisao_llm_{carimbo:%Y%m%d_%H%M}.txt"
    destino.write_text(
        f"# Revisão do plano pelo {cfg['nome']} — {carimbo.isoformat(timespec='seconds')}\n"
        f"# Parâmetros: {json.dumps({k: cfg[k] for k in ('think', 'temperature', 'seed', 'num_ctx')})}\n\n"
        f"{texto}\n",
        encoding="utf-8",
    )

    print(texto)
    print(f"\n--- Resposta salva em: {destino}")
    print("Agora: leia as sugestões e preencha a tabela em planejamento/revisao_llm.md")
    print("(para cada uma: aceita / modificada / rejeitada + justificativa do grupo).")


if __name__ == "__main__":
    main()
