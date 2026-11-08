# Plano de simplificação da página inicial

Data: 06/11/2026. Entrega de planejamento: nenhuma alteração da interface.

## Premissas e evidência

Base: código atual de `everytune/static/index.html`, `app.js`, `downloads.js`, PRODUCT.md, DESIGN.md e auditorias anteriores. Objetivo principal assumido, conforme a conversa: encontrar a gravação correta e salvar um arquivo oferecido pela origem. Uso pessoal em português, desktop e celular; usuários recorrentes precisam manter seleção de fontes, créditos e configurações avançadas.

Não há dados de uso, mapa de calor ou teste com participantes que comprovem abandono ou tempo perdido. O diagnóstico abaixo é inspeção de interface/código. Espaçamentos, limites visuais e metas de melhoria são propostas, não resultados medidos.

## Decisão principal

Uma coluna, busca dominante e opções secundárias sob demanda. A ação inicial prioritária é **Buscar**. Depois da consulta, a interface prioriza identificar a gravação e verificar arquivos. Só apresenta **Salvar arquivo** quando a preparação termina. Não tenta resolver a ausência de downloads com destaque visual ou resultados de outros artistas.

## Cortes, agrupamentos e trade-offs

| Atual | Decisão e prioridade | Custo e efeito esperado | Trade-off e validação |
|---|---|---|---|
| Slogan, descrição, rodapé explicativo da busca, vazio ilustrado e sugestões de artistas dizem coisas próximas | P1: substituir por título funcional “Buscar música ou artista”, campo e um exemplo de entrada; remover ilustração e sugestões genéricas | Baixo: menos mensagens antes da tarefa | Menos ajuda para exploração; observar sucesso na primeira busca e pedidos de ajuda |
| Sidebar expõe escolha técnica e dezenas de fontes no desktop | P1: remover sidebar permanente; manter controle de foco **Ambas / Streaming / Comunidade** e uma entrada **Opções de busca** | Médio: a escolha de grupo continua direta; a lista individual deixa de competir com resultados | Seleção individual ganha uma abertura; medir tempo de mudar fonte e erros de escopo |
| Contagens e títulos de fontes repetidos em múltiplos lugares | P1: um resumo de seleção; status detalhado dentro do painel de opções/diagnóstico | Baixo: menos repetição | Não esconder falta de credenciais: resumo deve indicar fontes sem acesso quando isso afeta a busca |
| Modo, texto de ajuda, campos separados, versões e filtros ficam espalhados | P1: agrupar controles da consulta em Opções; filtros de resultados aparecem somente após haver resultados | Médio: menos decisões antes de digitar | Créditos e busca bruta ficam menos visíveis; usar rótulos explícitos e mostrar resumo do modo ativo |
| Histórico, exemplos e estado vazio competem | P2: até três buscas recentes reais somente antes de pesquisar; sem histórico, nenhum bloco substituto | Baixo: reaproveita histórico existente | Menos itens imediatamente disponíveis; histórico completo pode continuar no acesso secundário, sem criar autocomplete remoto |
| Muitos links, selos, monogramas e ações por resultado | P1: título/artista primeiro; versão e origem depois; uma ação contextual por linha, detalhes sob demanda | Médio: comparação mais direta | Mais um passo para detalhes de créditos/licença; não esconder versão que diferencie gravações |
| Modal de arquivos mistura seleção com inspeção manual de URL | P2: painel de arquivos associado ao resultado; inspeção manual fica na área Fontes/Ajustes | Alto: mantém o contexto da gravação durante a escolha | Painel expandido aumenta rolagem; abrir só um painel por vez e preservar seleção ao fechar |
| Downloads, preparo e catálogo podem parecer equivalentes | P0: estados distintos e rótulos específicos, independentemente da limpeza visual | Médio: evita ação sem resultado útil | Mais estados na implementação; medir tentativas de baixar itens que são apenas catálogo |

A redução busca retirar informação secundária do primeiro plano, não simplesmente aumentar espaços. A heurística de design minimalista trata da competição entre informações relevantes e irrelevantes ([NN/G](https://www.nngroup.com/articles/aesthetic-minimalist-design/)). Expor opções avançadas mediante solicitação segue divulgação progressiva, com o custo explícito de reduzir sua descoberta imediata ([NN/G](https://www.nngroup.com/articles/progressive-disclosure/)).

## Estrutura proposta

```text
EveryTune                                  Downloads (n)   Ajustes

Buscar música ou artista
[ Artista ou Artista - Faixa…                         ] [Buscar]
Fontes: [Ambas | Streaming | Comunidade]   Opções de busca
Resumo: nomes conferidos · covers identificados ocultos

Antes de pesquisar: recentes, quando existirem
Depois de pesquisar: progresso resumido → resultados

Resultados                                 Filtrar resultados
Título da gravação · versão
Artista · álbum / duração
Origem · situação do arquivo                Ação contextual
```

- Sem hero e estado vazio simultâneos. O espaço de resultados não ocupa um bloco ilustrado antes da primeira consulta.
- Sem sidebar fixa em qualquer largura. O painel Opções usa expansão inline; no celular, fica na mesma sequência de leitura.
- Dentro de Opções: modo de busca, artista/título explícitos, política de covers e seleção individual por grupo. Manter o foco entre streaming/comunidade e as marcações do outro grupo.
- Créditos: modo acessível pelo painel, com identidades ambíguas apresentadas separadamente. O objetivo especializado não pode ser apagado pelo foco em downloads.
- Catálogo sem arquivo fica identificado. Filtro de disponibilidade distingue arquivo informado de arquivo efetivamente preparado; não promover metadados para sucesso.
- Atalhos de teclado para pular conteúdo continuam disponíveis, mas aparecem visualmente ao receber foco, sem ocupar linhas permanentes.

## Workflow por estado

1. **Inicial:** digitar e pressionar Enter. Nenhuma configuração obrigatória se houver fontes aptas. Se não houver, mostrar a causa e o caminho específico para configurar.
2. **Pesquisando:** manter campo, consulta e foco. Exibir um resumo de progresso e Cancelar; erros por fonte ficam agrupados, com aviso visível quando afetarem a possibilidade de obter arquivos.
3. **Resultados:** identificar título + artista + versão. Filtrar é opcional. Um item sem referência de arquivos mostra Somente catálogo; um item não resolvido oferece **Ver arquivos**, sem promessa de baixar.
4. **Verificando arquivos:** expansão no próprio item, com indicador local. Erro permanece nesse contexto e permite tentar novamente ou abrir a origem.
5. **Escolhendo:** formato, tamanho quando conhecido e condições de uso junto das opções. Para um original: escolher **Preparar MP3**, por exemplo. Para pacote: selecionar arquivos antes de habilitar **Preparar ZIP**. Preservar o ZIP por item/álbum existente; não criar cesta entre fontes.
6. **Preparando:** fila continua em segundo plano, sem exigir abrir Downloads. Exibir progresso e cancelamento no item e acesso à fila.
7. **Pronto:** mostrar **Salvar arquivo**. Não fazer segundo download automático nem presumir que a gravação já foi salva no disco.
8. **Sem resultado/sem arquivo:** distinguir ausência de correspondência, arquivo não oferecido, acesso necessário e falha. Propor uma ação compatível com a causa; não usar covers como substituição silenciosa.

O fluxo elimina o desvio obrigatório ao modal/inspeção manual, mas mantém a escolha antes do ZIP e o gesto de salvar do navegador. Informar estados de forma compreensível reduz a incerteza da operação; esconder progresso para parecer minimalista seria uma regressão ([NN/G](https://www.nngroup.com/articles/visibility-system-status/)).

## Regras visuais propostas

- Preservar a família tipográfica local e a identidade de papel quente/verde petróleo. Proposta de escala: texto principal 16 px, apoio 14 px e um título de página entre 24–32 px; verificar textos reais antes de fixar.
- Um único estilo preenchido para a ação prioritária da etapa; ações de origem, detalhes e configurações recebem menor ênfase. Várias linhas de resultado não viram vários botões verdes competindo.
- Verde para ação; neutros para estrutura; cores de erro/foco reservadas à sua função. Evitar cor diferente para cada plataforma.
- Espaçamento em escala 8/16/24/32, com mais distância entre etapas que entre título e artista. Esses números são ponto de partida de composição, não requisito normativo.
- Lista como apresentação inicial. Grade continua preferência, sem seletor extra no primeiro plano. Capas pequenas, proporcionais e opcionais; não ampliar arte para preencher a tela.
- Expandir opções com controle semanticamente identificado, operável por teclado e com estado expandido exposto. Se usar botão personalizado, seguir o padrão de disclosure da [W3C APG](https://www.w3.org/WAI/ARIA/apg/patterns/disclosure/).

## Bend 2: organização e limite real

Ver [parecer de viabilidade](BEND_HOME_FEASIBILITY_2026-11-06.md). Bend 2.0.40 emite `.mjs`; isso não demonstra uma API nativa de DOM/CSS. A nova lógica pode ter origem em Bend, mas a alternativa web demonstrada exige HTML/CSS e um adaptador de navegador. Portanto **não é uma implementação literalmente sem código externo ao Bend**. Se a proibição dessa ponte for obrigatória, a viabilidade fica pendente; o plano não autoriza substituí-la silenciosamente por JavaScript.

Arquitetura proposta caso a ponte mínima seja aceita:

```text
ui/home/model.bend    tipos, estado, eventos, transições e decisões de ação
ui/home/view.bend     composição da busca, opções, resultados e painel de arquivos
ui/home/styles.bend   tokens e emissão dos estilos comuns da home
ui/home/main.bend     exports utilizados pelo navegador
static/home-adapter.js integração DOM/eventos/HTTP, sem regras de produto duplicadas
LAWS.bend             requisitos e novas leis parciais explicitamente delimitadas
PROOF.bend            provas que importam a implementação realmente distribuída
```

Não criar um arquivo por botão. Cada módulo concentra uma responsabilidade e expõe uma interface pequena. Interface principal proposta: `update(state, event)` produz novo estado e comandos; `view(state)` produz descrição da apresentação. O adaptador executa comandos de DOM/rede e devolve respostas como eventos. Dados externos entram como texto, não HTML executável; renderização deve preservar links seguros, foco e nós inalterados.

Estados explícitos: inicial, buscando, sem correspondência, resultados, verificando arquivos, escolhendo, preparando, pronto e falha. Respostas carregam identidade da consulta/tarefa; eventos antigos não substituem a busca atual. Nenhuma enumeração de estado confere autorização de download: o servidor continua validando IDs, seleção e destino.

Reaproveitar os endpoints Python, federação e preparação existentes. Migrar a home por inteiro para um único dono do estado; remover handlers antigos correspondentes em app.js/downloads.js quando a substituição estiver pronta. Preferências, conectores e servidor ficam fora do redesenho, sem renomear sua implementação Python como Bend.

Build: verificar `PROOF.bend`, gerar o módulo real e os estilos, empacotar os artefatos no executável. O precedente é `scripts/build_ui_policy.py`; estendê-lo ou substituí-lo em um único ponto, sem dois pipelines concorrentes. Não distribuir WSL/Bend ao usuário final.

Leis candidatas: seleção vazia não habilita ZIP; estado pronto exige evento da tarefa correta; resposta de busca antiga não altera a atual; catálogo não apresenta ação de salvar. Provar apenas funções usadas pela home emitida e preservar os requisitos existentes. Provas não substituem Python, DOM ou testes de transferência. `--verdict` continua dependente do Lean compatível, ausente na verificação anterior.

## Ordem executável e critérios de saída

1. **Contrato e viabilidade:** conferir os eventos/endpoints usados, capturar a linha de base de tarefas e provar a importação de um módulo Bend no navegador com a CSP existente. Resolver a exigência literal de linguagem antes de migrar a tela.
2. **Estrutura inicial:** retirar duplicações, substituir sidebar por foco + Opções, manter preferências e busca por nomes. Saída: pesquisar sem abrir configurações; grupos/seleção individual continuam acessíveis.
3. **Resultados e arquivos:** compor as linhas e o painel contextual com os estados acima. Saída: original e ZIP selecionado chegam a Salvar arquivo sem desvio para inspeção manual; catálogo não oferece falso download.
4. **Substituição e regressão:** remover a lógica antiga da home e estilos órfãos; atualizar smoke tests existentes. Saída: testes Python pertinentes, módulo Bend emitido, teclado/foco, consultas atrasadas/cancelamento, 320–1440 px e ambos os temas aprovados.
5. **Validação de uso e build:** comparar tarefas na interface anterior e proposta, corrigir falhas observadas e verificar uma transferência real no executável. Não anunciar ganho de usabilidade somente porque o build passou.

## Medição proposta

Antes/depois com as mesmas tarefas e respostas controladas, alternando a ordem entre participantes: encontrar uma faixa, pesquisar um artista, mudar o foco de fontes, selecionar dois arquivos para ZIP, buscar créditos e interpretar ausência de arquivo. Repetir transferência real separadamente para verificar a integração.

- Tempo da página pronta até a primeira busca enviada; taxa de busca enviada sem entrar em ajustes.
- Tempo e número de ações de resultado até solicitação de salvamento, em tarefas cujo arquivo existe.
- Taxa global de pesquisa → solicitação de salvamento, incluindo falta de disponibilidade; registrar essa causa separadamente.
- Seleção do artista/versão errados; tentativas de baixar itens só de catálogo; sucesso ao localizar Opções e créditos.
- Separar tempo esperando a fonte do tempo de interação. Usar a mesma consulta/resposta para não atribuir ao layout uma diferença do catálogo.

Hipóteses de aceitação a calibrar após a linha de base: reduzir em 20% a mediana de ações entre resultado e salvar, sem reduzir sucesso na troca de fontes/créditos; zero salvamento de versão errada nas tarefas controladas. Não são estimativas de ganho já demonstrado.

Com o uso pessoal atual, testes de tarefas e observação são mais úteis inicialmente que um A/B com amostra pequena. A/B só depois de haver sessões independentes suficientes e critérios definidos. Mapas de calor, se usados, são complemento: cliques não explicam a intenção. Métricas locais e opcionais, sem registrar consultas, credenciais ou conteúdo pessoal; nenhuma telemetria externa é necessária para validar o plano.
