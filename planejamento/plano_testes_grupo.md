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

**Hipótese 1:** acredito que a aplicação expõe rotas/recursos não listados nos menus, alcançáveis por quem conhece o caminho, porque observei ___ (hora).
- **Como testar:** ___ (ex.: pedir uma lista de caminhos candidatos e observar o código de resposta de cada um).
- **Confirma se:** ___ (ex.: caminhos fora dos menus respondem com conteúdo da aplicação).
- **Refuta se:** ___ (ex.: todos retornam 404 ou 403).

**Ferramenta:** descoberta de rotas (principal); `http_request` para confirmar caso a caso.
**Evidência esperada no log:** código de resposta e um trecho do conteúdo de cada caminho que responder.
**Previsão sobre a IA:** _(a preencher: onde achamos que vai ajudar / falhar)_.

---

## I2 — Autenticação ou autorização

**Aspecto investigado e por quê:** se o servidor confere que um recurso pertence ao usuário autenticado, ou se devolve o recurso de qualquer id informado (IDOR). Base: a avaliação apontou IDOR como a classe dominante no Juice Shop.

**Hipótese 1:** acredito que o servidor devolve um recurso de outro usuário ao trocar o id na requisição, porque observei ___ (hora).
- **Como testar:** ___ (ex.: autenticar com conta de teste, pegar o id do próprio recurso e refazer a requisição com outro id).
- **Confirma se:** ___ (ex.: a resposta traz dados que não pertencem à conta usada).
- **Refuta se:** ___ (ex.: a resposta é 401/403 ou vazia).

**Ferramenta:** `http_request`.
**Evidência esperada no log:** a requisição com o id trocado, o código de resposta e o dado retornado que não é da conta de teste.
**Previsão sobre a IA:** _(a preencher)_.

---

## I3 — Tratamento de entradas, requisições ou acesso a recursos

**Aspecto investigado e por quê:** se o servidor devolve a entrada do usuário sem escapar, fazendo o navegador interpretá-la como código (XSS refletido). Observação ao vivo: termo de busca com `<b>` refletido no título do resultado.

**Hipótese 1:** acredito que a busca reflete a entrada sem codificar a saída, porque observei ___ (hora).
- **Como testar:** ___ (ex.: enviar à busca uma entrada com marcação e inspecionar a resposta crua do servidor).
- **Confirma se:** ___ (ex.: a marcação volta sem escape no corpo da resposta).
- **Refuta se:** ___ (ex.: a marcação volta escapada, como texto).

**Ferramenta:** `http_request`.
**Evidência esperada no log:** a requisição de busca e o trecho da resposta mostrando a entrada escapada ou não.
**Previsão sobre a IA:** _(a preencher)_.
