# Roteiro da exploração manual (Fase 3a)

> Escrito no formato de um prompt; quem executa é o grupo.

---

## Papel

Você é um integrante do Grupo 7 fazendo o **reconhecimento manual** do OWASP Juice Shop. Seu trabalho é **observar e registrar**, não atacar. As hipóteses e o plano de testes nascem das suas observações.

## Objetivo

Ao final, o grupo deve ter:
1. `planejamento/observacoes_iniciais.md` preenchido, com observações datadas;
2. `planejamento/plano_testes_grupo.md` com **3 investigações**, uma por tema, cada uma com hipóteses testáveis;
3. a lista de **ferramentas** que cada hipótese exige.

## Regras

1. **Só o Juice Shop**, em `http://localhost:3000` pelo túnel SSH. Nada de WordPress, Nextcloud ou pfSense.
2. **Só navegador e DevTools.** Nada de ferramenta automática (nmap, ffuf, scanners). Elas entram depois, pelo agente.
3. **Observar, não explorar.** Se algo parecer vulnerável, **anote e siga em frente**. O teste em si acontece na Fase 4, com o agente e os logs. Uma falha "achada" agora, sem registro, não serve de evidência.
4. **Anote tudo na hora**, mesmo o que parecer bobo. Observação que não foi anotada não existe.
5. Os dois participam juntos: um navega, o outro anota. Troquem a cada etapa.

## Preparação (5 min)

1. Ligar a VPN do pfSense.
2. No PowerShell: `ssh -L 3000:127.0.0.1:3000 discorder_adm@10.0.80.3` (deixar a janela aberta).
3. No servidor, zerar o Juice Shop: `~/af-techacker/lab/restore.sh`.
4. No Chrome, abrir `http://localhost:3000`.
5. Apertar **F12**, abrir a aba **Network** e marcar **Preserve log** (para não perder as requisições ao trocar de página).
6. Abrir `planejamento/observacoes_iniciais.md` ao lado e preencher data, hora de início e participantes.

## Etapa 1 — Usar a loja como um cliente comum (30 min)

Faça, em ordem, o que um cliente faria. A cada passo, olhe a tela **e** a aba Network.

1. Navegar pela página inicial e abrir alguns produtos.
2. Usar a busca.
3. Abrir os menus laterais e do topo; visitar cada página que aparecer.
4. Criar uma conta (e-mail e senha de teste, que **não** sejam reais) e fazer login.
5. Pôr produtos no carrinho, alterar quantidades e ir até o checkout.
6. Ver e editar o perfil.
7. Usar qualquer formulário: contato, avaliação de produto, reclamação etc.
8. Trocar o idioma, fazer logout e login de novo.

**Para cada passo, pergunte-se:** o que apareceu na tela? Que requisições foram feitas? Alguma coisa estranha, inesperada ou com cara de "não deveria estar aqui"?

## Etapa 2 — Olhar por trás da tela (30–45 min)

**Aba Network** (filtro **Fetch/XHR**, que mostra só as conversas da página com o servidor):
- Para cada requisição interessante, anote: **método** (GET/POST…), **caminho**, **código de resposta** (200, 401, 403, 500…), **o que foi enviado** e **o que voltou**.
- Quais requisições exigem login e quais funcionam sem?
- Alguma resposta traz **mais informação do que a tela mostra**?
- Quando algo dá errado, que **mensagem de erro** volta? Ela revela detalhes internos?

**Aba Application:**
- Em **Cookies** e **Local Storage**: o que o site guarda no navegador **antes** e **depois** do login? Anote os nomes e o formato do que aparecer.

**Aba Sources:**
- Abra os arquivos JavaScript principais da aplicação. Procure **caminhos de páginas ou de API** que não aparecem em nenhum menu. Anote os que encontrar.

## Etapa 3 — Perguntas-guia por tema (15 min)

Respondam por escrito, com base no que observaram (se não souberem responder, isso também é uma observação):

**I1 — Reconhecimento e enumeração**
- O que a aplicação revela sobre si mesma sem login?
- Que páginas e rotas existem, e quais aparecem só no código ou nas requisições, sem link visível?
- O servidor entrega arquivos ou informações que não deveria?

**I2 — Autenticação ou autorização**
- Como o site sabe quem você é depois do login? Onde essa informação fica e o que tem dentro dela?
- O que acontece se você pedir algo que pertence a outro usuário?
- Como o login trata o que você digita?

**I3 — Tratamento de entradas, requisições ou acesso a recursos**
- Onde o usuário consegue mandar dados ao servidor?
- O que volta quando você manda algo inesperado (texto muito longo, caracteres especiais, campo vazio)?
- Dá para chegar a um recurso mudando um número ou um caminho na requisição?

Usem também o conteúdo das aulas: cada técnica vista na disciplina é uma pergunta possível.

## Etapa 4 — Como preencher `observacoes_iniciais.md`

- **Uma linha por observação**, com a hora.
- **Separe fato de interpretação:** na coluna "O que observamos" vai só o que apareceu (ex.: "a requisição X voltou 500 com a mensagem Y"). A opinião vai em "Por que pareceu interessante".
- **Marque o tema** (I1, I2, I3 ou "?" se não souber).
- **Guarde a evidência:** print em `planejamento/prints/` com nome `HHMM_descricao.png`, ou a requisição copiada (botão direito na requisição → Copy → Copy as cURL) colada no arquivo. Na coluna "Evidência", escreva o nome do print ou "cURL abaixo".
- Não escreva conclusões do tipo "é vulnerável". Escreva "pode ser interessante investigar se…".

## Etapa 5 — Transformar observações em plano (30–45 min)

Preencham `planejamento/plano_testes_grupo.md`:

1. **Escolham 3 investigações**, uma por tema, cada uma ligada a pelo menos uma linha de `observacoes_iniciais.md`.
2. **Para cada uma, 1 ou 2 hipóteses** no formato:
   > **Hipótese:** acho que ___ acontece, porque observei ___ (linha das 14:32).
   > **Como testar:** vou fazer ___ com a ferramenta ___.
   > **Confirma se:** ___.  **Refuta se:** ___.
3. **Confira cada hipótese com este checklist:**
   - [ ] Está ligada a uma observação concreta?
   - [ ] Existe um resultado que a **refuta**? Se não existir, reescrevam.
   - [ ] Dá para testar com uma requisição ou ferramenta específica?
   - [ ] A evidência que confirma e a que refuta estão definidas **antes** do teste?
   - [ ] Fica dentro do escopo (só o Juice Shop)?
4. **Ferramentas:** para cada hipótese, anotem qual ferramenta a testa. Depois, olhem a lista completa e decidam:
   - o `http_request` e o `nmap_scan` (já prontos) bastam?
   - falta alguma, como descoberta de rotas ou leitor de token? Justifiquem em uma frase.
   - o nmap serve para alguma hipótese? Se não, registrem isso (vira argumento no relatório).
5. **Previsão sobre a IA:** para cada investigação, uma ou duas frases sobre onde vocês acham que o agente vai ajudar e onde vai falhar.

## Critério de pronto

- [ ] `observacoes_iniciais.md` com pelo menos 10 observações, cada uma com hora, tema e evidência
- [ ] 3 investigações distintas, uma por tema
- [ ] Cada hipótese passa no checklist da Etapa 5
- [ ] Ferramentas necessárias listadas, com a decisão sobre nmap e ferramentas extras
- [ ] Previsão sobre a IA escrita
