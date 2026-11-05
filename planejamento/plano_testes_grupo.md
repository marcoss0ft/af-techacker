# Plano de testes do grupo

> Estratégia definida pelo grupo a partir da exploração manual (`observacoes_iniciais.md`) e da
> avaliação de segurança do Juice Shop. As três investigações cobrem situações distintas:
> achar o que está escondido (I1), furar controle de acesso (I2) e injetar entrada (I3).

## Resumo e justificativa das escolhas

| # | Tema | Investigação escolhida | Por que esta, e não outra do mesmo tema |
|---|---|---|---|
| I1 | Reconhecimento e enumeração | Rotas e recursos não listados nos menus | Observado ao vivo: `/score-board` acessível direto pela URL e `/administration` com 403. Pergunta clara e curta; é a que mais pede uma ferramenta de descoberta. Preferida a "erros verbosos", que renderia uma investigação difusa. |
| I2 | Autenticação / autorização | IDOR: acessar recurso de outro usuário trocando o id | Broken Access Control é a classe mais presente e de maior impacto no Juice Shop. Teste direto (trocar id), confirma/refuta nítidos, usa só `http_request`. Preferida ao JWT, que exigiria ferramenta extra e testes mais frágeis para um resultado limpo em ~15 passos. |
| I3 | Tratamento de entradas | XSS refletido na busca | Observação mais forte do grupo: entrada com `<b>` refletida no título do resultado. Hipótese e evidência ficam na própria resposta do servidor. Preferida à SQLi no login, cujo "confirma" (logar sem senha) é mais indireto. |

**Ferramentas que estas escolhas exigem:**
- `http_request` — cobre I2 e I3 por completo e parte do I1. Fixa.
- **descoberta de rotas** (wordlist pequena) — motivada pelo I1; a implementar.
- leitor de JWT — descartado, porque o I2 ficou com IDOR, e não com o token.
- nmap — **descartado e não integrado ao agente.** Como o alvo e a porta já são conhecidos, ele não contribui para nenhuma das três hipóteses. Optamos por não oferecer ao modelo uma ferramenta sem uso no plano. Decisão a registrar no relatório (critério de seleção de ferramentas).

**Conjunto final de ferramentas do agente:** `http_request` e `dir_enum` — duas ferramentas, ambas interagindo com o Juice Shop.

---

## I1 — Reconhecimento e enumeração

**Aspecto investigado e por quê:** quais páginas, endpoints e arquivos existem sem aparecer em nenhum menu, e se os que respondem "não autorizado" são de fato barrados no servidor. Observado em `observacoes_iniciais.md`: `/score-board` abriu direto pela URL; `/administration` retornou 403.

**Hipótese 1:** acredito que a aplicação expõe páginas e recursos que funcionam mas não aparecem em nenhum menu, alcançáveis por quem conhece o caminho.
- **Porque observei (por volta das 08:23):**
  - `/#/score-board` abriu o placar de desafios ao ser digitado direto na URL, sem estar no menu (print `planejamento/prints/score_board_aberto.png`, com a URL visível).
  - O menu lateral não lista "Score Board" nem "Administration" (print `planejamento/prints/0822_menu_lateral_e_feedback.jpg`).
  - `/#/administration` retornou "403 - You are not allowed to access this page" (print `planejamento/prints/0823_administration_403.jpg`).
- **Como testar:** com a `dir_enum`, o agente verifica uma lista de endereços de servidor (ex.: `/ftp`, `/rest/...`, arquivos de backup) e vê quais respondem; `http_request` confirma caso a caso o que for interessante.
- **Confirma se:** existem endereços que respondem com conteúdo próprio (diferente da página padrão da SPA), sem estar em nenhum menu.
- **Refuta se:** todos os caminhos de fora do menu retornam 404 ou a mesma página padrão da SPA.

**Ferramenta:** `dir_enum` (principal); `http_request` para confirmar caso a caso.
**Evidência esperada no log:** código de resposta e tamanho de cada caminho testado, destacando os que diferem da linha de base.
**Nota sobre as rotas `/#/...`:** as rotas que observamos à mão (`/#/score-board`, `/#/administration`) são rotas de **front-end** (o `#` indica roteamento no navegador); o `http_request`/`dir_enum` atuam sobre endereços de **servidor**. Por isso a parte do agente foca em caminhos de servidor não listados (ex.: `/ftp`), enquanto as rotas de tela ficam como observação manual.
**Previsão sobre a IA:** achamos que o agente vai ajudar bastante aqui, porque descobrir endereços de servidor é fazer muitas requisições, que é o que ele faz bem com a `dir_enum`. Esperamos que ele encontre rotas que não vimos à mão. O risco é ele confundir os 200 genéricos da SPA com rotas reais, ou insistir em caminhos que não existem; aí a nossa supervisão vai precisar filtrar o que é achado de verdade.

---

## I2 — Autenticação ou autorização

**Aspecto investigado e por quê:** se o servidor confere que um recurso pertence ao usuário autenticado, ou se devolve o recurso de qualquer id informado (IDOR). Base: a avaliação apontou IDOR como a classe dominante no Juice Shop.

**Hipótese 1:** acredito que o servidor entrega um carrinho pelo número informado na URL (`/rest/basket/<id>`), sem checar se ele pertence ao usuário autenticado (IDOR).
- **Porque observei (16:01):** ao abrir o carrinho logado com a conta de teste, a requisição `GET /rest/basket/6` devolveu `"id": 6` e `"UserId": 25` — ou seja, o carrinho é identificado por um número pequeno e sequencial, e a resposta o liga a um usuário específico (print `planejamento/prints/i2_basket_id.png`).
- **Como testar:** com o `http_request`, autenticado como a conta de teste, pedir `/rest/basket/5` (e outros números vizinhos) e comparar o `UserId` da resposta com o nosso (25).
- **Confirma se:** a resposta traz um carrinho com `UserId` diferente de 25, ou produtos que não são nossos.
- **Refuta se:** a resposta é 401/403, vazia, ou devolve apenas o nosso próprio carrinho.

**Ferramenta:** `http_request`.
**Evidência esperada no log:** a requisição com o id trocado, o código de resposta e o `UserId`/produtos retornados que não são da conta de teste.
**Nota:** diferente de I1 e I3, aqui o agente consegue testar **e** confirmar sozinho, porque tudo acontece na resposta crua que o `http_request` enxerga. Bom contraste para a análise crítica.
**Previsão sobre a IA:** achamos que o agente vai se sair muito bem aqui, porque o teste é trocar um número e ler a resposta, que é exatamente o que o `http_request` faz. O risco é ele pedir muitos carrinhos seguidos sem necessidade, ou tirar conclusão de um único caso; nossa supervisão vai decidir quando já há evidência suficiente.

---

## I3 — Tratamento de entradas, requisições ou acesso a recursos

**Aspecto investigado e por quê:** se o servidor devolve a entrada do usuário sem escapar, fazendo o navegador interpretá-la como código (XSS refletido). Observação ao vivo: termo de busca com `<b>` refletido no título do resultado.

**Hipótese 1:** acredito que a aplicação devolve o termo de busca sem codificar os símbolos de HTML, fazendo o navegador interpretá-los como código em vez de texto (XSS refletido).
- **Porque observei:** ao buscar `apple<b>x</b>`, o `x` apareceu em **negrito** no título "Search Results" da página, por volta das 08:22 — ou seja, o navegador interpretou o `<b>` como marcação, e não como texto (print `planejamento/prints/0822_busca_html_refletido.png`).
- **Observação adicional (DevTools):** inspecionando a requisição `GET /rest/products/search?q=...`, vimos que a resposta crua (JSON) **não** contém o termo buscado — ela devolve a lista de produtos, não o texto do usuário. Logo, o reflexo não está nessa resposta de API, e sim na renderização do título feita pelo front-end. (Notamos também que as descrições de produto já trazem HTML cru, como `<a>` e `<em>`, no JSON.)
- **Como testar:** (a) com o agente (`http_request`), enviar a busca com marcação HTML e inspecionar a resposta; (b) confirmar no navegador se a marcação é interpretada na tela.
- **Confirma se:** a tela mostra o efeito da marcação (negrito) em vez dos sinais `<b>` — e, se alguma resposta de API refletir o termo, ele volta sem escape.
- **Refuta se:** a tela mostra `<b>` como texto comum e nenhuma resposta reflete o termo sem escape.

**Ferramenta:** `http_request`.
**Evidência esperada no log:** as requisições feitas pelo agente e suas respostas; o print da tela confirma a parte visual.
**Nota sobre o limite do agente (importante para a análise crítica):** já sabemos, pela inspeção manual, que a requisição de busca **não** reflete o termo na resposta crua, e que o `http_request` vê só o cru, não a tela. Portanto, esperamos que o agente **não** consiga confirmar sozinho este XSS refletido — a confirmação final depende do humano no navegador. Esta investigação serve justamente para observar como o agente lida com uma falha que a sua única "janela" (a resposta crua) não revela.
**Previsão sobre a IA:** achamos que o agente vai ter dificuldade nesta investigação, porque a requisição de busca não reflete o termo na resposta crua, e o reflexo só aparece na tela, que o agente não vê. A confirmação vai depender do humano no navegador.
