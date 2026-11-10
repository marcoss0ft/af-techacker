# Roteiro do vídeo (até 10 minutos)

> Objetivo do vídeo (enunciado): demonstrar o funcionamento do agente e apresentar **pelo menos uma
> investigação completa**, da hipótese à conclusão, destacando as decisões do modelo e as
> intervenções do grupo.

**A investigação completa que vamos mostrar ao vivo: I2 (IDOR no carrinho)** — é a melhor para o
vídeo, porque a IA faz o pulo lógico, e o grupo intervém (rejeita, modifica, força). Mostra as duas
coisas que valem nota: o agente contribuindo e a supervisão agindo.

**Antes de gravar:**
- Lab no ar; Juice Shop fechado no navegador antes do restore.
- Ter abertas: 1 janela com o terminal do agente, 1 com o diagrama da arquitetura, 1 com o navegador (para a parte visual, se citar a I3).
- A IA é lenta (CPU). **Grave tudo e corte as esperas na edição**, com um aviso na tela ("[corte: ~1 min de inferência]"). Não acelere o áudio da fala.
- Falar em dupla ou revezar: deixa claro que os dois participaram.

---

## Bloco 1 — Abertura e objetivo (0:00–1:00)
- Quem são, disciplina, e o que é o trabalho em 2 frases: "um agente supervisionado que usa um LLM local (Qwen3 4B) para investigar o OWASP Juice Shop; avaliamos onde a IA ajuda e onde falha".
- Deixar claro o enquadramento: **não** é sobre achar vulnerabilidades, é sobre supervisão e análise crítica.

## Bloco 2 — Arquitetura e laboratório (1:00–2:30)
- Mostrar o diagrama: tudo roda no servidor do kit (`discorder`); Juice Shop e Ollama só em `127.0.0.1`; o grupo acessa por VPN + SSH.
- Mostrar, rápido, a prova de **isolamento** (os `curl` que falham de fora; o túnel que funciona) — 1 frase, sem se alongar.
- Mostrar o **restore** rodando e confirmando o estado inicial.
- Citar o agente: 3 ferramentas (`login`, `http_request`, `dir_enum`), com a **trava de escopo no código** e o **log** de cada passo. Dizer que há testes automáticos da trava.

## Bloco 3 — Investigação completa ao vivo: I2 (2:30–7:30)
Este é o coração do vídeo. Seguir o fluxo real:
1. **Hipótese** (10s): "o servidor entrega um carrinho pelo id, sem checar o dono — IDOR".
2. **Rodar o agente** com o objetivo. Mostrar o **turno 1**: a IA propõe `login` sozinha → autorizar. (Destacar: ela entendeu que precisava autenticar.)
3. **Turno 2**: a IA faz o pulo do IDOR sozinha (pedir um id diferente) → autorizar. (Destacar: raciocínio genuíno da IA.)
4. **A intervenção**: a IA quis concluir a partir de um carrinho **vazio** → o grupo **rejeita/modifica** e força `/rest/basket/1` → vem o carrinho de outro usuário (`UserId 1`). (Destacar: a supervisão melhorou a evidência.)
5. **A falha**: mostrar a IA **repetindo** a proposta e o **alerta de repetição** do agente. (Destacar: limitação do modelo; a decisão ficou com o humano.)
6. **Conclusão**: IDOR confirmado, apontando a evidência no **log**.

## Bloco 4 — Uma falha da IA e como lidamos (7:30–9:00)
- Mostrar um exemplo concreto (pode ser o da própria I2, ou o da I3): o agente não enxerga o XSS da tela; ou o agente confunde/repete.
- Explicar como o grupo detectou e o que fez (rejeitou, forçou, confirmou no navegador).
- Fechar a ideia central: **onde a IA ajudou, onde falhou, onde o humano foi necessário** — com a escala I1 (útil) → I2 (útil com supervisão) → I3 (pouco útil).

## Bloco 5 — Fechamento (9:00–9:45)
- 1 ou 2 lições: o que o agente de 4B consegue e não consegue; o papel da supervisão.
- Agradecer e encerrar. **Cronometrar: tem que ficar abaixo de 10 min.**

---

## Checklist antes de enviar o vídeo
- [ ] Mostra o lab funcionando e o restore
- [ ] Mostra UMA investigação completa (I2), da hipótese à conclusão
- [ ] Destaca decisões do modelo E intervenções do grupo
- [ ] Mostra pelo menos uma falha concreta da IA e como foi tratada
- [ ] Esperas de inferência cortadas, com aviso na tela
- [ ] Duração ≤ 10 min (cronometrado)
- [ ] Áudio audível; tela legível (fonte do terminal grande o suficiente)
