# Auditoria automática de links FMHY Audio

Data UTC: 2026-11-05T18:42:36+00:00. Alvos processados: **1188/1188**. Inventário original: 1.188 URLs únicas; JUMO incluído como referência adicional quando ausente.

Esta é uma inspeção de metadados públicos, não validação manual de cada serviço nem 1.188 integrações. Nenhum áudio, executável ou script remoto foi executado. Bloqueios, CAPTCHA, autenticação e robots não foram contornados. Páginas JS não foram executadas pelo auditor: ausência de form HTML não prova ausência de busca. Encontrar um form não verifica autorização para scraping, API ou incorporação de resultados.

## Cobertura

| Situação | Quantidade |
|---|---:|
| html_inspected | 1017 |
| http_blocked | 39 |
| http_error | 1 |
| network_error | 6 |
| non_html_resource | 4 |
| redirect_limit | 1 |
| robots_disallowed | 85 |
| robots_unavailable | 28 |
| timeout | 6 |
| unsafe_destination | 1 |

## Tipo de página observado

| Tipo | Quantidade |
|---|---:|
| tool_or_related_service | 302 |
| website_with_javascript | 286 |
| radio_podcast_or_ambient | 180 |
| não classificado por acesso/conteúdo | 171 |
| repository_or_software | 120 |
| public_search_form_candidate | 94 |
| website_unclassified | 35 |

## Auditoria das barras de pesquisa

[search-audit.json](search-audit.json): 94/94 páginas de catálogos com forms GET processadas; 97 consultas de formulário registradas. Cada formulário navegável foi inspecionado novamente para recuperar parâmetros fixos, e cada URL de busca passou por robots/DNS/limites de corpo. HTTP 200 ou eco do termo não prova que um catálogo tem a faixa correta; JSON-LD/microdata e possíveis campos HTML são apenas evidências, não equivalem a um adaptador validado.

| Resultado da consulta | Quantidade |
|---|---:|
| fetched | 66 |
| http_error | 4 |
| query_error | 1 |
| robots_disallowed | 26 |

## Verificações de busca de catálogo

Estas consultas foram executadas em páginas de resultados reais, com robots permitido e sem áudio. Os presets HTML continuam sujeitos a mudanças e às condições do site; a inspeção não é uma API oficial nem uma autorização jurídica de reprodução.

| Fonte | Consulta / evidência | Resultado observado / preset |
|---|---|---|
| UCSB Cylinders | [Kathleen Parlow](https://cylinders.library.ucsb.edu/search.php?query=Kathleen+Parlow&query_type=keyword&nq=1) | 5 registros; título, performers e ano observados; preset HTML de acervo |
| CitizenFreak | [Rush](https://citizenfreak.com/search?q=Rush) | busca real por seções; cartões de títulos sem artista; somente externo |
| ⁠OC Remix | [Avitron](https://ocremix.org/quicksearch/remix/?qs_query=Avitron) | 1 remix; Arranged by Avitron e Chris ~ Amaterasu explícito; preset HTML |
| VGMRips | [Koji Kondo](https://vgmrips.net/packs/search?q=Koji+Kondo) | 20 packs na primeira página; Composer: Koji Kondo explícito; preset HTML de álbum |

Presets: [source_presets.json](../everytune/data/source_presets.json). Fixtures sanitizadas em `tests/fixtures/catalogue_ucsb.html`, `catalogue_vgmrips.html` e `catalogue_ocremix.html`, preservando 1–2 registros observados, sem scripts, previews ou links de download. Os campos de créditos constantes (=Performer, =Composer, =Arranger) refletem rótulos efetivamente vistos. Compositores/arranjadores não são apresentados como cantores.

UCSB exige `nq=1` junto de `query_type=keyword`; sem `nq`, a consulta de teste devolveu o catálogo inteiro e foi rejeitada como validação de busca. CitizenFreak devolve títulos sem artista no próprio cartão: mantido como externo para não inventar a atribuição. OC ReMix `/site-search/` usa Google/JavaScript; o preset usa o formulário HTML específico `/quicksearch/remix/`, cuja resposta foi verificada. VGMRips retorna packs/álbuns e seus compositores, não faixas individuais.

## Candidatos com formulário GET observado

Todos os candidatos são apenas evidência de navegação externa; cada integração precisa de validação de resultado, termos, paginação e identidade dos créditos. A lista completa, incluindo bloqueios e scripts de SPA a inspecionar, está em [source-audit.json](source-audit.json).

| Página | Seção FMHY | Evidência de pesquisa |
|---|---|---|
| [Wiki Comparisons](https://wikipedia.org/wiki/Comparison_of_music_streaming_services) | Streaming Apps | GET `https://en.wikipedia.org/w/index.php` com `search`, `title` |
| [The 120 Minutes Archive](https://altmusictv.com/) | Streaming Sites | GET `https://altmusictv.com/` com `q`; GET `https://altmusictv.com/` com `q` |
| [⁠unmusic](https://unmusic.xyz/) | Streaming Sites | GET `https://unmusic.xyz/p/` com `q` |
| [Hype Machine](https://hypem.com/popular) | Streaming Sites | GET `https://hypem.com/search` com `q` |
| [UCSB Cylinders](https://cylinders.library.ucsb.edu/index.php) | Specialty Streaming | GET `https://cylinders.library.ucsb.edu/search.php` com `query` |
| [Irama Nusantara](https://www.iramanusantara.org/en) | Specialty Streaming | GET `https://www.iramanusantara.org/en` com `keyword`; GET `https://www.iramanusantara.org/en` com `keyword` |
| [setlist.fm](https://www.setlist.fm/) | Concerts / Live Shows | GET `https://www.setlist.fm/search` com `query` |
| [CitizenFreak](https://citizenfreak.com/) | Specialty Streaming | GET `https://citizenfreak.com/search` com `q` |
| [LiveBootlegConcert](https://livebootlegconcert.blogspot.com/) | Concerts / Live Shows | GET `https://livebootlegconcert.blogspot.com/search` com `q` |
| [Volume](https://volume.com/) | Concerts / Live Shows | GET `https://volume.com/search/` com `q` |
| [WorldConcertHall](https://www.worldconcerthall.com/en/schedule-list/) | Concerts / Live Shows | GET `https://www.google.com/search` com `q` |
| [OperaOnVideo](https://www.operaonvideo.com/) | Concerts / Live Shows | GET `https://www.operaonvideo.com/` com `s` |
| [NTS Radio](https://www.nts.live/) | DJ Mixes / Livesets | GET `https://www.nts.live/` com `q` |
| [Konserthuset](https://www.konserthuset.se/en/play/) | Concerts / Live Shows | GET `https://www.konserthuset.se/en/search-on-konserthuset.se` com `q`; GET `https://www.konserthuset.se/en/search-on-konserthuset.se` com `q` |
| [⁠HD Mixtapes](https://hdmixtapes.org/) | DJ Mixes / Livesets | GET `https://hdmixtapes.org/search` com `q`; GET `https://hdmixtapes.org/search` com `q` |
| [TopDJMixes](https://topdjmixes.com/) | DJ Mixes / Livesets | GET `https://www.topdjmixes.com/` com `s`; GET `https://www.topdjmixes.com/` com `s` |
| [Core Radio](https://coreradio.online/) | Download Sites | GET `https://coreradio.online/` com `story` |
| [DiscogC](https://www.discogc.com/) | Download Sites | GET `https://www.discogc.com/#` com `phrase` |
| [FlacMusic](https://www.flacmusic.info/) | Download Sites | GET `https://www.flacmusic.info/index.php` com `story` |
| [ThemFire](https://themfire.pro/) | Download Sites | GET `https://themfire.pro/` com `s` |
| [IntMusic](https://intmusic.net/) | Download Sites | GET `https://intmusic.net` com `s` |
| [Exystence](https://exystence.net/) | Download Sites | GET `https://exystence.net/` com `s`; GET `https://exystence.net/` com `s` |
| [iPlusFree](https://www7.iplusfree.org/) | Download Sites | GET `https://www7.iplusfree.org/` com `s` |
| [Music Rider](https://musicrider.org/) | Download Sites | GET `https://musicrider.org` com `s` |
| [SongsLover](https://songslover.net/) | Download Sites | GET `https://songslover.net/` com `s`; GET `https://songslover.net/` com `s` |
| [RockDownload](https://www.rockdownload.org/) | Download Sites | GET `https://www.rockdownload.org/` com `s`; GET `https://www.rockdownload.org/` com `s` |
| [z3.fm](https://z3.fm/) | Download Sites | GET `https://z3.fm/mp3/search` com `keywords` |
| [nodata](https://nodata.tv/) | Download Sites | GET `https://nodata.tv` com `s` |
| [Discografias Completas](https://www.discografias-completas.org/) | Download Sites | GET `https://www.discografias-completas.org/#` com `phrase` |
| [mp3db](https://mp3db.pro/) | Download Sites | GET `https://mp3db.pro/search.php` com `s` |
| [⁠Butterboy Compilations](https://butterboycompilations.blogspot.com/) | Download Sites | GET `https://butterboycompilations.blogspot.com/search` com `q` |
| [⁠Primitive Offerings](https://primitiveofferings.blogspot.com/) | Download Sites | GET `https://primitiveofferings.blogspot.com/search` com `q` |
| [FreeMIDI](https://freemidi.org/) | Download Sites | GET `https://freemidi.org/search` com `q`; GET `https://freemidi.org/search` com `q` |
| [Wiki](https://musichoarders.xyz/) | Download Sites | GET `https://musichoarders.xyz/` com `query` |
| [GloryBeats](https://glorybeats.com/) | Download Sites | GET `https://glorybeats.com/` com `s` |
| [PandaCD](https://pandacd.io/) | Audio Torrenting | GET `https://pandacd.io/index.php` com `search` |
| [TribalMixes](https://www.tribalmixes.com/) | Audio Torrenting | GET `https://www.tribalmixes.com/browse.php` com `search`; GET `https://www.tribalmixes.com/browse.php` com `search` |
| [Unminus](https://www.unminus.com/) | Royalty Free Music | GET `https://www.unminus.com/search` com `query`; GET `https://www.unminus.com/search` com `query` |
| [⁠Sound Image](https://soundimage.org/) | Royalty Free Music | GET `https://soundimage.org/` com `s` |
| [free-stock-music](https://www.free-stock-music.com/) | Royalty Free Music | GET `https://www.free-stock-music.com/search.php` com `keyword` |
| [⁠OpenTracks](https://opentracks.com/en/) | Royalty Free Music | GET `https://opentracks.com/en/bgm` com `keywords`; GET `https://opentracks.com/en/se` com `keywords` |
| [Search](https://vgm.hcs64.com/) | Media Soundtracks | GET `https://vgm.hcs64.com/` com `text` |
| [RenovationRecords](https://renovatiorecords.blogspot.com/) | Media Soundtracks | GET `https://renovatiorecords.blogspot.com/search` com `q` |
| [Sitting on Clouds](https://www.sittingonclouds.net/) | Media Soundtracks | GET `https://www.sittingonclouds.net/` com `query` |
| [SakuraOST](https://www.sakuraost.com/) | Media Soundtracks | GET `https://www.sakuraost.com/search` com `q` |
| [⁠OC Remix](https://ocremix.org/) | Game Soundtracks | GET `https://ocremix.org/site-search/` com `q` |
| [The 16-bit Audiophile Project](https://16bap.theclassicgamer.net/) | Game Soundtracks | GET `https://16bap.theclassicgamer.net/` com `s` |
| [VGMRips](https://vgmrips.net/packs/) | Game Soundtracks | GET `https://vgmrips.net/packs/search` com `q` |
| [2](https://sittingonclouds.com/) | Media Soundtracks | GET `https://www.sittingonclouds.com/` com `query` |
| [Zophar's Domain](https://www.zophar.net/music) | Game Soundtracks | GET `https://www.zophar.net/music/search` com `search`; GET `https://www.zophar.net/music/search` com `search` |
| [⁠CVGM](https://www.cvgm.net/) | Game Soundtracks | GET `https://www.cvgm.net/search/` com `q` |
| [Last.fm](https://www.last.fm/home) | Tracking / Databases | GET `https://www.last.fm/search` com `q`; GET `https://www.last.fm/search` com `q` |
| [VGMPF](https://www.vgmpf.com/Wiki/index.php) | Game Soundtracks | GET `https://www.vgmpf.com/Wiki/index.php` com `search`, `title` |
| [Has it Leaked](https://hasitleaked.com/) | Tracking / Databases | GET `https://hasitleaked.com/` com `s`; GET `https://hasitleaked.com/` com `s` |
| [MusicBrainz](https://musicbrainz.org/) | Tracking / Databases | GET `https://musicbrainz.org/search` com `query` |
| [SoundtrackTracklist](https://soundtracktracklist.com/) | Tracking / Databases | GET `https://soundtracktracklist.com/` com `s` |
| [ClassicRockHistory](https://www.classicrockhistory.com/classic-rock-bands-list-and-directory/) | Tracking / Databases | GET `https://www.classicrockhistory.com` com `s` |
| [RemixSearch](https://remixsearch.net/) | Tracking / Databases | GET `https://remixsearch.net/s.php` com `search`; GET `https://remixsearch.net/s.php` com `search` |
| [TheIndieRockPlaylist](https://www.theindierockplaylist.com/) | Tracking / Databases | GET `https://www.theindierockplaylist.com/` com `s` |
| [Bandcamp Daily](https://daily.bandcamp.com/) | Curated Recommendations | GET `https://daily.bandcamp.com/search` com `q` |
| [Hidden Gems](https://daily.bandcamp.com/hidden-gems) | Curated Recommendations | GET `https://daily.bandcamp.com/search` com `q` |
| [Shfl](https://theshfl.com/) | Curated Recommendations | GET `https://theshfl.com/search` com `q` |
| [The Quietus](https://thequietus.com/charts/) | Curated Recommendations | GET `https://thequietus.com/` com `s` |
| [Loudness War](https://dr.loudness-war.info/) | Tracking / Databases | GET `https://dr.loudness-war.info/` com `artist`, `album` |
| [Essential Charts](https://4chanmusic.miraheze.org/wiki/Essential_Charts) | Curated Recommendations | GET `https://4chanmusic.miraheze.org/w/index.php` com `search`, `title` |
| [DigitalDreamDoor](https://digitaldreamdoor.com/pages/music0.html) | Curated Recommendations | GET `https://digitaldreamdoor.com/pages/DDD-Search-Results-zeta.html` com `q` |
| [MusicTo](https://www.musicto.com/) | Curated Recommendations | GET `https://www.musicto.com/` com `s` |
| [⁠TWGEEMA](https://twgeema.com/) | Curated Recommendations | GET `https://www.twgeema.com/search` com `q` |
| [cosine.club](https://cosine.club/) | Music Discovery | GET `https://cosine.club/` com `q` |
| [New Music](https://furia.com/page.cgi?type=log&skip=20#id492) | Music Discovery | GET `https://furia.com/page.cgi` com `terms`; GET `https://furia.com/page.cgi` com `terms` |
| [SuperFridayChart](https://www.superfridaychart.com/) | Music Discovery | GET `https://www.superfridaychart.com/#` com `q` |
| [Lyrion](https://lyrion.org/) | Audio Servers | GET `https://lyrion.org/` com `query` |
| [Extensions](https://lyrion.org/extensions/applications/) | Audio Servers | GET `https://lyrion.org/extensions/applications/` com `query` |
| [Classic Rock Covers](https://www.classic-rock-covers.com/) | Album Artwork | GET `https://www.classic-rock-covers.com/search` com `q` |
| [Intellectual](https://intellectual.insprill.net/) | Lyric Sites | GET `https://intellectual.insprill.net/search` com `q` |
| [FindMusicByLyrics](https://findmusicbylyrics.com/) | Lyric Sites | GET `https://findmusicbylyrics.com/search` com `q` |
| [AZLyrics](https://www.azlyrics.com/) | Lyric Sites | GET `https://www.azlyrics.com/search/` com `q`; GET `https://www.azlyrics.com/search/` com `q` |
| [SongMeanings](https://songmeanings.com/) | Lyric Sites | GET `https://songmeanings.com/query/` com `query`; GET `https://songmeanings.com/query/` com `query` |
| [⁠AnimeSongLyrics](https://www.animesonglyrics.com/) | Lyric Sites | GET `https://www.animesonglyrics.com/results` com `q`; GET `https://www.animesonglyrics.com/results` com `q` |
| [⁠Lyrical Nonsense](https://www.utatime.com/global/) | Lyric Sites | GET `https://www.utatime.com/search/` com `s` |
| [Sheet Host](https://sheet.host/) | Sheet Music / Notation | GET `https://sheet.host/sheets` com `q` |
| [MuseScore](https://musescore.org/) | Sheet Music / Notation | GET `https://musescore.com/sheetmusic` com `text`; GET `https://musescore.org/en/search/content` com `keys` |
| [PresetShare](https://presetshare.com/) | Audio Editing | GET `https://presetshare.com/presets` com `query` |
| [⁠SoundPacks](https://soundpacks.com/) | SFX / Samples | GET `https://soundpacks.com/` com `s` |
| [OrangeFreeSounds](https://orangefreesounds.com/) | SFX / Samples | GET `https://orangefreesounds.com/` com `s`; GET `https://orangefreesounds.com/` com `s` |
| [SongStems](https://songstems.net/) | SFX / Samples | GET `https://songstems.net/search` com `q`; GET `https://songstems.net/search` com `q` |
| [GDC](https://sonniss.com/gameaudiogdc) | SFX / Samples | GET `https://sonniss.com` com `s`; GET `https://sonniss.com/` com `s` |
| [FreeSoundsLibrary](https://www.freesoundslibrary.com/) | SFX / Samples | GET `https://www.freesoundslibrary.com/` com `s` |
| [⁠BigSoundBank](https://bigsoundbank.com/) | SFX / Samples | GET `https://bigsoundbank.com/search` com `q`; GET `https://bigsoundbank.com/search` com `q` |
| [Freesound](https://freesound.org/) | SFX / Samples | GET `https://freesound.org/search/` com `q`; GET `https://freesound.org/search/` com `q` |
| [MyInstants](https://www.myinstants.com/index/us/) | SFX / Samples | GET `https://www.myinstants.com/en/search/` com `name` |
| [SampleSwap](https://sampleswap.org/) | SFX / Samples | GET `https://sampleswap.org/filebrowser-new.php` com `q` |
| [DeadPulpit](https://www.deadpulpit.com/) | Download Sites | GET `https://www.deadpulpit.com/search` com `q` |
| [Google Song Identification](https://support.google.com/websearch/answer/7554088) | Song Identification | GET `https://support.google.com/websearch/search` com `q` |

## Critérios e limites

- Até 220.000 bytes por página e 64.000 por robots, com truncamento registrado. HTML parcial pode ocultar forms ou documentação; scripts listados não foram executados.
- Robots 401/403 ou regras impeditivas bloqueiam a visita; robots indisponível/429/5xx não é tratado como permissão. 404/410 indica ausência de arquivo robots.
- Cada destino e redirect é validado para HTTP(S), portas 80/443 e DNS público. Respostas não HTML/texto/JSON são encerradas antes da leitura do corpo; extensões de mídia/binários não são requisitadas.
- Requisições serializadas por host, concorrência global limitada, sem retries automáticos para desbloquear sites. URLs com fragmentos visitam a página-base, mantendo o alvo original no registro.
- `repository_or_software` e `tool_or_related_service` são classificações heurísticas baseadas em host/seção; não afirmações de que o produto nunca possui pesquisa.
- Só ações GET foram registradas como candidatos de redirecionamento. Forms POST e chamadas JavaScript precisam de inspeção específica. A ausência de API/form observado é desconhecimento, não incompatibilidade permanente.
- Não há investigação de licença ou termo de cada site neste crawler. Nenhum candidato foi adicionado ao aplicativo automaticamente.

## Reexecutar

```powershell
.\.venv\Scripts\python scripts/audit_sources.py --self-test
.\.venv\Scripts\python scripts/audit_sources.py
```

O JSON é um checkpoint atômico, salvo a cada 25 alvos. Reexecução só processa URLs ainda ausentes; `--refresh` refaz a auditoria. `--concurrency` e `--timeout` controlam o custo de rede.
