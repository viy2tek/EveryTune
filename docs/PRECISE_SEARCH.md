# Busca estrita por artista e faixa — 05/11/2026

A correção combina recuperação por campos e conferência local obrigatória. Não é uma
reprodução da implementação privada dos streamings; usa recursos públicos documentados:

- [Spotify](https://developer.spotify.com/documentation/web-api/reference/search):
  `artist` e `track` juntos, com `market=BR`.
- [MusicBrainz](https://musicbrainz.org/doc/MusicBrainz_API/Search/RecordingSearch):
  `artist:"…" AND recording:"…"`.
- [Last.fm](https://www.last.fm/api/show/track.search): `track` e `artist` separados.
- [Apple Search](https://performance-partners.apple.com/search-api) e
  [Lookup](https://developer.apple.com/library/archive/documentation/AudioVideo/Conceptual/iTuneSearchAPI/LookupExamples.html):
  `songTerm` para título; o artista principal é conferido pelo `artistId` via lookup
  em lote quando há artista informado. O intervalo de requisições continua respeitado.

`Soft Pillow Kisses - Stolen Flowers` é artista primeiro, faixa depois. Campos separados
prevalecem e permitem nomes com hífen. A interpretação fica visível. Sem separador/campos,
o nome completo precisa coincidir com título, artista ou álbum. Não se adivinha a fronteira
entre dois nomes. Maiúsculas, acentos e pontuação são normalizados; erros de grafia, Live,
Remastered, Remix e créditos adicionais do título não são relaxados automaticamente.

Ambos os campos precisam coincidir no mesmo resultado. Os artistas individuais precisam
vir da API ou lookup oficial; não dividimos bandas por vírgula, “&” ou “feat”. Uploader
não é presumido como intérprete. Mixes, acervos e arquivos sem identificação de faixa
não são certificados como o par solicitado. O filtro atua antes dos eventos e também
no cache, cujas chaves incluem estratégia e campos. Paginação permanece explícita.

“Sem resultados” significa resposta vazia; “Sem correspondência”, candidatos rejeitados.
“Relacionada” foi removido. Erros/credenciais ficam separados. A contagem distingue fontes
avaliadas das que possuem acesso para consulta. Links aceitos continuam preservados.

[Evidência real](precise-smoke.json), com limite de 15 candidatos por fonte:

- Consulta relatada: zero correspondências; 15 candidatos alheios do iTunes rejeitados.
- `Daft Punk - Get Lucky`: 7 links de iTunes e MusicBrainz com artista e título conferidos.

68 testes passam, incluindo rejeição de banda/faixa erradas, artista ausente, diferenças
normalizadas, Live/Remastered, créditos, lookup iTunes, campos das APIs e cache separado.
O teste de navegador verifica a regressão e o preenchimento apenas dos campos separados.

Precisão tem prioridade: metadados incompletos, aliases, homônimos, títulos com créditos,
limites de página, bloqueios e regiões podem causar omissões. Resultado vazio não prova
que a música não existe. Correspondência textual não garante gravação/master idênticos.
As APIs com credenciais continuam sem teste real por falta de acesso próprio.

O histórico continua textual: para nomes que contêm o próprio separador ` - `, confira
a interpretação e preencha novamente os campos separados ao reutilizar uma busca recente.
