# Provedores e downloads — versão 0.4.0

Entrega de 05/11/2026. Escopo ampliado pelo usuário para streaming pago/freemium, comunidade e download dos arquivos oferecidos. Confirmado: escolher arquivos antes de gerar ZIP.

## Catálogo e seleção

O catálogo agora oferece **76 conectores e 15 pesquisas externas**. Streaming: **9 conectores + 4 atalhos**; comunidade/acervos/metadados: **67 conectores + 11 atalhos**. Essa é uma classificação da interface, independente de assinatura, licença ou autorização de download. Audius é tratado como plataforma de streaming; MusicBrainz, Discogs e Last.fm como metadados da comunidade.

Escolha **Streaming e comunidade**, **Só streaming** ou **Só comunidade**, e marque as fontes individuais. Cada grupo tem **Todas** e **Limpar**. Alternar o foco preserva as marcações do outro grupo. A mudança vale para a próxima pesquisa, evitando consultas involuntárias a dezenas de sites. O backend também aplica o grupo. O foco inicial pode ser salvo nas preferências/perfis.

Spotify, Apple Music API e SoundCloud voltaram ao catálogo com credenciais próprias. Não foram compradas contas, criadas aplicações nem cobrados créditos/tokens. A assinatura de um usuário não garante elegibilidade para a API de desenvolvimento. [Pesquisa com documentação primária](PROVIDER_DOWNLOAD_RESEARCH.md). As APIs autenticadas dependem do acesso oficial do usuário e não foram testadas ao vivo com credenciais nesta entrega.

## Arquivos e formatos

Em cada resultado, **Arquivos e downloads** consulta a origem sob demanda. Exibe arquivos diretos, pacotes originais, espelhos, formato informado, tamanho quando disponível, licença informada e link de evidência. Extensão, rótulo e cabeçalhos não comprovam codec, qualidade ou direitos; não há conversão nem promoção de qualidade.

A navegação **Downloads** também permite **Verificar uma página de origem ou de pesquisa externa**. O endereço deve pertencer ao domínio da fonte selecionada. Internet Archive aceita /details/identificador, inclusive itens classificados como data que não aparecem na busca de áudio; Commons aceita /wiki/File:Nome. Fontes configuráveis e atalhos externos também podem ser inspecionados. Isso não transforma esses atalhos em busca federada integrada.

| Fonte | Implementação | Limite |
|---|---|---|
| Internet Archive | Metadados oficiais: arquivos, derivados, pacotes, capas, torrent e dados; formatos e tamanhos informados | Não oferece arquivos privados nem itens explicitamente restritos; até 500 arquivos exibidos |
| Wikimedia Commons | URL do arquivo original e tamanho via imageinfo | Preserva a licença e não pressupõe uso irrestrito |
| Jamendo | MP3 96 kbps, MP3 VBR, OGG e FLAC documentados, apenas com audiodownload_allowed=true | Exige Client ID próprio; formatos documentados, sem validação autenticada nesta entrega |
| SoundCloud | Original, apenas quando downloadable=true e a API oferece download_url | Exige acesso OAuth próprio; não exporta playlist automaticamente |
| Audius | Original apenas com os indicadores completos de permissão e disponibilidade, sem bloqueio de acesso | access.download isolado não basta; caso público mWB22 corretamente não gera arquivo |
| Páginas da comunidade | Links explícitos, URLs publicadas em texto e botões estáticos com endereço de download; pacotes, áudio/MIDI, documentos, capas e outros formatos reconhecidos | Não executa JavaScript nem envia formulários de acesso/pagamento; seletor CSS de links pode ser configurado |
| Spotify, Apple Music, Deezer, YouTube, Mixcloud e conectores de metadados | Mantêm o link e os metadados da origem | Não foi exposto um arquivo exportável pela integração; ouvir offline não é exportar MP3/FLAC |

Um link externo permanece externo enquanto for uma página de acesso, hospedagem, autenticação ou espelho. **Verificar arquivo direto** faz HEAD com validação de redirecionamentos, sem ler mídia; só muda a opção para arquivo quando os cabeçalhos confirmam uma resposta de arquivo. Se não confirmar, o usuário continua na origem. Cookies do navegador, sessões pagas e desafios interativos não são importados.

## ZIP, progresso e dados locais

Selecione os arquivos desejados, filtre por tipo/formato e use **Preparar ZIP selecionado**. Somente os arquivos marcados entram no pacote. Um ZIP/RAR já oferecido pela fonte pode ser baixado como original; ele não é extraído automaticamente. Espelhos podem apontar para o mesmo conteúdo; os nomes repetidos são diferenciados dentro do ZIP.

As preparações exibem bytes e quantidade de arquivos, permitem cancelamento e apresentam **Salvar arquivo** quando prontas. Fechar o painel não cancela a tarefa. O limite inicial é **2.048 MB por preparação**, configurável entre 10 e 32.768 MB. Há no máximo duas transferências simultâneas, 20 preparações recentes e 500 arquivos por seleção.

Os arquivos ficam em um diretório temporário próprio, expiram após 30 minutos de inatividade (sem interromper um salvamento em andamento) e são removidos no encerramento; a limpeza por expiração roda a cada minuto. O arquivo que você salvar pelo navegador permanece na pasta escolhida. Falhas e cancelamentos removem arquivos parciais; ZIP com uma falha não é apresentado como concluído. Não há extração de arquivos nem execução de mídia.

O transporte de arquivos é separado do transporte de metadados. Continua exigindo HTTPS público com DNS pinado em cada redirecionamento, sem repassar autorização para outro host, e aplica limite de bytes antes e durante a escrita. A API usa referências/opções emitidas pelo servidor, sem aceitar URLs arbitrárias para transferência. Ao alterar credenciais ou fontes, opções antigas são invalidadas e preparações afetadas em andamento são canceladas.

## Verificação e cobertura real

**173 testes passaram.** Foram exercitados os grupos, seleção individual, perfis, país na busca de streaming, referências, arquivos privados, redirecionamentos, SSRF, remoção de credenciais, limite de tamanho, cancelamento, nomes seguros, conteúdo do ZIP e recusa de HTML disfarçado de áudio. A interface Edge verificou os dois grupos, mudança de foco, preservação de duas fontes marcadas, lista de arquivos, seleção manual e salvamento de ZIP com **dois arquivos XML públicos**. Nenhuma música foi transferida automaticamente nessa validação.

Uma amostra de **60 páginas/itens** (59 páginas com exemplos de resultados da comunidade e um item Archive) encontrou opções em **48**, não confirmou opções em **10** e teve **2 falhas de leitura**. Em 37 havia links diretos de algum tipo; em 32 havia links externos. **Esses números incluem capas e metadados**: apenas cinco amostras tinham áudio direto e quatro tinham pacote direto. O resultado de uma página não representa todo o catálogo do site nem garante que cada arquivo esteja disponível. [Dados da auditoria](download-options-audit.json).

| Fonte da amostra | Estado | Diretos | Externos | Formatos informados |
|---|---|---:|---:|---|
| [UCSB Cylinder Audio Archive](https://cylinders.library.ucsb.edu/detail.php?query_type=mms_id&query=990029995950203776&r=1&of=5) | Opções identificadas | 1 | 0 | PHP |
| [VGMRips](https://vgmrips.net/packs/pack/arm-wrestling-arcade) | Opções identificadas | 3 | 0 | PNG, VGZ, ZIP |
| [OC ReMix](https://ocremix.org/remix/OCR02572) | Opções identificadas | 3 | 0 | MP3 |
| [iPlusFree](https://www7.iplusfree.org/the-beatles-abbey-road-2019-mix-itunes-plus-aac-m4a/) | Opções identificadas | 0 | 1 | — |
| [Music Rider](https://musicrider.org/jah-wobble-tian-qiyi-mystic-liverpool-the-beatles-psychedelic-psongbook-2026/) | Opções identificadas | 0 | 1 | MP3 |
| [SongsLover](https://songslover.net/video/eric-bellinger-black-beatles.html) | Sem opção confirmada | 0 | 0 | — |
| [Exystence](https://exystence.net/blog/2020/03/10/al-di-meola-across-the-universe-the-beatles-vol-2-2020/) | Opções identificadas | 1 | 2 | FLAC, JPG |
| [Hipstrumentals](https://hipstrumentals.com/2022/04/rae-sremmurd-feat-gucci-mane-black-beatles-instrumental/) | Opções identificadas | 1 | 1 | MP3 |
| [EDMWaves](https://edmwaves.org/2025/06/30/bp-tiesto-streaming-classics/) | Opções identificadas | 1 | 1 | JPEG |
| [EssentialHouse](https://essentialhouse.club/2020/04/km-with-the-beatles-xcape-rhythm-records/) | Opções identificadas | 0 | 2 | — |
| [IntMusic](https://intmusic.net/319412/jah-wobble-mystic-liverpool-the-beatles-psychedelic-psongbook-2026) | Opções identificadas | 0 | 2 | — |
| [⁠Old School Metal Music](https://oldschoolmetalmusicz.blogspot.com/2021/05/metal-mania-4-best-of-metallica.html) | Opções identificadas | 4 | 0 | JPG |
| [Metalminos](https://metalminos.net/metallica-72-seasons-320-kbps/) | Opções identificadas | 0 | 3 | — |
| [FondSound](https://www.fondsound.com/the-beatles-strawberry-fields-foreverpenny-lane-1967/) | Opções identificadas | 2 | 0 | JPEG, JPG |
| [1Gabba](https://1gabba.pw/node/87341/tiesto-traffic-longtimemixer-bootleg) | Opções identificadas | 1 | 2 | XML |
| [Discografias Completas](https://www.discografias-completas.org/fort-minor-320-kbps-mega/) | Leitura indisponível | 0 | 0 | ConnectTimeout |
| [Rap War](https://rap-war-fam.blogspot.com/2026/11/sites-kid-mind-state-2026.html) | Opções identificadas | 1 | 1 | JPG |
| [Lost Songs](https://lostsongshc.blogspot.com/2026/11/88-miles-per-hour-2004-are-you-listening.html) | Opções identificadas | 1 | 1 | JPG, M4A |
| [Ezhevika](https://ezhevika.blogspot.com/2026/10/halifax-halifax-1981.html) | Opções identificadas | 1 | 1 | JPG |
| [Cova-Argh!!!!](https://josephbarulho.blogspot.com/2026/11/destruction-birth-of-malice-2025.html) | Opções identificadas | 1 | 1 | JPG |
| [Urban Asprines](https://urbanaspirines.blogspot.com/2026/11/john-lee-hooker-with-groundhogs-hooker.html) | Opções identificadas | 18 | 1 | FLAC, JPG |
| [Paradise of Garage Comps](https://paradiseofgaragecomps.blogspot.com/2026/09/reuploads-2016.html) | Opções identificadas | 0 | 3 | — |
| [FlatblackAndClassical](https://www.flatblackandclassical.com/2025/03/dagar-brothers-moae-135-lp-recorded-and.html) | Opções identificadas | 7 | 0 | JPEG, JPG, ZIP |
| [MusicRepublic](https://music-republic-world-traditional.blogspot.com/2026/10/angola-malawi-cameroon-nigeria-egypt.html) | Opções identificadas | 8 | 2 | FLAC, JPG, MP3 |
| [Nothin' Sez Somethin'](https://nathannothinsez.blogspot.com/2026/11/musick-that-needed-work-u-unkle.html) | Opções identificadas | 3 | 1 | JPG |
| [inconstant sol](https://inconstantsol.blogspot.com/2011/01/what-long-strange-trip.html) | Opções identificadas | 2 | 5 | JPG |
| [Tone and Wave](https://toneandwave.blogspot.com/2026/11/sparker-demo-tape-1993.html) | Opções identificadas | 1 | 1 | JPG |
| [ccMixter](https://ccmixter.org/files/MalreDeszik/71326) | Sem opção confirmada | 0 | 0 | — |
| [Canna](https://canna.to/u/689142-100-hits-of-the-70-s-80-s-90-s-2020) | Sem opção confirmada | 0 | 0 | — |
| [CannaPower](https://canna-power.to/u/689142-100-hits-of-the-70-s-80-s-90-s-2020) | Sem opção confirmada | 0 | 0 | — |
| [Geocities MIDIs](https://www.midicities.com/ViewGeocitiesSong?token=1880c7a4-6820-48f0-85a8-f3c1eda30235) | Opções identificadas | 0 | 1 | MIDI |
| [Rapload](https://rapload.org/?audio=nasaan-method-acting-2026) | Sem opção confirmada | 0 | 0 | — |
| [Gabber](https://gabber.od.ua/node/44505/angerfist-t78-psycho-killa-2026) | Opções identificadas | 0 | 2 | RAR |
| [GlobalDJMix](https://globaldjmix.com/solomun-live-tomorrowland-2025-week-2-freedom-stage-2025-july-26/) | Opções identificadas | 1 | 0 | JPG |
| [Systems of Romance](https://www.systemsofromance.com/blog/2012/03/coldwave-grab-bag-red-rain-coat-jus-dorange/) | Sem opção confirmada | 0 | 0 | — |
| [Classical Music Download](https://classical-music-download.com/piano/19620-nils-anders-mortensen-js-bach-partitas-nos-2-3-amp-4-bwv-826-828-2026-flac-hi-res.html) | Opções identificadas | 0 | 1 | — |
| [Certified Mixtapez](https://www.certifiedmixtapez.com/Main/Details?refId=49e8528e) | Sem opção confirmada | 0 | 0 | — |
| [madrotter-treasure-hunt](https://madrotter-treasure-hunt.blogspot.com/2026/11/the-apollo-sweet-and-beautiful.html) | Opções identificadas | 2 | 1 | JPG |
| [Tape Attack](https://tapeattack.blogspot.com/2026/09/glenn-branca-4symphonie-west-berlin.html) | Opções identificadas | 2 | 0 | JPG |
| [DeadPulpit](https://www.deadpulpit.com/2026/10/scrape-st-ep.html) | Sem opção confirmada | 0 | 0 | — |
| [Butterboy Compilations](https://butterboycompilations.blogspot.com/2026/11/va-hope-butterboy-compilation-4-x-cds.html) | Opções identificadas | 1 | 1 | JPG |
| [Primitive Offerings](https://primitiveofferings.blogspot.com/2026/11/various-artists-intended-play-2005.html) | Opções identificadas | 1 | 1 | PNG |
| [KTI Music](https://ktimusic.blogspot.com/2026/04/style-house-date-2026-country-ukraine.html) | Opções identificadas | 1 | 0 | PNG |
| [Die or DIY](https://dieordiy2.blogspot.com/2026/10/various-artists-cambodian-nuggets.html) | Opções identificadas | 1 | 1 | JPG |
| [With The Song Of Life](https://forwardwiththesong.blogspot.com/2019/03/jo-stafford-reflections-ultimate.html) | Opções identificadas | 2 | 1 | JPG, RAR |
| [Sophie's Floorboard](https://sophiesfloorboard.blogspot.com/2026/09/heavens-to-betsy.html) | Opções identificadas | 6 | 6 | JPG |
| [ProgRockVintage](https://www.progrockvintage.com/2026/02/publicado-originalmente-em-setembro-de.html) | Opções identificadas | 1 | 1 | JPG |
| [aboutdisco](https://aboutdiscowithlove.blogspot.com/2026/03/convertible-like-rain-ep.html) | Opções identificadas | 1 | 0 | JPG |
| [The T-SQUARE Plaza](https://tsquareplaza.blogspot.com/2026/06/voyage-2026.html) | Opções identificadas | 1 | 0 | JPG |
| [1000 Flights](https://1000flights.blogspot.com/2026/10/disciplina-disciplina-alampo-records.html) | Opções identificadas | 2 | 0 | JPG |
| [LosslessAlbums](https://losslessalbums.club/hi-res/201392-computerwife-born-from-a-wish-2026-hi-res.html) | Opções identificadas | 0 | 1 | — |
| [nodata](https://nodata.tv/149934) | Sem opção confirmada | 0 | 0 | — |
| [FlacMusic](https://flacmusic.info/42842-va-spin-the-bottle-an-all-star-tribute-to-kiss-2004.html) | Opções identificadas | 1 | 0 | JPG |
| [FreeMIDI](https://freemidi.org/artist-251-beatles) | Opções identificadas | 0 | 50 | — |
| [Grime Archive](https://www.grimearchive.org/mix/4537731) | Opções identificadas | 1 | 0 | — |
| [HQ Hip Hop](https://94hiphop.com/va-the-genesis-of-nasty-english-ep-cd-2026-flac-320-kbps) | Sem opção confirmada | 0 | 0 | — |
| [BurningTheGround](https://burningtheground.net/?p=30517) | Opções identificadas | 4 | 0 | JPG, RAR |
| [Tom Lehrer Songs](https://tomlehrersongs.com/the-elements/) | Opções identificadas | 7 | 1 | JPEG, MP3, PDF |
| [We Need Match](https://we-need-match.ru/forums/topic/4478-various-artists-metal-hammer-decades-of-destruction-1986-2016-flac/?do=findComment&comment=7450) | Leitura indisponível | 0 | 0 | O destino retornou mídia/binário em vez de metadados. |
| [Internet Archive](https://archive.org/details/sam-torres-still) | Opções identificadas | 10 | 0 | Archive BitTorrent, Flac, Item Tile, Metadata, PNG, Spectrogram, VBR MP3, WAVE |

## O que permanece pendente

A seleção de ZIP é por item/álbum; combinar arquivos de vários resultados em uma cesta única ainda não foi implementado.

Não há cobertura universal de downloads: botões gerados por JavaScript, páginas protegidas, links escondidos por login, links apenas HTTP, formulários e hospedagens que exigem interação podem continuar na origem ou exigir um conector específico. Certified Mixtapez não publicou arquivo nos links HTML da amostra; seu frontend observado contém um botão de download que apenas exibe uma mensagem, sem uma transferência comprovada. We Need Match retornou conteúdo binário no ponto em que se esperava HTML e não foi lido como metadados.

Não foram validados login/OAuth real de provedores, transferências grandes, outro computador ou Linux. Os testes de transferências de mídia usam bytes sintéticos; o teste real de ZIP usa somente metadados XML públicos.
