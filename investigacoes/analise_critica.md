# Análise crítica da contribuição da IA (Fase 6)

> Base: as três investigações (`I1.md`, `I2.md`, `I3.md`) e os logs correspondentes
> (`logs/investigacao_I1.jsonl`, `_I2.jsonl`, `_I3.jsonl`). Modelo: Qwen3 4B via Ollama,
> `temperature` 0.2, sem seed fixo (ver nota sobre a integração). Todas as afirmações abaixo
> remetem a turnos registrados em log.

## Resumo
O agente foi **útil em graus diferentes** conforme a investigação: enumerou bem na I1, fez o
raciocínio central na I2, e foi praticamente cego na I3. Em todas as três, a **supervisão humana
foi decisiva** — para elevar a qualidade da evidência, para tirar o modelo de loops e para confirmar
o que a "janela" do agente não revelava. O trabalho não mostra que a IA substitui o testador;
mostra **onde ela acelera o reconhecimento e onde ela falha e precisa de condução**.

---

## As 7 perguntas da seção 6

### 1. Em quais situações o modelo apresentou sugestões tecnicamente adequadas?
- **I1:** recebendo só o objetivo, o modelo escolheu sozinho a `dir_enum` para enumerar rotas — ferramenta coerente — e, a partir dos resultados, decidiu aprofundar num achado com `http_request`. Sugestões adequadas.
- **I2:** propôs `login` por conta própria (entendeu que precisava autenticar) e fez o **pulo lógico do IDOR** sem ajuda: "meu carrinho é o 6, vou pedir um id diferente para ver se acesso o de outro usuário". Esse é o raciocínio central da investigação, e foi do modelo.
- **I3:** aqui praticamente não houve sugestão adequada (ver pergunta 4).

Ou seja: o modelo é tecnicamente adequado em tarefas de **reconhecimento e no raciocínio de "trocar um identificador"**, que são padrões bem representados no treinamento.

### 2. O agente conseguiu selecionar ferramentas coerentes com os objetivos?
Parcialmente, e isso variou:
- **I1:** sim — `dir_enum` para enumerar, `http_request` para inspecionar um achado.
- **I2:** sim — `login` e depois `http_request` nos recursos indexados por id.
- **I3:** **não** — propôs `http_request` para `/#/products`, confundindo uma **rota de front-end** (o `#` indica roteamento no navegador) com um **endpoint de servidor**. A ferramenta até era a certa, mas o alvo não existia como endpoint. O modelo não distinguiu os dois conceitos.

### 3. Os resultados obtidos influenciaram as decisões seguintes?
**Em parte, e de forma inconsistente.**
- **Quando influenciaram:** na I1, o resultado da `dir_enum` levou o modelo a propor abrir um arquivo específico; na I2, o resultado do `login` (o id do carrinho) levou ao teste do IDOR. Nesses casos a cadeia "resultado → próxima ação" funcionou.
- **Quando NÃO influenciaram:** em vários turnos o modelo **ignorou** o resultado e repetiu a proposta anterior (I2 e I3). Na I3, mesmo depois de a busca retornar vazia, ele voltou a propor `/#/products`. O resultado novo não alterou a decisão.

Conclusão: o modelo reage a resultados em situações simples, mas **perde o fio** quando o passo exige corrigir uma ideia já fixada.

### 4. O modelo apresentou interpretações incorretas ou conclusões sem evidências?
**Sim, repetidamente — e este é um dos achados mais importantes.**
- **I2 — conclusão a partir de evidência vazia:** o modelo quis **finalizar afirmando IDOR** com base no carrinho `/rest/basket/7`, que havia retornado `data: null` (vazio). "Acessei o carrinho de outro usuário" foi afirmado sobre uma resposta que não continha carrinho nenhum.
- **I2 — confusão entre requisições:** após o grupo forçar o `/rest/basket/1` (que trouxe dados reais), o modelo atribuiu esses produtos ao carrinho **7**, misturando de qual requisição veio cada resposta.
- **I2 — imprecisão factual recorrente:** descreveu o acesso como "sem autenticação adicional", quando a sessão **estava** autenticada.
- **I3 — cegueira à falha:** o modelo só vê a resposta crua; como a busca de API não reflete o termo, ele concluiria "não há XSS", quando o XSS **existe** (confirmado na tela).

### 5. Houve ações repetitivas, desnecessárias ou inadequadas?
**Sim, de forma marcante.** Em I2 e I3 o modelo **repetiu propostas idênticas** por vários turnos, inclusive depois de o grupo rejeitar com orientação. O agente tem um **detector de repetição** que sinalizou cada ocorrência (`⚠ o modelo repetiu a proposta anterior`). Na I3, foram três turnos propondo o mesmo `/#/products`. Essas repetições não agregaram nada à investigação e só avançaram por intervenção humana.

### 6. Em quais situações a intervenção humana foi necessária?
Em todas as três investigações, e de três formas distintas:
- **Elevar a qualidade da evidência (I2):** o grupo rejeitou a conclusão baseada no carrinho vazio e **forçou** o `/rest/basket/1`, obtendo a prova real (`UserId 1` ≠ `UserId 25`).
- **Dar direção quando o modelo travou (I2, I3):** quando a rejeição com orientação não bastou (o modelo repetia), o grupo usou **Modificar** para impor a ação — por exemplo, forçar o segundo recurso `/api/Addresss/1`.
- **Confirmar o que o agente não enxerga (I3):** a existência do XSS foi confirmada **pelo humano no navegador** (a busca `apple<b>x</b>` renderizou o `x` em negrito), porque a falha está na renderização, fora da resposta crua.

### 7. Quais limitações foram observadas no modelo e na integração?
**No modelo (Qwen3 4B):**
- alucina/confunde endpoints (`/#/products` como endpoint; produtos atribuídos ao carrinho errado);
- conclui sem evidência suficiente (IDOR a partir de carrinho vazio);
- fixa-se numa proposta e **não incorpora o feedback** de uma rejeição com orientação (loop);
- comete imprecisões factuais ("sem autenticação").

**Na integração desenvolvida:**
- o `http_request` enxerga apenas a **resposta crua**, não a renderização da página — por isso o agente não detecta XSS refletido que só aparece na tela (limitação estrutural, assumida de propósito como objeto de estudo);
- o agente **não informa ao modelo quando uma ação foi modificada/forçada** pelo grupo, então o modelo atribui a si resultados que vieram de uma ação do humano (contribui para a confusão entre requisições);
- duas limitações foram **identificadas e corrigidas durante o trabalho** (ver próxima seção): a ausência de "Modificar" no passo de finalização e o uso de um *seed* fixo que tornava as respostas quase determinísticas e agravava os loops.

---

## Exemplo concreto de limitação (obrigatório), em detalhe

**Caso: na I2, o modelo concluiu uma vulnerabilidade a partir de uma evidência vazia e, em seguida,
não conseguiu sair do loop.**

1. O modelo pediu `/rest/basket/7` e recebeu `HTTP 200` com `{"status":"success","data":null}` — ou seja, **nenhum carrinho**.
2. No turno seguinte, propôs **finalizar** afirmando "o usuário autenticado consegue acessar o carrinho de outro usuário (id=7), com produtos e quantidades" — uma conclusão **falsa**, porque a resposta estava vazia.
3. **Como o grupo detectou:** comparamos a afirmação do modelo com a resposta real registrada no log; o campo `data` era `null`, não havia produtos. A conclusão não se sustentava na evidência.
4. **Como o grupo lidou:** rejeitamos e **forçamos** `/rest/basket/1`, que retornou um carrinho real de `UserId 1`. Essa sim é a evidência do IDOR. Em seguida, ao tentar levar o modelo a um segundo recurso, ele **repetiu** a proposta do carrinho mesmo após rejeição com orientação; tivemos de **impor** o teste de `/api/Addresss/1`.
5. **O que isso ensina:** a saída de um LLM pequeno pode ser confiante e errada ao mesmo tempo. A frase "uma sugestão do modelo não é evidência" (do enunciado) se confirmou na prática: só a resposta real da ferramenta, lida pelo grupo, sustentou a conclusão.

*(Um segundo exemplo igualmente ilustrativo está na I3: o agente é estruturalmente incapaz de
confirmar o XSS refletido, porque ele vive na renderização e o agente só vê o corpo cru.)*

---

## Comparação: estratégia do grupo × contribuição do agente

O plano do grupo (feito sem IA) previa: **I1** enumerar rotas não listadas; **I2** trocar o id de um
recurso para testar IDOR; **I3** enviar marcação HTML à busca para testar XSS refletido.

Recebendo **apenas o objetivo** (sem a estratégia), o agente:
- **I1 e I2:** re-derivou, sozinho, uma abordagem muito próxima da que o grupo havia planejado (enumerar com `dir_enum`; autenticar e trocar o id). Isso **valida** o plano do grupo — a estratégia era a "natural" —, mas também mostra que, nesses casos, o agente **acrescenta pouco além do que o grupo já havia pensado**; seu ganho é de velocidade no trabalho repetitivo, não de ideias novas.
- **I3:** **divergiu para pior** — propôs uma rota de tela inexistente como endpoint, algo que o plano do grupo não cometeria.

**Previsão do grupo × realidade:** o grupo previu que o agente iria bem na I2 e mal na I3. Confirmou-se
nos dois: na I2 ele fez o raciocínio (mas precisou de supervisão para a evidência); na I3 ele não
contribuiu para a confirmação. A previsão feita *antes* dos testes se mostrou correta.

**Escala de contribuição (síntese):**
- **I1 — útil:** enumerou bem; supervisão pontual (corrigir a atribuição de um caminho).
- **I2 — útil com supervisão:** bom raciocínio inicial; a evidência de qualidade e a ampliação de escopo vieram do grupo.
- **I3 — pouco útil:** cego para a falha por limite estrutural; confirmação inteiramente humana.

---

## Nota sobre a honestidade do experimento (integração corrigida durante o trabalho)
Duas falhas da **nossa ferramenta** foram descobertas durante os testes e **corrigidas**, para não
contaminar as conclusões sobre o *modelo*:
1. o agente não permitia "Modificar" uma proposta de finalização, o que, numa primeira tentativa de
   I2, impediu de impor o segundo recurso; corrigimos e refizemos o teste;
2. usávamos um *seed* fixo, que tornava a saída quase determinística e agravava os loops; removemos
   o seed fixo.
Os episódios de repetição descritos acima (perguntas 3 e 5) foram observados **depois** dessas
correções, num teste limpo — por isso são atribuíveis ao modelo, não à integração. Registrar e
corrigir esses pontos faz parte da própria análise crítica: parte do que parecia "limitação da IA"
era, na verdade, limitação da ferramenta que construímos.
