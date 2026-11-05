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
    print("A inferência na CPU é lenta; a resposta aparece aos poucos abaixo.\n")

    # stream=True: o texto chega aos poucos, então dá para ver o progresso e não estoura timeout.
    resposta = requests.post(
        f"{cfg['url']}/api/chat",
        json={
            "model": cfg["nome"],
            "messages": [
                {"role": "system", "content": prompt_sistema},
                {"role": "user", "content": f"Plano de testes do grupo:\n\n{plano}"},
            ],
            "stream": True,
            "think": cfg["think"],
            "options": {"temperature": cfg["temperature"], "seed": cfg["seed"], "num_ctx": cfg["num_ctx"]},
        },
        timeout=(30, 1800),   # 30s para conectar, até 30 min entre pedaços da resposta
        stream=True,
    )
    resposta.raise_for_status()

    partes = []
    for linha in resposta.iter_lines():
        if not linha:
            continue
        pedaco = json.loads(linha)
        trecho = pedaco.get("message", {}).get("content", "")
        if trecho:
            print(trecho, end="", flush=True)   # mostra a resposta chegando
            partes.append(trecho)
        if pedaco.get("done"):
            break
    texto = "".join(partes)
    print()

    carimbo = datetime.now().astimezone()
    destino = BASE.parent / "logs" / f"revisao_llm_{carimbo:%Y%m%d_%H%M}.txt"
    destino.write_text(
        f"# Revisão do plano pelo {cfg['nome']} — {carimbo.isoformat(timespec='seconds')}\n"
        f"# Parâmetros: {json.dumps({k: cfg[k] for k in ('think', 'temperature', 'seed', 'num_ctx')})}\n\n"
        f"{texto}\n",
        encoding="utf-8",
    )

    print(f"\n--- Resposta salva em: {destino}")
    print("Agora: leia as sugestões e preencha a tabela em planejamento/revisao_llm.md")
    print("(para cada uma: aceita / modificada / rejeitada + justificativa do grupo).")


if __name__ == "__main__":
    main()
