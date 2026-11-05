"""Agente supervisionado: loop objetivo → proposta da IA → decisão humana → execução → registro.

Uso:
    python agent.py --investigacao I2 --objetivo "Investigar se é possível acessar
                    a cesta de outro usuário trocando o id na API."

A cada passo o grupo autoriza (A), modifica (M), rejeita (R) ou finaliza (F) a proposta.
Tudo é registrado em logs/investigacao_<id>.jsonl.
"""

import argparse
import json
import textwrap
from pathlib import Path

import yaml

from llm import LLM
from registro import RegistroJSONL, sha256_texto
from tools import ForaDeEscopo, ParametrosInvalidos, carregar_ferramentas

BASE = Path(__file__).parent


def carregar_config() -> dict:
    return yaml.safe_load((BASE / "config.yaml").read_text(encoding="utf-8"))


def ler_decisao() -> str:
    """Lê A/M/R/F do grupo, repetindo até vir uma opção válida."""
    while True:
        escolha = input("  [A]utorizar  [M]odificar  [R]ejeitar  [F]inalizar > ").strip().upper()
        if escolha in ("A", "M", "R", "F"):
            return escolha
        print("  Opção inválida.")


def editar_parametros(parametros: dict) -> dict:
    """Permite ao grupo reescrever os parâmetros como JSON antes de executar."""
    print("  Parâmetros atuais:", json.dumps(parametros, ensure_ascii=False))
    print("  Digite o novo JSON de parâmetros (ou Enter para manter):")
    bruto = input("  > ").strip()
    if not bruto:
        return parametros
    try:
        novo = json.loads(bruto)
        if not isinstance(novo, dict):
            raise ValueError
        return novo
    except (json.JSONDecodeError, ValueError):
        print("  JSON inválido; mantendo os parâmetros originais.")
        return parametros


def mostrar_proposta(turno: int, proposta: dict) -> None:
    print(f"\n{'='*70}\nTURNO {turno}")
    print("Interpretação:", proposta.get("interpretacao", ""))
    fatos = proposta.get("fatos_observados") or []
    if fatos:
        print("Fatos observados:")
        for f in fatos:
            print("  -", f)
    print("Justificativa:", proposta.get("justificativa", ""))
    if proposta.get("acao") == "finalizar":
        print(">> O modelo propõe FINALIZAR.")
        print("Conclusão proposta:", proposta.get("conclusao", ""))
    else:
        print(f">> Ferramenta: {proposta.get('ferramenta')}")
        print("   Parâmetros:", json.dumps(proposta.get("parametros") or {}, ensure_ascii=False))


def resumir(texto: str, limite: int) -> str:
    return texto if len(texto) <= limite else texto[:limite] + f"\n[... truncado em {limite} chars ...]"


def main() -> None:
    ap = argparse.ArgumentParser(description="Agente supervisionado de testes de segurança.")
    ap.add_argument("--investigacao", required=True, help="Identificador, ex.: I1, I2, I3")
    ap.add_argument("--objetivo", required=True, help="Objetivo da investigação (uma frase)")
    args = ap.parse_args()

    cfg = carregar_config()
    ferramentas = carregar_ferramentas(cfg)
    prompt_sistema = (BASE / "prompts" / "sistema.md").read_text(encoding="utf-8")
    prompt_sha = sha256_texto(prompt_sistema)

    # Catálogo das ferramentas, inserido no prompt para o modelo saber o que existe.
    catalogo = "\n".join(f"- {f.nome}: {f.descricao}" for f in ferramentas.values())
    llm = LLM(cfg["modelo"], cfg["limites"], list(ferramentas.keys()))
    reg = RegistroJSONL(cfg["logs"]["dir"], args.investigacao)

    mensagens = [
        {"role": "system", "content": prompt_sistema},
        {"role": "user", "content":
            f"Ferramentas disponíveis:\n{catalogo}\n\nObjetivo da investigação:\n{args.objetivo}"},
    ]

    print(textwrap.dedent(f"""
        Investigação {args.investigacao} | sessão {reg.sessao}
        Objetivo: {args.objetivo}
        Ferramentas: {', '.join(ferramentas)}
        Lembrete: rode o restore.sh e confirme o estado inicial antes de começar.
    """))

    max_turnos = cfg["limites"]["max_turnos"]
    max_chars = cfg["limites"]["max_chars_saida_modelo"]

    for turno in range(1, max_turnos + 1):
        resultado = llm.propor(mensagens)

        # O modelo não produziu uma proposta válida nem após nova tentativa.
        if resultado.proposta is None:
            print(f"\nTURNO {turno}: o modelo não respondeu no formato exigido.")
            print("Resposta bruta:", resumir(resultado.resposta_bruta, 500))
            reg.registrar({
                "turno": turno, "objetivo": args.objetivo,
                "config": llm.config_para_log(prompt_sha),
                "resposta_bruta_modelo": resultado.resposta_bruta,
                "json_valido": False, "tentativas": resultado.tentativas,
                "erros_formato": resultado.erros_formato,
                "decisao_humana": "ABORTADO_FORMATO",
                "duracao_ms": {"modelo": resultado.duracao_ms},
                "tags": ["json_invalido", "falha_ia"],
            })
            if input("  Tentar mais um turno? [s/N] > ").strip().lower() != "s":
                break
            mensagens.append({"role": "user", "content": "Responda apenas com o JSON no formato exigido."})
            continue

        proposta = resultado.proposta
        mostrar_proposta(turno, proposta)

        registro = {
            "turno": turno, "objetivo": args.objetivo,
            "config": llm.config_para_log(prompt_sha),
            "resposta_bruta_modelo": resultado.resposta_bruta,
            "json_valido": True, "tentativas": resultado.tentativas,
            "justificativa_modelo": proposta.get("justificativa"),
            "interpretacao_modelo": proposta.get("interpretacao"),
            "fatos_observados": proposta.get("fatos_observados"),
            "duracao_ms": {"modelo": resultado.duracao_ms},
            "tags": [],
        }

        # Caminho "finalizar".
        if proposta.get("acao") == "finalizar":
            decisao = ler_decisao()
            if decisao == "F":
                conclusao_grupo = input("  Conclusão do grupo (Enter p/ aceitar a do modelo) > ").strip()
                registro.update({
                    "decisao_humana": "FINALIZADO",
                    "conclusao_modelo": proposta.get("conclusao"),
                    "decisao_grupo_pos_resultado": conclusao_grupo or "(aceita a do modelo)",
                })
                reg.registrar(registro)
                print("\nInvestigação encerrada. Preencha investigacoes/%s.md." % args.investigacao)
                break
            # O grupo não quer finalizar: devolve isso ao modelo e segue.
            motivo = input("  Por que não finalizar? (vai para o modelo) > ").strip()
            registro.update({"decisao_humana": "REJEITADO", "motivo_decisao": motivo or "continuar investigando"})
            reg.registrar(registro)
            mensagens += [
                {"role": "assistant", "content": resultado.resposta_bruta},
                {"role": "user", "content": f"Não vamos finalizar. {motivo}. Proponha a próxima ação."},
            ]
            continue

        # Caminho "usar_ferramenta".
        ferramenta = ferramentas[proposta["ferramenta"]]
        parametros = proposta.get("parametros") or {}
        decisao = ler_decisao()

        if decisao == "R":
            motivo = input("  Motivo da rejeição (vai para o modelo) > ").strip()
            registro.update({
                "ferramenta_proposta": ferramenta.nome, "parametros_propostos": parametros,
                "decisao_humana": "REJEITADO", "motivo_decisao": motivo or "(sem motivo)",
            })
            reg.registrar(registro)
            mensagens += [
                {"role": "assistant", "content": resultado.resposta_bruta},
                {"role": "user", "content":
                    f"A ação foi rejeitada pelo supervisor. Motivo: {motivo}. Proponha outra ação."},
            ]
            continue

        if decisao == "F":
            registro.update({"decisao_humana": "FINALIZADO",
                             "decisao_grupo_pos_resultado": input("  Conclusão do grupo > ").strip()})
            reg.registrar(registro)
            break

        if decisao == "M":
            parametros = editar_parametros(parametros)

        # Execução, com a trava de escopo dentro do wrapper.
        registro.update({
            "ferramenta_proposta": ferramenta.nome, "parametros_propostos": proposta.get("parametros"),
            "decisao_humana": "MODIFICADO" if decisao == "M" else "AUTORIZADO",
            "parametros_executados": parametros,
        })
        try:
            res = ferramenta.executar(parametros)
        except (ForaDeEscopo, ParametrosInvalidos) as e:
            print(f"  BLOQUEADO pela trava de escopo: {e}")
            registro.update({"bloqueio_escopo": str(e), "tags": ["fora_escopo"]})
            reg.registrar(registro)
            mensagens += [
                {"role": "assistant", "content": resultado.resposta_bruta},
                {"role": "user", "content":
                    f"A ação foi bloqueada pela política de escopo: {e}. Proponha uma ação dentro do alvo."},
            ]
            continue
        except Exception as e:  # falha de rede, timeout etc.
            print(f"  ERRO ao executar: {e}")
            registro.update({"erro_execucao": str(e), "tags": ["erro_execucao"]})
            reg.registrar(registro)
            mensagens += [
                {"role": "assistant", "content": resultado.resposta_bruta},
                {"role": "user", "content": f"A ferramenta falhou: {e}. Proponha outra ação."},
            ]
            continue

        # Saída completa em arquivo (com hash); resumo truncado ao modelo.
        caminho_raw, sha = reg.salvar_saida_bruta(turno, res.saida)
        print("  Resultado (início):")
        print(textwrap.indent(resumir(res.saida, 1200), "    "))

        # Decisão do grupo após ver o resultado (só para o log; NÃO vai para a IA).
        # Enter grava "seguir"; texto só quando a decisão foge do óbvio.
        decisao_pos = input("\n  Decisão do grupo (Enter = seguir) > ").strip()
        registro.update({
            "saida_resumo": resumir(res.saida, max_chars),
            "saida_arquivo": caminho_raw, "saida_sha256": sha,
            "parametros_executados": res.parametros_executados,
            "decisao_grupo_pos_resultado": decisao_pos or "seguir",
        })
        reg.registrar(registro)

        mensagens += [
            {"role": "assistant", "content": resultado.resposta_bruta},
            {"role": "user", "content":
                f"Resultado da ferramenta {ferramenta.nome}:\n{resumir(res.saida, max_chars)}\n\n"
                "Interprete o resultado e proponha a próxima ação, ou finalize se já for suficiente."},
        ]
    else:
        print(f"\nLimite de {max_turnos} turnos atingido. Investigação encerrada.")

    print(f"\nLog: {reg.caminho}")


if __name__ == "__main__":
    main()
