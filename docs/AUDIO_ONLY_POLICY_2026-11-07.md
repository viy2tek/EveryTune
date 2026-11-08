# Somente resultados com áudio e arquivos de mídia

Pedido: retirar catálogo e qualquer resultado sem áudio da lista e de sua contagem; permitir apenas áudio e imagem nos arquivos.

## Comportamento

- A home envia `require_audio: true`; esse também é o padrão da API de pesquisa. Fontes conhecidas que só oferecem catálogo são excluídas da consulta e da lista de seleção da home.
- Após conferir nomes/versões, o servidor resolve as opções do candidato e exige ao menos uma opção de áudio direto, com destino permitido e resposta HEAD compatível e não declarada vazia. Espelhos declarados como áudio só passam depois de confirmação como arquivo direto. Não há GET do áudio durante a pesquisa.
- Somente após essa verificação o resultado recebe `audio_available: true` e é enviado à home. O contador é calculado a partir desses resultados. Cache de metadados não dispensa a verificação. Resolução e HEAD têm concorrência e orçamento de tempo limitados; falha de um candidato preserva os demais que passaram.
- Atalhos de pesquisa externa sem áudio verificado também ficam fora da home; não são tratados como resultados baixáveis.
- A interface também aplica a guarda Bend `audio_result` aos resultados recebidos. Um item só de imagens, sem arquivo, com HTML no lugar de áudio, inacessível ou sem confirmação fica fora, não em uma categoria concorrente de catálogo.
- Imagens podem acompanhar resultados que tenham áudio. O manifesto só apresenta arquivos de áudio reconhecidos e imagens; não apresenta PDF, XML, texto, vídeo, arquivos de projeto, MIDI, trackers, arquivos compactados da origem ou outros tipos.
- Preparação revalida os IDs e tipos no servidor. MIME incompatível ou nome final incompatível devolvido pela origem produz falha com limpeza dos parciais. A filtragem não depende apenas da interface.
- O ZIP local continua disponível para reunir a seleção de áudios e imagens. Não se trata de aceitar ZIP/RAR da origem, cujo conteúdo não foi inspecionado.
- `require_audio: false` preserva consultas de metadados para integrações de API e testes específicos; não há essa opção na home. Esses dados não passam pela guarda de exibição de áudio da interface.

## Limites da confirmação

HEAD comprova uma resposta de arquivo naquele momento, não codec, integridade, autoria, upload oficial ou disponibilidade permanente. A transferência valida novamente a resposta e os limites de bytes. Fontes que recusam HEAD ou exigem interação externa não entram como disponíveis, mesmo que o usuário consiga acessá-las manualmente. Não há conversão de streams, extração de ZIP ou contorno de acesso.

## Verificação

- 184 testes Python: disponibilidade antes da contagem, imagem isolada excluída, áudio quebrado/HTML excluídos, cache rechecado, HEAD sem leitura de mídia, tipos ocultos recusados via API, MIME/nome inválidos e seleção exata de ZIP de áudio.
- Guardas `audio_result` e `allowed_file` no módulo Bend emitido; duas leis parciais adicionais. As provas não cobrem HTTP nem o servidor Python.
- Regressões de home e UX: política enviada pela busca, fonte de streaming com download, fila, seleção de arquivos, metadados sem áudio excluídos sem contagem e comportamento responsivo.
- Teste live voltou a preparar/servir o MP3 de Magic Juand com 4.573.184 bytes; a consulta de XXXTENTACION não retornou áudios confirmados na amostra Openverse, e iTunes foi excluído por ser catálogo.
- Executável atualizado em `dist/audio-only/EveryTune.exe`, aprovado nos testes da home e na transferência real. A versão anterior pode permanecer aberta, mas deve ser encerrada antes de usar esta para evitar confusão entre interfaces.

Não foi reavaliada toda a disponibilidade externa de todos os provedores. A checagem adicional BendTT/Lean continua pendente conforme os relatórios anteriores.
