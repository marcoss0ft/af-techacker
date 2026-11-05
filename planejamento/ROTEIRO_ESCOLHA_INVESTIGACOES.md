# Roteiro: escolher as 3 investigações e as ferramentas (Fase 3a)

> Escrito no formato de um prompt; quem executa é o grupo. Resultado em `plano_testes_grupo.md`.

---

## Contexto do projeto

Você é integrante do Grupo 7 na AF de Tecnologias Hackers. O projeto é um **agente supervisionado**: um programa em Python que integra um LLM local (Qwen3 4B via Ollama) a ferramentas de segurança para investigar o OWASP Juice Shop, rodando no servidor do kit (`discorder`, acesso por VPN + SSH).

O agente funciona em ciclo: recebe um objetivo, propõe uma ação com uma ferramenta, o grupo autoriza/modifica/rejeita, a ferramenta roda, o resultado volta ao modelo e ele propõe o próximo passo. Tudo é registrado em log.

O que precisa ser entregue nesta etapa: **3 investigações**, uma por tema, cada uma com hipóteses testáveis e a ferramenta que a testa. Essas 3 escolhas decidem quais ferramentas o agente vai precisar.

**Material já levantado pelo grupo:** a exploração manual do Juice Shop (prints da busca com HTML refletido, rota `/administration` com 403, `/score-board` acessível, tela de checkout) e a avaliação de segurança que mapeou as classes de vulnerabilidade (A01 Broken Access Control, A03 Injection, A02/A07 cripto e autenticação, A05/A06 configuração e componentes, A08–A10).

## Objetivo deste roteiro

Transformar o que o grupo observou em **3 investigações**, uma por tema, e a partir delas decidir as ferramentas do agente.

## Os 3 temas (o enunciado sugere)

- **I1 — Reconhecimento e enumeração:** o que a aplicação revela sobre si mesma; rotas, páginas e arquivos que existem mas não aparecem nos menus.
- **I2 — Autenticação ou autorização:** como o site identifica o usuário e decide o que ele pode acessar; acesso a recursos de outros usuários.
- **I3 — Tratamento de entradas, requisições ou acesso a recursos:** o que o servidor faz com o que o usuário envia; o que volta quando a entrada é inesperada.

## Passo 1 — Listar as candidatas de cada tema

Para cada tema, liste as observações do grupo (dos prints e da avaliação) que se encaixam. Candidatas já levantadas, para começar:

| Tema | Candidatas observadas pelo grupo |
|---|---|
| I1 | rotas acessíveis direto pela URL (`/score-board`, `/administration` com 403); arquivos/documentos em diretórios previsíveis; erros verbosos |
| I2 | acesso a recurso de outro usuário trocando o id (IDOR); escalonamento para admin; conteúdo e validação do token de sessão (JWT) |
| I3 | entrada da busca refletida na página (XSS visto na tela); entrada do login/busca interpretada como consulta (SQLi) |

## Passo 2 — Escolher uma investigação por tema

Para cada tema, escolha **uma** candidata, usando estes critérios:

1. **Temos observação própria dela?** O que o grupo viu ao vivo (ex.: o HTML refletido na busca) é mais forte do que o que só foi lido.
2. **Dá para testar em até ~15 passos do agente?** Prefira o que é curto e direto.
3. **Tem confirmação e refutação nítidas?** Precisa existir um resultado que diga claramente "não é isso".
4. **As três juntas cobrem situações distintas?** Evite três investigações que, no fundo, testam a mesma coisa.

## Passo 3 — Escrever cada hipótese

Para cada investigação escolhida, escreva no formato de quatro partes:

> **Hipótese:** acredito que ___, porque observei ___ (hora da observação).
> **Como testar:** vou fazer ___ (método, caminho, dados exatos).
> **Confirma se:** a resposta mostrar ___.
> **Refuta se:** a resposta mostrar ___.

Se não conseguir escrever o "refuta se", a hipótese ainda está vaga. Reescreva.

## Passo 4 — Derivar as ferramentas das hipóteses

A ferramenta existe para responder à pergunta da hipótese. Depois de escrever as três, olhe o que cada teste exige:

| A pergunta do teste é… | Ferramenta | Situação no agente |
|---|---|---|
| "O servidor responde assim a este pedido?" (trocar id, enviar entrada, ler cabeçalho/erro) | `http_request` | pronto |
| "Que rotas/arquivos existem além dos que conheço?" | descoberta de rotas (wordlist pequena) | a implementar, se alguma hipótese pedir |
| "O que tem dentro deste token de sessão?" | leitor de JWT (local, sem rede) | a implementar, se alguma hipótese pedir |
| "Que serviço/versão roda nesta porta?" | `nmap_scan` | pronto (valor limitado: alvo já conhecido) |

Decida e registre:
- Quais ferramentas as 3 investigações exigem.
- Se falta implementar alguma (descoberta de rotas, leitor de JWT), justifique em uma frase ligada a uma hipótese.
- Se o `nmap_scan` não é exigido por nenhuma hipótese, registre isso — vira argumento no relatório sobre seleção de ferramentas.

## Passo 5 — Prever o papel da IA

Para cada investigação, uma ou duas frases: onde o agente provavelmente vai ajudar e onde vai falhar. Isso será comparado depois com o que o agente realmente fizer.

## Formato de saída (em `plano_testes_grupo.md`)

Para cada uma das 3 investigações:
1. Aspecto investigado e por quê (ligado a uma observação).
2. Hipótese(s) no formato de quatro partes.
3. Ferramenta que testa cada hipótese.
4. Evidência esperada no log (código de resposta, trecho do conteúdo, dado que não deveria vir).
5. Previsão sobre a IA.

No fim, a lista consolidada de ferramentas que o agente vai precisar.

## Critério de pronto

- [ ] 3 investigações, uma por tema, cada uma ligada a uma observação do grupo
- [ ] Cada hipótese tem "confirma se" e "refuta se" claros
- [ ] Cada hipótese aponta uma ferramenta
- [ ] Decisão registrada sobre descoberta de rotas, leitor de JWT e nmap
- [ ] Previsão sobre a IA escrita para cada investigação
