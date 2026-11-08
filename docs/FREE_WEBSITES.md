# Sites gratuitos — situação atual 0.3.0

> Atualização 0.4.0: [grupos de provedores, downloads e ZIP selecionado](PROVIDERS_DOWNLOADS.md).
> As restrições de catálogo exclusivamente gratuito da versão anterior foram substituídas pelo novo escopo solicitado.


Verificação de 05/11/2026. Escopo: pesquisa em websites gratuitos, sem compra de créditos/tokens; créditos musicais preservados; sem downloads e sem programas de terceiros como fontes.

**124 links auditados. 57 conectores específicos dessas seções instalados: 16 anteriores + 41 novos.** Os 41 novos passaram por consulta positiva e consulta impossível com o transporte real do aplicativo. Dos 16 anteriores, 15 retornaram correspondências na última verificação; ThemFire respondeu sem correspondência. Internet Archive também já possui adaptador nativo. Canna e CannaPower são espelhos e podem repetir resultados.

O catálogo completo tem **73 conectores configurados e 15 atalhos externos**. Três APIs opcionais requerem chave própria; não foram incluídas integrações cujo acesso exige plano pago. Ter conector instalado não garante disponibilidade permanente da fonte.

## Como usar

Escolha **Resultados da fonte** para enviar o texto sem interpretar `Artista - Faixa`, conservar a ordem recebida de cada fonte e mostrar candidatos sem rejeitá-los por nome. O rótulo **Retornado pela fonte · sem conferência** distingue esses resultados. Este é o modo inicial em perfis novos. Perfis existentes mantêm sua preferência salva.

Os modos **Faixa exata**, **Nome completo / artista e faixa** e **Pessoa e créditos** continuam disponíveis. Eles conferem os metadados e não transformam uma menção em crédito confirmado. Em sites de páginas/postagens, não inventamos título de faixa, artista ou papel de produção.

## O que foi integrado nesta ampliação

Formulários GET e POST, corpos de formulário e JSON, buscas nos feeds públicos dos próprios blogs e leitura dos resultados por seletores específicos. HTTP público com DNS pinado, limites de corpo, validação de URL, regras de acesso e isolamento de erros continuam ativos. Conectores são declarativos; não executam código fornecido em perfis.

O teste real no Edge comparou **os títulos e a ordem da pesquisa FreeMIDI** com a tela do EveryTune. Testou também Certified Mixtapez com POST JSON e LosslessAlbums com POST de formulário. Isso comprova esses testes, não equivalência visual de todos os sites. Os 22 feeds Blogger usam a busca pública do catálogo; indexação, ordenação e quantidade podem diferir da página HTML.

**Carregar próxima página** preserva itens restantes da resposta recebida. Os feeds usam paginação pública por índice, começando em 1. Nos demais sites, só se avança para novas páginas remotas quando esse mecanismo está configurado e validado; não prometemos varrer todo o catálogo. We Need Match exige 60 segundos entre consultas; o aplicativo apresenta limite em vez de bloquear as outras fontes durante esperas longas.

## Novos conectores verificados

| Fonte | Método | Consulta de teste | Itens recebidos no teste |
|---|---|---|---:|
| [Ezhevika](https://ezhevika.blogspot.com/feeds/posts/default) | GET JSON | Halifax | 1 |
| [Cova-Argh!!!!](https://josephbarulho.blogspot.com/feeds/posts/default) | GET JSON | Destruction | 5 |
| [Urban Asprines](https://urbanaspirines.blogspot.com/feeds/posts/default) | GET JSON | John | 5 |
| [Paradise of Garage Comps](https://paradiseofgaragecomps.blogspot.com/feeds/posts/default) | GET JSON | Reuploads | 5 |
| [FlatblackAndClassical](https://www.flatblackandclassical.com/feeds/posts/default) | GET JSON | Dagar | 2 |
| [MusicRepublic](https://music-republic-world-traditional.blogspot.com/feeds/posts/default) | GET JSON | ANGOLA | 3 |
| [Nothin' Sez Somethin'](https://nathannothinsez.blogspot.com/feeds/posts/default) | GET JSON | Musick | 5 |
| [inconstant sol](https://inconstantsol.blogspot.com/feeds/posts/default) | GET JSON | What | 5 |
| [Tone and Wave](https://toneandwave.blogspot.com/feeds/posts/default) | GET JSON | Sparker | 2 |
| [ccMixter](https://ccmixter.org/search) | GET HTML | love | 5 |
| [Canna](https://canna.to/suche) | POST HTML | Abba | 5 |
| [CannaPower](https://canna-power.to/suche) | POST HTML | Abba | 5 |
| [Geocities MIDIs](https://www.midicities.com/geocities-search) | GET HTML | titanic | 5 |
| [Rapload](https://rapload.org/) | GET HTML | Nas | 5 |
| [Gabber](https://gabber.od.ua/tt) | GET HTML | Angerfist | 5 |
| [GlobalDJMix](https://globaldjmix.com/search-result) | GET HTML | Solomun | 5 |
| [Systems of Romance](https://www.systemsofromance.com/blog/) | GET HTML | coldwave | 5 |
| [Classical Music Download](https://classical-music-download.com/) | POST HTML | Bach | 5 |
| [Certified Mixtapez](https://www.certifiedmixtapez.com/Main/GetSearchResults) | POST JSON | Gucci | 5 |
| [madrotter-treasure-hunt](https://madrotter-treasure-hunt.blogspot.com/feeds/posts/default) | GET JSON | APOLLO | 5 |
| [Tape Attack](https://tapeattack.blogspot.com/feeds/posts/default) | GET JSON | Glenn | 5 |
| [DeadPulpit](https://www.deadpulpit.com/feeds/posts/default) | GET JSON | SCRAPE | 4 |
| [Butterboy Compilations](https://butterboycompilations.blogspot.com/feeds/posts/default) | GET JSON | Hope | 5 |
| [Primitive Offerings](https://primitiveofferings.blogspot.com/feeds/posts/default) | GET JSON | various | 5 |
| [KTI Music](https://ktimusic.blogspot.com/feeds/posts/default) | GET JSON | Remix | 5 |
| [Die or DIY](https://dieordiy2.blogspot.com/feeds/posts/default) | GET JSON | Various | 5 |
| [With The Song Of Life](https://forwardwiththesong.blogspot.com/feeds/posts/default) | GET JSON | Stafford | 5 |
| [Sophie's Floorboard](https://sophiesfloorboard.blogspot.com/feeds/posts/default) | GET JSON | Heavens | 5 |
| [ProgRockVintage](https://www.progrockvintage.com/feeds/posts/default) | GET JSON | DROSSELBART | 1 |
| [aboutdisco](https://aboutdiscowithlove.blogspot.com/feeds/posts/default) | GET JSON | Convertible | 1 |
| [The T-SQUARE Plaza](https://tsquareplaza.blogspot.com/feeds/posts/default) | GET JSON | VOYAGE | 5 |
| [1000 Flights](https://1000flights.blogspot.com/feeds/posts/default) | GET JSON | DISCIPLINA | 1 |
| [LosslessAlbums](https://losslessalbums.club/) | POST HTML | Computerwife | 3 |
| [nodata](https://nodata.tv) | GET HTML | Bowie | 5 |
| [FlacMusic](https://www.flacmusic.info/index.php) | GET HTML | Beatles | 5 |
| [FreeMIDI](https://freemidi.org/search) | GET HTML | Beatles | 2 |
| [Grime Archive](https://www.grimearchive.org/search) | GET HTML | Wiley | 5 |
| [HQ Hip Hop](https://94hiphop.com/) | GET HTML | Nas | 5 |
| [BurningTheGround](https://burningtheground.net/) | GET HTML | Madonna | 4 |
| [Tom Lehrer Songs](https://tomlehrersongs.com/) | GET HTML | Elements | 3 |
| [We Need Match](https://we-need-match.ru/search/) | GET HTML | Metallica | 1 |

## Situação dos 124 links

As situações iniciais de “sem GET observado” não são conclusões de impossibilidade. As novas pesquisas individuais e os motivos remanescentes estão registrados abaixo. [Pesquisa detalhada de 35 sites](PENDING_SITE_RESEARCH.md), [comparação dos sites dinâmicos](dynamic-sites-browser.json), [testes dos 41 conectores](federated-live.json).

| Site | Situação | Evidência ou limitação |
|---|---|---|
| [Music Download Guide](https://rentry.co/wheredownloadmusic) | Guia, comunidade ou índice | Guide, community, repository or search index; not a music website connector. |
| [Audio Download CSE](https://cse.google.com/cse?cx=006516753008110874046:ibmyuhh72io) | Guia, comunidade ou índice | Guide, community, repository or search index; not a music website connector. |
| [CSE 2](https://cse.google.com/cse?cx=006516753008110874046:ohobg3wvr_w) | Guia, comunidade ou índice | Guide, community, repository or search index; not a music website connector. |
| [CSE 3](https://cse.google.com/cse?cx=32d85b41e2feacd3f) | Guia, comunidade ou índice | Guide, community, repository or search index; not a music website connector. |
| [Lossless-Music](https://lossless-music.org/) | Restrição em robots.txt | Verificação automática inicial; detalhes no JSON da auditoria. |
| [FLAC Attack](https://flacattack.net/) | Restrição em robots.txt | Verificação automática inicial; detalhes no JSON da auditoria. |
| [GetRockMusic](https://getrockmusic.net/) | Restrição em robots.txt | Verificação automática inicial; detalhes no JSON da auditoria. |
| [ShareMania](https://sharemania.us/) | Sem conector confirmado | Guest homepage exposes login/registration; no guest search form or search link observed. No account created. |
| [AlterPortal](https://alterportal.net/) | Sem conector confirmado | Search form observed (POST story, do=search, subaction=search, titleonly=3), but robots explicitly Disallow /*do=search. Search not executed. |
| [iPlusFree](https://www7.iplusfree.org/) | Conector HTML da versão anterior | Consulta: Beatles; 6 resultados.  |
| [Music Rider](https://musicrider.org/) | Conector HTML da versão anterior | Consulta: Beatles; 2 resultados.  |
| [ccMixter](https://ccmixter.org/) | Busca integrada; positivo e negativo conferidos | Consulta: love; 5 resultados. Termo inexistente: 0 resultados. |
| [musify](https://musify.club/) | Sem conector confirmado | Homepage and robots HTTP403. No access bypass attempted. |
| [punk.cat](https://punkcata.blogspot.com/) | Restrição em robots.txt | Verificação automática inicial; detalhes no JSON da auditoria. |
| [Internet Archive](https://archive.org/details/audio) | Sem conector confirmado | A fonte já está integrada pelo adaptador nativo Internet Archive; não foi duplicada. |
| [Ezhevika](https://ezhevika.blogspot.com/) | Busca integrada; positivo e negativo conferidos | Consulta: Halifax; 1 resultados. Termo inexistente: 0 resultados. |
| [SoundClick](https://www.soundclick.com/default.cfm) | Recusa HTTP | Verificação automática inicial; detalhes no JSON da auditoria. |
| [SongsLover](https://songslover.net/) | Conector HTML da versão anterior | Consulta: Beatles; 3 resultados.  |
| [](https://t.me/+wdUhO_yV_A5lM2E5) | Guia, comunidade ou índice | Guide, community, repository or search index; not a music website connector. |
| [LEAKED](https://leaked.cx/) | Sem conector confirmado | Guest homepage exposes forum catalogue but no guest search form/link. No login attempted. |
| [New Album Releases](https://newalbumreleases.net/) | Restrição em robots.txt | Verificação automática inicial; detalhes no JSON da auditoria. |
| [Exystence](https://exystence.net/) | Conector HTML da versão anterior | Consulta: Beatles; 19 resultados.  |
| [Tancpol](https://tancpol.net/) | Restrição em robots.txt | Verificação automática inicial; detalhes no JSON da auditoria. |
| [Mixupload](https://mixupload.com/) | Restrição em robots.txt | Verificação automática inicial; detalhes no JSON da auditoria. |
| [Canna](https://canna.to/?lang=eng) | Busca integrada; positivo e negativo conferidos | Consulta: Abba; 5 resultados. Termo inexistente: 0 resultados. |
| [xprm](https://xprm.net/) | Restrição em robots.txt | Verificação automática inicial; detalhes no JSON da auditoria. |
| [zvu4no](https://zvu4it.org/) | Sem conector confirmado | First-party /scripts/zvu4it-hybrid.js sets location.href=/tracks/+encodeURIComponent(query). GET /tracks/Beatles HTTP200 returns John Lennon / Imagine. Only artist search and signed direct media URLs observed for record links; no stable individual detail URL, so not promoted. |
| [Geocities MIDIs](https://www.midicities.com/GeoCities) | Busca integrada; positivo e negativo conferidos | Consulta: titanic; 5 resultados. Termo inexistente: 0 resultados. |
| [Music Hoarders](https://discord.gg/kQUQkuwSaT) | Guia, comunidade ou índice | Guide, community, repository or search index; not a music website connector. |
| [ArtScene](http://artscene.textfiles.com/music/midi/) | Sem conector confirmado | Apache directory listing with filenames and folders; no server search form observed. No recursive crawl or media request. |
| [VGMusic](https://www.vgmusic.com/) | Sem conector confirmado | Public category navigation plus random-song form; no server text search observed. No media requested. |
| [Tricotism](https://www.tricotism.com/) | Sem conector confirmado | Static Tricotism page, no search forms/scripts/search links observed. |
| [Rapload](https://rapload.org/) | Busca integrada; positivo e negativo conferidos | Consulta: Nas; 5 resultados. Termo inexistente: 0 resultados. |
| [GoldHipHop](https://goldhiphop.pro/) | Recusa HTTP | Verificação automática inicial; detalhes no JSON da auditoria. |
| [Mixtape Collections](https://rentry.co/FMHYB64#mixtape-collections) | Guia, comunidade ou índice | Guide, community, repository or search index; not a music website connector. |
| [Certified Mixtapez](https://www.certifiedmixtapez.com/) | Busca integrada; positivo e negativo conferidos | Consulta: Gucci; 5 resultados. Termo inexistente: 0 resultados. |
| [ELEKTROBEATS](https://elektrobeats.org/) | Restrição em robots.txt | Verificação automática inicial; detalhes no JSON da auditoria. |
| [Hipstrumentals](https://hipstrumentals.com/) | Conector HTML da versão anterior | Consulta: Beatles; 2 resultados.  |
| [MyPromoSound](https://mypromosound.com/) | Restrição em robots.txt | Verificação automática inicial; detalhes no JSON da auditoria. |
| [EDMWaves](https://edmwaves.org/) | Conector HTML da versão anterior | Consulta: Tiesto; 12 resultados.  |
| [r/xTrill](https://reddit.com/r/xTrill) | Restrição em robots.txt | Verificação automática inicial; detalhes no JSON da auditoria. |
| [Backup](https://reddit.com/r/xTrillBackup) | Restrição em robots.txt | Verificação automática inicial; detalhes no JSON da auditoria. |
| [ElectronicFresh](https://electronicfresh.com/) | Restrição em robots.txt | Verificação automática inicial; detalhes no JSON da auditoria. |
| [CannaPower](https://canna-power.to) | Busca integrada; positivo e negativo conferidos | Consulta: Abba; 5 resultados. Termo inexistente: 0 resultados. |
| [1Techno](https://1techno.org/) | Sem conector confirmado | Observed GET /f?t=Adam Beyer redirects /?t=Adam%20Beyer. robots disallows /?t=; excluded rather than using redirect as workaround. |
| [oVPN DJ Mixes](https://rentry.co/FMHYB64#ovpn-dj-mixes) | Guia, comunidade ou índice | Guide, community, repository or search index; not a music website connector. |
| [Gabber](https://gabber.od.ua/) | Busca integrada; positivo e negativo conferidos | Consulta: Angerfist; 5 resultados. Termo inexistente: 0 resultados. |
| [LOA2K](https://loa2k.neocities.org/) | Sem conector confirmado | Static LoA2K catalogue and archive download links, no server search form. Download links not followed. |
| [EssentialHouse](https://essentialhouse.club/) | Conector HTML da versão anterior | Consulta: Beatles; 1 resultados.  |
| [GetMetal Club](https://getmetal.club/) | Restrição em robots.txt | Verificação automática inicial; detalhes no JSON da auditoria. |
| [Nuclear Holocaust](https://nuclear-holocaust.blogspot.com/) | Restrição em robots.txt | Verificação automática inicial; detalhes no JSON da auditoria. |
| [Nu Guide](https://nuvaporwave.neocities.org/mirrors) | Sem conector confirmado | Static list of download mirrors, no search form or scripts. Not a federated search service. |
| [GlobalDJMix](https://globaldjmix.com/) | Busca integrada; positivo e negativo conferidos | Consulta: Solomun; 5 resultados. Termo inexistente: 0 resultados. |
| [DMO](https://dance-music.org/) | Sem conector confirmado | Na inspeção pelo navegador, nenhum campo de pesquisa foi renderizado. Não foi inventado um endpoint de busca. |
| [We Need Match](https://we-need-match.ru/) | Busca integrada; positivo e negativo conferidos | Consulta: Metallica; 1 resultados. Termo inexistente: 0 resultados. |
| [Cova-Argh!!!!](https://josephbarulho.blogspot.com/) | Busca integrada; positivo e negativo conferidos | Consulta: Destruction; 5 resultados. Termo inexistente: 0 resultados. |
| [In The Fog](https://in-the-fog.ru/) | robots.txt indisponível | Verificação automática inicial; detalhes no JSON da auditoria. |
| [HeavyMetalRarities](https://heavymetalrarities.com/) | Restrição em robots.txt | Verificação automática inicial; detalhes no JSON da auditoria. |
| [F.P.F.T.P.](https://fpftp.blogspot.com/) | Restrição em robots.txt | Verificação automática inicial; detalhes no JSON da auditoria. |
| [Urban Asprines](https://urbanaspirines.blogspot.com/) | Busca integrada; positivo e negativo conferidos | Consulta: John; 5 resultados. Termo inexistente: 0 resultados. |
| [Paradise of Garage Comps](https://paradiseofgaragecomps.blogspot.com/) | Busca integrada; positivo e negativo conferidos | Consulta: Reuploads; 5 resultados. Termo inexistente: 0 resultados. |
| [KPopFLAC](https://www.kpopflac.xyz/) | Restrição em robots.txt | Verificação automática inicial; detalhes no JSON da auditoria. |
| [Systems of Romance](https://www.systemsofromance.com/blog/) | Busca integrada; positivo e negativo conferidos | Consulta: coldwave; 5 resultados. Termo inexistente: 0 resultados. |
| [Classical Music Download](https://classical-music-download.com/) | Busca integrada; positivo e negativo conferidos | Consulta: Bach; 5 resultados. Termo inexistente: 0 resultados. |
| [chucrute com quiabo](https://rabanetecomquiabo.blogspot.com/) | Restrição em robots.txt | Verificação automática inicial; detalhes no JSON da auditoria. |
| [FoggyNotion](https://foggynotion-flac.blogspot.com/) | Restrição em robots.txt | Verificação automática inicial; detalhes no JSON da auditoria. |
| [MeetingInMusic](https://meetinginmusic.blogspot.com/) | Restrição em robots.txt | Verificação automática inicial; detalhes no JSON da auditoria. |
| [Bluegrass Archive](https://rentry.co/FMHYB64#bluegrass-archive) | Guia, comunidade ou índice | Guide, community, repository or search index; not a music website connector. |
| [David W. Niven Collection](https://archive.org/details/davidwnivenjazz) | Sem conector confirmado | Public davidwnivenjazz collection; existing Archive connector searches audio. Specific collection filter needs a fixed query wrapper; not added as unscoped duplicate. |
| [FlatblackAndClassical](https://www.flatblackandclassical.com/) | Busca integrada; positivo e negativo conferidos | Consulta: Dagar; 2 resultados. Termo inexistente: 0 resultados. |
| [MusicRepublic](https://music-republic-world-traditional.blogspot.com/) | Busca integrada; positivo e negativo conferidos | Consulta: ANGOLA; 3 resultados. Termo inexistente: 0 resultados. |
| [Nothin' Sez Somethin'](https://nathannothinsez.blogspot.com/) | Busca integrada; positivo e negativo conferidos | Consulta: Musick; 5 resultados. Termo inexistente: 0 resultados. |
| [inconstant sol](https://inconstantsol.blogspot.com/) | Busca integrada; positivo e negativo conferidos | Consulta: What; 5 resultados. Termo inexistente: 0 resultados. |
| [Bootleg Radioclash](https://rentry.co/FMHYB64#bootleg-radioclash) | Guia, comunidade ou índice | Guide, community, repository or search index; not a music website connector. |
| [Tone and Wave](https://toneandwave.blogspot.com/) | Busca integrada; positivo e negativo conferidos | Consulta: Sparker; 2 resultados. Termo inexistente: 0 resultados. |
| [The Noise-Arch Archive](https://archive.org/details/noise-arch) | Sem conector confirmado | Public noise-arch collection; existing Archive connector searches audio. Specific collection filter needs a fixed query wrapper; not added as unscoped duplicate. |
| [madrotter-treasure-hunt](https://madrotter-treasure-hunt.blogspot.com/) | Busca integrada; positivo e negativo conferidos | Consulta: APOLLO; 5 resultados. Termo inexistente: 0 resultados. |
| [Tape Attack](https://tapeattack.blogspot.com/) | Busca integrada; positivo e negativo conferidos | Consulta: Glenn; 5 resultados. Termo inexistente: 0 resultados. |
| [Kiddie Records](http://www.kiddierecords.com/) | Sem conector confirmado | Catálogo estático observado, sem formulário de busca pública confirmado. |
| [IntMusic](https://intmusic.net/) | Conector HTML da versão anterior | Consulta: Beatles; 20 resultados.  |
| [LosslessAlbums](https://losslessalbums.club/) | Busca integrada; positivo e negativo conferidos | Consulta: Computerwife; 3 resultados. Termo inexistente: 0 resultados. |
| [Old School Metal Music](https://oldschoolmetalmusicz.blogspot.com/) | Conector HTML da versão anterior | Consulta: Metallica; 1 resultados.  |
| [Metalminos](https://metalminos.net/) | Conector HTML da versão anterior | Consulta: Metallica; 8 resultados.  |
| [ThemFire](https://themfire.pro/) | Conector HTML da versão anterior | Consulta: Beatles; 0 resultados.  |
| [FondSound](https://www.fondsound.com/) | Conector HTML da versão anterior | Consulta: Beatles; 1 resultados.  |
| [1Gabba](https://1gabba.pw/) | Conector HTML da versão anterior | Consulta: Tiesto; 1 resultados.  |
| [DiscogC](https://www.discogc.com/) | Pesquisa ainda não validada | Falha ao verificar robots.txt na nova tentativa; sem conector habilitado. |
| [nodata](https://nodata.tv/) | Busca integrada; positivo e negativo conferidos | Consulta: Bowie; 5 resultados. Termo inexistente: 0 resultados. |
| [Discografias Completas](https://www.discografias-completas.org/) | Conector HTML da versão anterior | Consulta: Fort Minor 320 Kbps [MEGA]; 1 resultados.  |
| [FreeMP3Cloud](https://freemp3cloud.com/) | Falha de inspeção | Verificação automática inicial; detalhes no JSON da auditoria. |
| [RockDownload](https://www.rockdownload.org/) | Pesquisa ainda não validada | Busca preenchida no navegador da própria fonte retornou zero ocorrências de Metallica e a lista recente de Placebo. Filtragem não validada neste ambiente; não é um problema resolvido apenas por executar JavaScript. |
| [FlacMusic](https://www.flacmusic.info/) | Busca integrada; positivo e negativo conferidos | Consulta: Beatles; 5 resultados. Termo inexistente: 0 resultados. |
| [z3.fm](https://z3.fm/) | Pesquisa ainda não validada | Endpoint de busca observado retornou HTTP 502; resposta de resultados não validada. |
| [mp3db](https://mp3db.pro/) | Pesquisa ainda não validada | Falha de conexão na inspeção; busca não validada. |
| [DeadPulpit](https://www.deadpulpit.com/) | Busca integrada; positivo e negativo conferidos | Consulta: SCRAPE; 4 resultados. Termo inexistente: 0 resultados. |
| [Butterboy Compilations](https://butterboycompilations.blogspot.com/) | Busca integrada; positivo e negativo conferidos | Consulta: Hope; 5 resultados. Termo inexistente: 0 resultados. |
| [Wiki](https://musichoarders.xyz/) | Pesquisa ainda não validada | Wiki de ferramentas e documentação; não foi confirmado um catálogo de músicas pesquisável. |
| [Primitive Offerings](https://primitiveofferings.blogspot.com/) | Busca integrada; positivo e negativo conferidos | Consulta: various; 5 resultados. Termo inexistente: 0 resultados. |
| [HipHopa](https://hiphopa.net/) | Pesquisa ainda não validada | robots.txt impede a consulta de pesquisa observada. |
| [FreeMIDI](https://freemidi.org/) | Busca integrada; positivo e negativo conferidos | Consulta: Beatles; 2 resultados. Termo inexistente: 0 resultados. |
| [Dez Flight Underground](https://dezflight-underground.com/) | Pesquisa ainda não validada | robots.txt impede a consulta de pesquisa observada. |
| [Ektoplazm](https://ektoplazm.com/) | Pesquisa ainda não validada | robots.txt impede a consulta de pesquisa observada. |
| [KTI Music](https://ktimusic.blogspot.com/) | Busca integrada; positivo e negativo conferidos | Consulta: Remix; 5 resultados. Termo inexistente: 0 resultados. |
| [Rap War](https://rap-war-fam.blogspot.com/) | Conector HTML da versão anterior | Consulta: Sites & The Kid; 1 resultados.  |
| [Die or DIY](https://dieordiy2.blogspot.com/) | Busca integrada; positivo e negativo conferidos | Consulta: Various; 5 resultados. Termo inexistente: 0 resultados. |
| [1Trance](https://1trance.org/) | Pesquisa ainda não validada | Formulário /f observado; a consulta não completou dentro do limite da inspeção. |
| [PSYFP](https://psyfp.ucoz.ru/) | Pesquisa ainda não validada | robots.txt impede a consulta de pesquisa observada. |
| [Grime Archive](https://www.grimearchive.org/) | Busca integrada; positivo e negativo conferidos | Consulta: Wiley; 5 resultados. Termo inexistente: 0 resultados. |
| [With The Song Of Life](https://forwardwiththesong.blogspot.com/) | Busca integrada; positivo e negativo conferidos | Consulta: Stafford; 5 resultados. Termo inexistente: 0 resultados. |
| [TechnicalDeathMetal](https://technicaldeathmetal.org/) | Pesquisa ainda não validada | Não foi possível verificar robots.txt na nova tentativa. |
| [Sophie's Floorboard](https://sophiesfloorboard.blogspot.com/) | Busca integrada; positivo e negativo conferidos | Consulta: Heavens; 5 resultados. Termo inexistente: 0 resultados. |
| [ProgRockVintage](https://www.progrockvintage.com/) | Busca integrada; positivo e negativo conferidos | Consulta: DROSSELBART; 1 resultados. Termo inexistente: 0 resultados. |
| [HQ Hip Hop](https://94hiphop.com/) | Busca integrada; positivo e negativo conferidos | Consulta: Nas; 5 resultados. Termo inexistente: 0 resultados. |
| [Take Metal](https://takemetal.org/) | Pesquisa ainda não validada | Não foi possível verificar robots.txt na nova tentativa. |
| [aboutdisco](https://aboutdiscowithlove.blogspot.com/) | Busca integrada; positivo e negativo conferidos | Consulta: Convertible; 1 resultados. Termo inexistente: 0 resultados. |
| [KPopMusicDownload](https://kpopdownloadscmm.blogspot.com/) | Pesquisa ainda não validada | O feed público retornou uma resposta não JSON; a pesquisa não foi validada. |
| [Lost Songs](https://lostsongshc.blogspot.com/) | Conector HTML da versão anterior | Consulta: 88 Miles Per Hour; 1 resultados.  |
| [BurningTheGround](https://burningtheground.net/) | Busca integrada; positivo e negativo conferidos | Consulta: Madonna; 4 resultados. Termo inexistente: 0 resultados. |
| [The T-SQUARE Plaza](https://tsquareplaza.blogspot.com/) | Busca integrada; positivo e negativo conferidos | Consulta: VOYAGE; 5 resultados. Termo inexistente: 0 resultados. |
| [JazznBlues](https://jazznblues.club/) | Pesquisa ainda não validada | robots.txt impede a busca do fórum; não foram utilizados cookies ou sessão de login. |
| [1000 Flights](https://1000flights.blogspot.com/) | Busca integrada; positivo e negativo conferidos | Consulta: DISCIPLINA; 1 resultados. Termo inexistente: 0 resultados. |
| [Tom Lehrer Songs](https://tomlehrersongs.com/) | Busca integrada; positivo e negativo conferidos | Consulta: Elements; 3 resultados. Termo inexistente: 0 resultados. |
| [Core Radio](https://coreradio.online/) | Falha de inspeção | Verificação automática inicial; detalhes no JSON da auditoria. |
| [GloryBeats](https://glorybeats.com/) | Falha de inspeção | Verificação automática inicial; detalhes no JSON da auditoria. |

## Limites e testes

Jumo segue sem conector: a busca pela própria interface devolveu HTTP403 `Invalid request context` no teste anterior. [Investigação](JUMO_RESEARCH.md). Não houve contorno de login, CAPTCHA ou bloqueios. Sites sem pesquisa pública confirmada ou sem resultados verificáveis permanecem pendentes.

**154 testes passaram.** A interface foi verificada no Edge, incluindo fontes, créditos, perfis, configurações, POST e comparação com a origem. O pacote Windows é testado separadamente por [smoke do executável](executable-smoke.json). Não houve validação em outro computador ou Linux, nem de APIs opcionais com credenciais.
