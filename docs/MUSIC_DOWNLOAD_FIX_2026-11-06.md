# Busca por identidade e download Openverse

## Causa reproduzida

Busca informada: `xxxtentacion`. Os prints estavam no modo de resposta bruta (`source`), que não conferia artista/título. O Openverse retornou um cover de WARET e faixas de Magic Juand, que não comprovam relação com o artista pesquisado.

O conector anunciava download com base em URL/licença na resposta, mas descartava a URL do arquivo. O resolvedor caía no parser HTML genérico da página do Jamendo; não havia integração de download nativa para o Openverse. A API possui campos separados para a página (`foreign_landing_url`) e o áudio (`url`). Referência: [documentação Openverse](https://docs.openverse.org/meta/media_properties/api.html).

## Correções

- `exclude_covers`, ligado por padrão, aplica-se também a resultados em cache e ao modo de exploração. Marcadores explícitos de cover prevalecem sobre a palavra remix no mesmo título. A opção pode ser ajustada na busca e nas preferências.
- A detecção não usa a palavra cover isoladamente em qualquer posição: títulos como “Cover Me” e “Under Cover” não são excluídos por esse motivo. Não há identificação acústica; covers sem marcação podem passar. Um remix mantém sua identificação e continua sujeito às regras de identidade do modo escolhido; não é transformado em correspondência exata de uma versão diferente.
- A busca inicial padrão passa a ser `auto`, que exige correspondência de nome/artista. A preferência desta máquina foi ajustada explicitamente para `auto` e exclusão de covers, preservando os demais ajustes. Perfis de outras máquinas mantêm suas escolhas persistidas; podem mudar Busca inicial nas preferências.
- O modo `source` continua disponível e informa que pode retornar outros artistas. O filtro de covers não o transforma em confirmação de nomes.
- SoundCloud agora preserva o nome do usuário informado como artista nos metadados do adaptador; isso não comprova identidade oficial da conta.
- Openverse tem resolução nativa: consulta o registro por ID novamente, valida identidade e licença, extrai URL principal e alternativas, reconhece MP3 declarado como `mp31`/`mp32`, e usa o transporte de downloads com validação de destinos, limites e cancelamento existentes.
- Arquivos alternativos inválidos são descartados sem perder os válidos. A origem e as condições de licença permanecem no painel. Uma licença declarada não comprova upload oficial nem autoria da gravação.
- Catálogos sem exportação (incluindo iTunes/Apple, Spotify e YouTube neste aplicativo) não recebem referência para abrir um painel de download vazio. A interface informa “Somente catálogo”.
- O rótulo de disponibilidade passa a dizer “Download informado pela origem”, distinguindo metadados de uma transferência concluída.

## Evidência

- 181 testes Python passaram, incluindo filtro de cover/remix, artista incorreto, preservação de títulos legítimos, formatos alternativos, recusa de destinos privados e identidade/licença revalidadas, fluxo de preparo e bytes originais, e ausência de ação de download para catálogos.
- Regressão UX nas seis larguras e dois temas passou, sem erros JavaScript nos estados cobertos.
- O executável atualizado foi gerado em `dist/updated/EveryTune.exe`, pois o executável anterior estava aberto e bloqueado pelo Windows. Ele passou pela regressão UX e pela mesma consulta/transferência real. Feche a versão anterior antes de abrir a nova.
- `scripts/music_download_smoke.py` faz consultas e transferência reais, sem respostas simuladas, em dados isolados.
- Para `xxxtentacion`, a consulta a iTunes/Openverse retornou oito registros com artista correspondente no iTunes e descartou os três candidatos do Openverse. Essa amostra não encontrou arquivo original exportável do artista, e não representa auditoria de todas as fontes.
- O exemplo do print, `Magic Juand - Rockstars (Instrumental) [Produced by Magic Juand]`, foi localizado pelo Openverse, resolvido, preparado e servido como MP3 de **4.573.184 bytes**; estado `ready`, cabeçalho MP3 e hash SHA-256 registrados em `artifacts/music-download-live.json`. O áudio foi usado somente na área temporária do teste e não incluído no repositório.

Os requisitos originais de busca estrita, origem, isolamento de falhas, seleção de arquivos e transporte público foram preservados. O Bend existente continua cobrindo a política do editor; não se atribui a essas provas a validação dos conectores ou do áudio.

Limites: não há prova automática de upload oficial em fontes que não a fornecem; contas com nome semelhante ou títulos dizendo “official” não recebem selo inventado. Os testes não garantem disponibilidade de músicas específicas nem acesso a fontes que exijam configuração ou interação externa.
