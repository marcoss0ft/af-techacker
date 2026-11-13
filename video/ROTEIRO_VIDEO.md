# Roteiro do vídeo — versão mínima (nota máxima, sem excesso)

O enunciado exige só isto no vídeo (até 10 min):
1. demonstrar o **funcionamento do agente**;
2. **uma investigação completa**, da hipótese à conclusão;
3. destacar as **decisões do modelo** e as **intervenções do grupo**;
4. duração **≤ 10 minutos**.

A gravação da **I2 (IDOR)** que já temos cobre os quatro. Este roteiro usa essa gravação, com uma
abertura e um fecho curtos. Alvo de duração: **5 a 7 minutos**.

**Como montar:** grave a narração (voiceover) lendo os textos abaixo por cima das imagens. Corte as
esperas da IA (coloque um aviso "[corte]" na tela). Não precisa aparecer o rosto.

---

## Bloco 1 — Abertura (~0:40) · imagem: o diagrama (`video/arquitetura.svg`)
> "Somos o Grupo 7, Vinicius e Marcos, da disciplina Tecnologias Hackers. Neste trabalho
> desenvolvemos um agente supervisionado que usa um modelo de linguagem local, o Qwen3 4B, para
> investigar o OWASP Juice Shop. O objetivo não é achar o máximo de vulnerabilidades, mas avaliar
> onde a IA ajuda, onde ela falha, e quando a supervisão humana é necessária. Tudo roda no servidor
> do kit: o alvo, o modelo e o agente ficam fechados em localhost, e a gente acessa por VPN e SSH."

## Bloco 2 — A investigação I2 completa (~4 a 5 min) · imagem: a gravação da I2
Narre por cima do vídeo, acompanhando o que aparece na tela:

- **Hipótese (ao começar):**
  > "A nossa hipótese: o servidor entrega um carrinho pelo número do id, sem checar se ele é seu —
  > a falha chamada IDOR."

- **Turno do login:**
  > "Damos só o objetivo ao agente. Repare que ele, sozinho, propõe fazer login primeiro — entendeu
  > que precisava estar autenticado. A gente autoriza."

- **Turno do primeiro teste (basket):**
  > "Agora o agente faz o raciocínio central sozinho: 'meu carrinho é o número 6, vou pedir um id
  > diferente pra ver se acesso o de outro usuário'. Isso é a contribuição boa da IA."

- **A intervenção (o carrinho vazio → forçar o /rest/basket/1):**
  > "Aqui entra a supervisão. O modelo tentou concluir a vulnerabilidade a partir de um carrinho
  > vazio — uma conclusão sem evidência. A gente rejeita e força o carrinho número 1. E o resultado:
  > logados como o usuário 25, recebemos o carrinho do usuário 1. IDOR confirmado, com evidência real
  > no log."

- **O segundo recurso e o loop:**
  > "Tentamos levar o agente a um segundo recurso. Mesmo pedindo, ele repete a proposta anterior — o
  > nosso detector de repetição avisa. Então a gente força o teste nos endereços, e esse endpoint
  > responde com bloqueio: o IDOR não é uniforme, alguns recursos vazam e outros são protegidos."

- **Conclusão:**
  > "Concluímos: IDOR confirmado no carrinho, evidência no log; o segundo recurso é protegido; e a IA
  > precisou de supervisão para a qualidade da evidência e para ampliar o escopo."

## Bloco 3 — Fecho (~0:40) · imagem: o slide de síntese (`video/slides_investigacoes.html`, último slide)
> "Nas três investigações, a IA foi útil no reconhecimento, útil com supervisão no IDOR, e pouco útil
> no XSS, onde ela nem enxerga a falha, porque só vê a resposta crua. A lição é que, com um modelo
> local pequeno, o valor está no fluxo supervisionado: a IA sugere e acelera, mas a condução, a
> validação e a responsabilidade ficam com a gente. Obrigado."

---

## Checklist antes de enviar
- [ ] Aparece o agente rodando (o ciclo propor → decidir → executar)
- [ ] Uma investigação completa (I2), da hipótese à conclusão
- [ ] Dá pra ver uma decisão do modelo E uma intervenção do grupo (autorizar / rejeitar / forçar)
- [ ] Esperas da IA cortadas, com aviso na tela
- [ ] Duração ≤ 10 min (de preferência 5–7)
- [ ] Áudio audível, terminal legível
