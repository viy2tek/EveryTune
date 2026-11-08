# Auditoria UX/UI do EveryTune 0.4.0

Data: 06/11/2026. Revisão de diagnóstico: não foram modificados os arquivos da interface nem os dados pessoais do aplicativo.

## Base, premissas e método

- Alvo assumido: o EveryTune deste projeto, e não os sites FMHY/Jumo usados como referências anteriores. Não foi fornecida uma URL de produção nesta solicitação.
- Cenário: uso pessoal em português, principalmente para pesquisar música, comparar fontes e preparar arquivos; mouse, teclado e toque. As configurações avançadas são uma tarefa secundária.
- Referência: WCAG 2.2 nível AA. Recomendações de conforto e de organização são identificadas como decisões de UX, não como requisitos normativos.
- Ambiente: Edge/Chromium instalado no Windows, em modo automatizado, aplicação real em loopback e diretório de dados temporário. Larguras de 1440, 1024, 768, 600, 390 e 320 CSS px; temas claro e escuro.
- Estados: início, resultados, cinco painéis de configurações, modal de downloads, fila, nomes longos, listas extensas, foco, ampliação de texto e espaçamento. Foram produzidas 49 capturas. Os resultados e as preparações foram simulados para controlar os estados; não houve download de música nem autenticação em plataformas.
- Inspeção do código para confirmar causas, destinos de navegação e ações destrutivas. As métricas de geometria/foco foram capturadas no navegador.
- O primeiro ensaio de espaçamento por elemento `<style>` foi bloqueado pela CSP. A verificação foi concluída via CSSOM na sessão isolada, sem enfraquecer a CSP ou modificar CSS do produto.

Evidências: [medições](C:/Users/User/Documents/ChatGPT/EveryTune/artifacts/ux-audit-2026-11-06/measurements.json), [verificações complementares](C:/Users/User/Documents/ChatGPT/EveryTune/artifacts/ux-audit-2026-11-06/followup.json), [script principal](C:/Users/User/Documents/ChatGPT/EveryTune/scripts/audit_ux_layout.py), [script complementar](C:/Users/User/Documents/ChatGPT/EveryTune/scripts/audit_ux_followup.py).

## Resultado e prioridade

Há **13 achados: quatro de severidade alta, oito média e um baixa**. Não identifiquei necessidade de substituir a identidade visual. Os principais problemas são de atualização dinâmica, organização móvel e proteção das configurações.

Pontuação heurística, não certificação nem resultado Lighthouse:

| Dimensão | Nota / 4 | Evidência principal |
|---|---:|---|
| Acessibilidade | 2 | Foco perdido durante atualizações e ausência de anúncio na fila |
| Performance | 3 | Carga inicial pequena; reconstrução de listas merece melhoria |
| Responsividade | 2 | Rolagem nos dois eixos a 320 px; resultados distantes no celular |
| Temas | 3 | Contraste textual adequado na amostra; contornos inconsistentes |
| Integridade da implementação | 2 | Sistema visual coerente, mas atualizações e ações não preservam todo o contexto |
| Total | **12/20** | Trabalho funcional de UX antes de acabamento visual |

O detector mecânico da skill não apontou ocorrências. Isso não invalida os defeitos encontrados por reprodução no navegador; o detector não cobre todos os comportamentos dinâmicos.

## Achados

### R01 — Foco de teclado perdido quando listas são atualizadas

**Severidade: alta. Custo: médio. Confirmado no navegador.**

**Local:** resultados e fila de downloads; [app.js:120](C:/Users/User/Documents/ChatGPT/EveryTune/everytune/static/app.js:120) e [downloads.js:49](C:/Users/User/Documents/ChatGPT/EveryTune/everytune/static/downloads.js:49).

**Evidência:** após focar um link de resultado e receber um evento de fonte, `document.activeElement` passou para `BODY`. O mesmo ocorreu após focar Cancelar e aguardar a atualização periódica da fila. A fila é reconstruída a cada segundo enquanto há preparação ativa.

**Impacto:** quem usa teclado perde a posição e pode deixar de ativar o botão que estava focado. Na fila, a operação fica dependente de agir antes da próxima atualização. A navegação com leitor de tela precisa de validação específica, mas a perda de foco DOM está confirmada.

**Correção:** manter os nós dos itens por ID e atualizar texto, progresso e estado sem recriar botões/links existentes. Ao remover um item por ação do usuário, escolher um destino de foco previsível.

**Trade-off:** restaurar foco após reconstruir a lista é uma mitigação barata, mas não preserva tão bem o contexto de leitura. Atualizações incrementais têm custo maior e resolvem também parte da recriação desnecessária do DOM. Referências: [operação por teclado sem temporização específica](https://www.w3.org/WAI/WCAG22/Understanding/keyboard.html) e [foco visível e persistente](https://www.w3.org/WAI/WCAG22/Understanding/focus-visible.html).

### R02 — Lista de fontes exige rolagem horizontal e vertical a 320 px

**Severidade: alta. Custo: baixo. Confirmado por geometria e captura.**

**Local:** Onde procurar → grupos Streaming/Comunidade. Regras de `#source-list` em [style.css](C:/Users/User/Documents/ChatGPT/EveryTune/everytune/static/style.css) e [expansion.css](C:/Users/User/Documents/ChatGPT/EveryTune/everytune/static/expansion.css).

**Evidência:** a caixa tem 280 px de largura útil, conteúdo com 315 px e 2777 px de altura. Ambos os eixos têm `overflow: auto`. A ação Limpar do segundo grupo fica fora da região inicialmente visível. A largura total do documento continua em 320 px: verificar apenas o overflow global não detectaria o defeito.

**Impacto:** nomes e ações ficam parcialmente escondidos; o usuário precisa combinar gestos horizontais e verticais dentro de uma lista simples.

**Correção:** em telas pequenas, usar uma coluna por grupo e permitir quebra nos cabeçalhos; garantir `min-width: 0` nas colunas e evitar overflow horizontal da lista. Não simplesmente esconder o conteúdo com `overflow-x: hidden`.

**Trade-off:** empilhar aumenta o comprimento vertical. Combinar essa correção com R03 evita que o aumento empurre ainda mais os resultados. O [critério de reflow](https://www.w3.org/WAI/WCAG22/Understanding/reflow.html) considera 320 CSS px e exige acesso ao conteúdo sem rolagem nos dois eixos, salvo exceções que não se aplicam a esta lista.

Evidência visual: [painel a 320 px](C:/Users/User/Documents/ChatGPT/EveryTune/artifacts/ux-audit-2026-11-06/source-panel-320.png).

### R03 — No celular, a tarefa principal fica depois de uma tela de configurações

**Severidade: alta. Custo: médio. Confirmado.**

**Local:** busca e resultados em 390 × 844 px; estrutura `.workspace` e `.source-sidebar`.

**Evidência:** depois de preencher os resultados de teste, a área de resultados começa em aproximadamente **958 px** a partir do topo. Os primeiros cartões ficam ainda abaixo dos seis filtros. Antes da primeira busca, a área vazia começa em cerca de 1099 px.

**Impacto:** após Buscar, o usuário pode continuar vendo apenas fontes e interpretar que nada aconteceu. A seleção avançada disputa espaço com a leitura das faixas.

**Correção:** no celular, apresentar Fontes como um resumo recolhível com grupo ativo e quantidade marcada; exibir os resultados logo depois da busca. Recolher também os filtros não utilizados, mantendo visíveis os filtros ativos.

**Trade-off:** a seleção detalhada passa a exigir um toque adicional, mas deixa de ocupar a tela em todas as pesquisas. Uma solução apenas com mudança de ordem visual não deve ser presumida suficiente: conferir também a sequência de leitura e de Tab. A prioridade de aparecer primeiro é uma decisão de UX, não uma regra WCAG de “primeira dobra”.

Evidência: [resultados no celular](C:/Users/User/Documents/ChatGPT/EveryTune/artifacts/ux-audit-2026-11-06/results-390.png).

### R04 — Restaurar padrões pode apagar personalizações sem revisão ou desfazer

**Severidade: alta. Custo: baixo a médio. Confirmado por inspeção de código; ação não executada sobre dados pessoais.**

**Local:** Ajustes → Perfis → Restaurar padrões; [preferences.js:101](C:/Users/User/Documents/ChatGPT/EveryTune/everytune/static/preferences.js:101) e [storage.py:98](C:/Users/User/Documents/ChatGPT/EveryTune/everytune/storage.py:98).

**Evidência:** o botão chama diretamente a exclusão/restauração do perfil. O armazenamento substitui a lista de fontes e as preferências. Não há confirmação contextual nem recuperação na interface.

**Impacto:** um clique pode eliminar fontes adicionadas e mapeamentos trabalhosos. O texto do botão não explica a extensão da substituição.

**Correção:** apresentar uma revisão curta do que será substituído e oferecer exportação do perfil atual. A solução mais robusta é manter uma cópia anterior e permitir Desfazer.

**Trade-off:** confirmação tem custo baixo, mas adiciona uma etapa; recuperação tem custo médio e reduz a necessidade de interromper o usuário. Esta recomendação é de prevenção de erro no fluxo, sem afirmar certificação ou falha normativa específica.

### R05 — Conclusão e falha da preparação não têm anúncio de status dedicado

**Severidade: média. Custo: baixo. Ausência confirmada no HTML/JS; experiência com leitor de tela ainda não testada.**

**Local:** Downloads → Preparações; [index.html:104](C:/Users/User/Documents/ChatGPT/EveryTune/everytune/static/index.html:104) e [downloads.js:51](C:/Users/User/Documents/ChatGPT/EveryTune/everytune/static/downloads.js:51).

**Evidência:** mensagens como Pronto para salvar e as falhas de um job são parágrafos comuns. A fila não possui uma região de status estável. O alerta de erro do modal atende falhas de chamadas, mas não substitui o anúncio das transições dos jobs.

**Impacto:** quem não acompanha visualmente a fila pode não perceber que o arquivo terminou ou falhou.

**Correção:** uma região persistente com `role="status"`/anúncio educado para mudanças importantes, com nome do arquivo e resultado. Evitar anunciar cada atualização de bytes ou tornar toda a lista uma região falante.

**Trade-off:** anunciar tudo gera ruído; anunciar apenas início, conclusão, cancelamento e falha mantém contexto. Referência: [WCAG 4.1.3 — mensagens de status](https://www.w3.org/WAI/WCAG22/Understanding/status-messages.html).

### R06 — Contornos dos campos claros têm pouco contraste

**Severidade: média. Custo: baixo. Contraste medido; enquadramento normativo depende da função visual do contorno.**

**Local:** campos de preferências e formulários, por exemplo País do catálogo; `input, select` em [style.css](C:/Users/User/Documents/ChatGPT/EveryTune/everytune/static/style.css).

**Evidência:** borda `#c4cbc1` contra fundo `#fffefa`: aproximadamente **1,64:1**. Nos campos observados, o contorno é uma pista importante de que o conteúdo é editável.

**Impacto:** o campo se mistura à superfície para usuários com baixa visão, mesmo quando o texto continua legível.

**Correção:** criar um token específico para contorno de controle, separado do divisor decorativo. Por exemplo, `#7b897f` oferece aproximadamente 3,63:1 contra o fundo do campo e 3,36:1 contra o papel claro desta interface.

**Trade-off:** não escurecer indiscriminadamente todos os divisores; isso aumentaria o peso visual sem necessidade. O [mínimo de 3:1 para informação visual necessária dos controles](https://www.w3.org/WAI/WCAG22/Understanding/non-text-contrast.html) não exige que toda linha decorativa ou todo botão tenha uma borda contrastante.

**Correção da inspeção preliminar:** os botões principais escuros não apresentaram a suposta falha de texto. A combinação medida de verde claro e texto escuro ficou em aproximadamente **10,26:1**. Nos textos normais amostrados não encontrei falha do [mínimo textual de 4,5:1](https://www.w3.org/WAI/WCAG22/Understanding/contrast-minimum.html).

### R07 — Estado de acesso das fontes desaparece no celular

**Severidade: média. Custo: baixo. Confirmado.**

**Local:** lista de fontes abaixo de 600 px; `.source-option .state { display: none; }` em [style.css](C:/Users/User/Documents/ChatGPT/EveryTune/everytune/static/style.css).

**Evidência:** Spotify mantém Requer acesso no texto do nó, mas seu estilo calculado é `display: none`. O checkbox permanece disponível para seleção.

**Impacto:** fica difícil distinguir uma fonte pronta de uma que exige configuração. O usuário pode selecioná-la e só descobrir o problema depois da busca.

**Correção:** manter um indicador textual compacto para estados que exigem ação, como Configurar acesso ou Indisponível, com caminho para o ajuste correspondente. Não depender apenas de cor ou de tooltip por hover.

**Trade-off:** mostrar todos os estados aumenta a densidade; priorizar apenas os que exigem ação conserva a informação útil sem repetir Não consultada em dezenas de linhas.

### R08 — Caminho de Tab até os resultados é excessivamente longo

**Severidade: média. Custo: baixo. Confirmado pela ordem de elementos focáveis.**

**Local:** entre a busca e o primeiro link de resultado.

**Evidência:** no estado com ambos os grupos e 12 resultados controlados, a busca ocupa a posição 4 e o primeiro link de resultado a posição 96 da sequência. O painel de fontes concentra 80 controles antes do primeiro resultado.

**Impacto:** usuários de teclado precisam atravessar dezenas de escolhas para chegar à tarefa principal.

**Correção:** adicionar um atalho visível ao receber foco, como Pular para resultados, e um destino focável no título dos resultados. O recolhimento do painel proposto em R03 também reduz esse caminho.

**Trade-off:** o atalho é barato e não remove a seleção avançada; não resolve sozinho o espaço visual no celular. Já existem títulos e regiões semânticas, por isso a falta desse link, isoladamente, não prova falha de conformidade. Referência: [mecanismos para contornar blocos](https://www.w3.org/WAI/WCAG22/Understanding/bypass-blocks.html).

### R09 — Metadados e ações auxiliares ficaram pequenos demais para esta densidade

**Severidade: média. Custo: baixo. Medição confirmada; recomendação tipográfica de UX.**

**Local:** estado das fontes no tablet, ações Todas/Limpar, notas de correspondência e créditos.

**Evidência:** estados em 9,92 px a 768 px de largura; ações em 10,4–10,88 px; etiqueta de correspondência em 10,72 px. Os títulos de faixa têm hierarquia distinta, mas informações úteis ficam bem menores.

**Impacto:** leitura lenta e dependência maior de ampliação para distinguir estado, evidência e ação.

**Correção:** testar 12–14 px para informação auxiliar e pelo menos 14 px nas ações deste produto, reduzindo rótulos repetidos para compensar a altura. Isso é uma recomendação de projeto, não um tamanho mínimo imposto pela WCAG.

**Trade-off:** letras maiores reduzem a quantidade de fontes visíveis; recolhimento e busca na lista são alternativas a encolher texto. A [WCAG 1.4.4 trata da ampliação a 200% sem perda](https://www.w3.org/WAI/WCAG22/Understanding/resize-text.html). O ensaio de tamanho de texto mostrou cortes internos na lista; confirmar também com zoom nativo e dispositivos reais antes de declarar conformidade.

### R10 — Algumas ações exigem precisão de toque desnecessária

**Severidade: média. Custo: baixo. Dimensões confirmadas; não é falha AA automática.**

**Local:** Selecionar todas, Todas/Limpar de cada grupo e seleção de arquivos no modal.

**Evidência:** Selecionar todas tem cerca de 15,2 px de altura; Todas/Limpar, 18,6 px. O checkbox de arquivo tem 17 × 17 px e seu texto adjacente não funciona como label clicável. Já os checkboxes das fontes têm o label da linha como alvo maior — não foram tratados como alvos de apenas 17 px.

**Impacto:** maior esforço e probabilidade de toque errado, sobretudo com uma mão.

**Correção:** ampliar a área clicável e associar o nome do arquivo ao checkbox. Para ações frequentes em toque, adotar 44 × 44 CSS px como meta de conforto.

**Trade-off e norma:** o [mínimo AA é 24 × 24, com exceções inclusive de espaçamento](https://www.w3.org/WAI/WCAG22/Understanding/target-size-minimum.html); [44 × 44 é a referência aprimorada AAA](https://www.w3.org/WAI/WCAG22/Understanding/target-size-enhanced.html). Uma dimensão menor, sozinha, não comprova falha AA. É possível ampliar apenas as áreas de toque mantendo o desenho compacto no desktop.

### R11 — Gerenciar fontes não garante a abertura da lista de fontes

**Severidade: baixa. Custo: baixo. Confirmado por inspeção da navegação.**

**Local:** botão Gerenciar fontes; [app.js:243](C:/Users/User/Documents/ChatGPT/EveryTune/everytune/static/app.js:243).

**Evidência:** a ação só abre a visão de ajustes. Em uma sessão nova, o painel inicial é Preferências; em outras sessões, pode ser o último painel usado.

**Impacto:** a ação promete uma tarefa e deixa o usuário procurar sua localização.

**Correção:** abrir diretamente Fontes instaladas usando o mecanismo de painel já existente. Quando a ação partir de uma fonte sem acesso, direcionar também para a fonte correspondente.

**Trade-off:** não é necessária uma reorganização de toda a navegação; um destino mais específico resolve a etapa extra.

### R12 — Editor mostra campos incompatíveis com a escolha atual

**Severidade: média. Custo: médio. Confirmado no formulário e nos eventos de código.**

**Local:** Ajustes → Adicionar fontes; [index.html](C:/Users/User/Documents/ChatGPT/EveryTune/everytune/static/index.html) e [preferences.js](C:/Users/User/Documents/ChatGPT/EveryTune/everytune/static/preferences.js).

**Evidência:** Corpo POST continua visível com método GET; nome de autorização aparece com autenticação Sem chave; mapeamentos de resultados permanecem na tela quando o tipo escolhido é Pesquisa externa.

**Impacto:** o usuário precisa entender campos que não interferem no conector escolhido, e pode preencher combinações rejeitadas pelo backend.

**Correção:** mostrar corpo apenas para POST, opções de autenticação apenas quando aplicáveis e mapeamento de resultados apenas para conectores integrados. Manter uma opção explícita de edição avançada completa para quem precisa dela.

**Trade-off:** exige regras de exibição e preservação do estado, mas mantém a liberdade de configuração sem impor toda a complexidade a cada uso.

### R13 — Ações repetidas têm nomes acessíveis genéricos

**Severidade: média. Custo: baixo. Nomes confirmados no código; navegação real por leitor de tela ainda não testada.**

**Local:** Preparar arquivo nas linhas do modal e Remover nas fontes instaladas.

**Evidência:** os botões usam o mesmo texto e não incorporam o nome do arquivo/fonte ao nome acessível. O conteúdo visual adjacente fornece contexto para quem vê a linha, mas não distingue os itens em uma lista de botões de tecnologia assistiva.

**Impacto:** identificar qual arquivo será preparado ou qual fonte será removida exige voltar ao conteúdo ao redor.

**Correção:** manter texto visível curto e complementar o nome acessível, por exemplo Preparar arquivo — faixa.flac e Remover fonte — Meu catálogo.

**Trade-off:** descrições longas repetidas seriam cansativas; incluir apenas o identificador útil. As referências são [rótulos descritivos](https://www.w3.org/WAI/WCAG22/Understanding/headings-and-labels.html) e [preservação do texto visível no nome acessível](https://www.w3.org/WAI/WCAG22/Understanding/label-in-name.html). Não declarei falha automática apenas por haver botões com o mesmo texto.

## Grid, temas e elementos visuais que não geraram achados

- O contêiner principal mantém largura máxima e margens coerentes entre busca e ajustes. Não identifiquei desalinhamento sistêmico entre essas visões.
- A 768 px, a divisão em duas colunas aperta a leitura, mas não houve overflow global nem sobreposição confirmada. A escolha de recolher fontes também nesse tamanho deve ser validada como decisão de UX, não apresentada como correção obrigatória.
- Não houve overflow horizontal global nos estados principais. R02 é um problema interno de rolagem, não uma largura errada de todo o documento.
- Os textos normais amostrados nos dois temas passaram no contraste de referência. Não há justificativa para substituir a paleta inteira.
- Há labels nos campos verificados e foco estilizado. O modal fecha por Escape. Isso não equivale a certificar toda a navegação de teclado.
- Não observei distorção nas imagens de teste. O código reserva dimensões e usa `object-fit: cover`, que preserva a proporção e pode recortar o conteúdo, conforme a [documentação MDN](https://developer.mozilla.org/en-US/docs/Web/CSS/Reference/Properties/object-fit). Não foram inspecionadas todas as capas remotas.
- Capas e logo têm `alt` vazio em contextos acompanhados de texto. Isso não é erro automático: é adequado quando a imagem é decorativa ou redundante; se a capa distinguir uma edição, essa informação precisa de alternativa textual. Referência: [imagens decorativas no WAI](https://www.w3.org/WAI/tutorials/images/decorative/).
- O ensaio de espaçamento do texto a 320 px não gerou overflow global no editor. A [WCAG 1.4.12 exige suportar ajustes de espaçamento](https://www.w3.org/WAI/WCAG22/Understanding/text-spacing.html), não usar esses valores como estilo padrão.

## Performance: observação e hipótese

Na navegação local observada, o evento DOMContentLoaded ocorreu em aproximadamente 151 ms; os recursos registrados somaram 98.781 bytes transferidos. Esses números são de uma medição local sem limitação artificial de CPU/rede, não uma média de usuários.

| Lista controlada | Tempo de JavaScript em renderResults | Nós no documento |
|---|---:|---:|
| 30 resultados | 1,9 ms | 1116 |
| 150 resultados | 6,9 ms | 3036 |
| 500 resultados | 20,1 ms | 8636 |

O tempo medido cobre a chamada de JavaScript, não toda a pintura nem o INP. O principal ponto a melhorar é a reconstrução repetida da lista, já tratada em R01. Não encontrei evidência para recomendar a troca do framework, uma biblioteca de virtualização imediata ou uma reescrita da aplicação.

**Hipótese:** em buscas reais, o tempo percebido pode depender mais das fontes externas e do resultado ficar fora da tela do que do carregamento inicial do frontend. Confirmar medindo tempo para o primeiro resultado, `elapsed_ms` das fontes e interações em aparelho real.

Não foram medidos LCP, INP e CLS em condições de campo. A [documentação oficial de Web Vitals](https://web.dev/articles/vitals) distingue essas métricas; os tempos acima não podem ser usados para declarar aprovação nos Core Web Vitals.

## Ordem recomendada de correção

1. **Preservar foco e anunciar estado dos jobs** — R01/R05. Maior efeito sobre operação por teclado; esforço médio.
2. **Proteger restauração e ajustar o destino de Gerenciar fontes** — R04/R11. Ganho alto por alterações pequenas e localizadas.
3. **Corrigir o overflow de 320 px e recolher fontes/filtros no mobile** — R02/R03/R07/R08. A correção CSS é curta; a reorganização requer validar descoberta de controles e foco.
4. **Ajustar contornos, tipografia e alvos** — R06/R09/R10/R13. Preservar identidade e densidade útil, com tokens específicos.
5. **Simplificar condicionalmente o editor** — R12. Custo maior, retorno concentrado em quem configura novas fontes.

Se usados os comandos da skill, a sequência correspondente é `$impeccable harden`, `$impeccable adapt`, `$impeccable clarify` e, depois das correções funcionais, `$impeccable polish`. Eles podem ser aplicados separadamente; não foram executados nesta revisão.

## Limites e pendências de validação

Não houve teste em Safari/iOS, Android físico, NVDA/VoiceOver, controle por voz ou dados de campo. A ampliação de texto foi simulada no CSSOM; confirmar zoom nativo antes de concluir conformidade 1.4.4. Não foram exercitadas todas as imagens remotas, integrações autenticadas ou transferências grandes. As observações de leitor de tela são inferências a partir de foco, nomes e semântica, quando não explicitamente medidas.

A documentação PRODUCT.md usa um formato antigo do registro da skill. `$impeccable init` pode atualizar esse registro, caso solicitado; isso não é um defeito visual nem altera os achados desta auditoria.
