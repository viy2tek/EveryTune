# Matriz de fontes e viabilidade

> Atualização 0.4.0: [grupos de provedores, downloads e ZIP selecionado](PROVIDERS_DOWNLOADS.md).
> As restrições de catálogo exclusivamente gratuito da versão anterior foram substituídas pelo novo escopo solicitado.


> Atualização 0.3.0: [fontes gratuitas, créditos e configurações](FREE_WEBSITES.md).
> As contagens e APIs pagas abaixo descrevem a entrega inicial e foram substituídas pelo relatório atual.


Verificação: **05/11/2026**. Descoberta inicial: [FMHY Audio](https://fmhy.net/audio).
Atualização da busca: veja [PRECISE_SEARCH.md](PRECISE_SEARCH.md). Todos os candidatos
agora passam por conferência estrita. Spotify/MusicBrainz/Last.fm usam campos separados
quando informados; iTunes busca título e confere o artista principal via lookup oficial.
Os rótulos antigos de relevância aproximada deixaram de ser exibidos.
O FMHY é um diretório editorial, não uma API de faixas. O inventário completo extraído
de links externos está em [fmhy-audio-links.json](fmhy-audio-links.json): 1.188 URLs,
incluindo ferramentas, espelhos, rádio, podcasts, documentação e serviços sem busca.
As 1.188 URLs foram inspecionadas na expansão; isso não confirma integração individual. O inventário não concede
licença nem certifica segurança. A tabela abaixo é a avaliação técnica dos candidatos
selecionados. Não se instala nem executa código dos sites catalogados.

## APIs implementadas

“Funcional” significa retorno real de dados normalizados pelo aplicativo. Os testes
reproduzíveis com mocks cobrem todos os adaptadores, mas não substituem acesso real.
Os resultados não autorizam reprodução ou redistribuição por si mesmos.

| Fonte / documentação oficial | Categoria / busca | API e acesso | Paginação / limites documentados ou desconhecidos | Dados, licença e viabilidade |
|---|---|---|---|---|
| [iTunes Search / Apple](https://performance-partners.apple.com/search-api) | Comercial; título, artista, álbum | Oficial pública; sem chave | `limit` até 200; aproximadamente 20 consultas/min, sujeito a mudança; sem cursor documentado no método usado | **Integrada e funcional**. Metadados e link da loja BR. Uso promocional e regras Apple. Sem player/prévia neste aplicativo. Cache 1h, intervalo 3,1s. |
| [MusicBrainz](https://musicbrainz.org/doc/MusicBrainz_API) / [busca](https://musicbrainz.org/doc/Indexed_Search_Syntax) | Metadados; gravação, artista, release | Oficial pública; User-Agent significativo; sem chave para leitura | Máximo 1 requisição/s por aplicativo; `limit`/`offset` | **Integrada e funcional**, sujeita a 503 transitório. Intervalo 1,1s e cache 24h. Metadados, nunca áudio; observar licenças e condições de uso não comercial. Consulta termos nos três campos. |
| [Internet Archive](https://archive.org/advancedsearch.php) / [APIs](https://archive.org/services/docs/api/) | Acervo, shows, netlabels e gravações históricas; busca textual | Advanced Search oficial, público | `rows`/`page`; quota numérica geral não confirmada. Documentação de serviços não acessível pelo navegador de pesquisa, formulário e JSON conferidos diretamente | **Integrada e funcional**. Retorna itens de acervo, que podem ser álbuns/shows e não faixas. `licenseurl` é preservada, quando presente. Sem presumir permissões de download ou áudio. |
| [Audius](https://docs.audius.co/api/) / [referência REST](https://api.audius.co/v1) | Independente/descentralizada; faixas | Oficial pública; acesso anônimo verificado; chave opcional para limites maiores | `limit`/`offset`; quota anônima numérica não confirmada | **Integrada e funcional**. Metadados, capa, link e flags informadas pela API. Conteúdo enviado por terceiros não recebe licença inventada. Sem acessar streams. |
| [Openverse](https://api.openverse.org/v1/) / [busca](https://docs.openverse.org/api/reference/search_algorithm.html) | Licenças abertas; áudio com categoria música | Oficial pública; consultas anônimas verificadas; registro aumenta acesso conforme serviço | `page`/`page_size`, `page_count`; limites dependem da autenticação. Números atuais não confirmados | **Integrada e funcional**. Metadados, licença, fonte original e duração; sinaliza disponibilidade apenas com evidência de áudio/licença. Licenças CC não equivalem a uso comercial irrestrito; confira atribuição e condições na origem. |
| [Wikimedia Commons / Search](https://www.mediawiki.org/wiki/API:Search) / [Imageinfo](https://www.mediawiki.org/wiki/API:Imageinfo) / [etiqueta](https://www.mediawiki.org/wiki/API:Etiquette) | Conteúdo livre; arquivos de áudio, não só música | MediaWiki oficial pública; sem chave | Busca com generator, namespace 6, `gsroffset`; requisições serializadas por fonte; leitura sem velocidade fixa garantida | **Integrada e funcional**. Página original, autor/licença a partir de extmetadata. HTML dos metadados convertido para texto. Verifique licença específica e contexto do arquivo. |
| [Mixcloud](https://www.mixcloud.com/developers/) | Mixes, programas e rádio; `cloudcast`, não busca no conteúdo de cada faixa | Oficial; leitura sem autenticação documentada | `limit`/`offset`; `paging.next`; limites retornados pelo serviço, sem quota fixa presumida | **Integrada e funcional**. Link de programa/mix, título, capa e duração quando disponíveis. Uploaders não são presumidos como artistas. Sem extração de streams/download. |
| [Jamendo](https://developer.jamendo.com/v3.0/tracks) | Independente; pesquisa em faixas | Oficial; Client ID próprio | `limit`/`offset`; quota conforme conta/termos, número não confirmado | **Integrável, depende de credenciais**. Adaptador implementado e testado com mocks, não validado ao vivo. Preserva `license_ccurl`, `audiodownload_allowed`, sem baixar. |
| [YouTube Data API](https://developers.google.com/youtube/v3/docs/search/list) | Vídeos musicais; título/consulta textual | Oficial; API key com serviço habilitado | `maxResults` até 50, `pageToken`; a documentação consultada informa 100 chamadas/dia e custo 1 na quota de Search Queries; confira quota efetiva do projeto | **Integrável, depende de credenciais**. Mocks; sem chave para validar. Restringe categoria 10/música. Canal não é presumido como artista; data do upload não vira ano da gravação. Link apenas, sem áudio extraído. |
| [Spotify](https://developer.spotify.com/documentation/web-api/reference/search) / [Client Credentials](https://developer.spotify.com/documentation/web-api/tutorials/client-credentials-flow) | Comercial; faixas e metadados | Oficial; Client ID/Secret e aplicação elegível | Busca atual: `limit` até 10; `offset` até 1000; limite de taxa depende da aplicação e janela de uso | **Integrável, depende de credenciais e elegibilidade**. Token obtido no backend e renovado ao expirar; não há fluxo de usuário. Mocks; políticas de dev mode podem restringir acesso. Sem player/prévia. |
| [SoundCloud](https://developers.soundcloud.com/docs/api/guide) / [OpenAPI consultado](https://developers.soundcloud.com/docs/api/explorer/api.json) | Independente; faixas | Oficial; OAuth access token de aplicação autorizada | `limit`/`offset`/`linked_partitioning` conforme OpenAPI; máximo geral de coleções 200; respeita 429. Quotas específicas dependem da operação | **Integrável, depende de credenciais**. Token fornecido manualmente, sem renovação automática. Mocks; reconfigurar token expirado. Sem inferir artista a partir do uploader e sem streams. |
| [Apple Music API](https://developer.apple.com/documentation/applemusicapi) | Comercial; catálogo songs, storefront BR | Oficial; developer token assinado externamente, conta habilitada | `limit` até 25 no adaptador e `offset`; quota efetiva não confirmada | **Integrável, depende de credenciais**. Mocks; geração e renovação do JWT não implementadas. Sobrepõe parte do catálogo iTunes. Sem tocar prévias/áudio. |
| [Last.fm](https://www.last.fm/api/show/track.search) | Metadados; método `track.search` busca nome da faixa, não busca global de álbuns | Oficial; API key; método de busca sem sessão de usuário | `limit`/`page`; erro 29 para rate limit; sem assumir quota numérica | **Integrável, depende de credenciais**. Mocks; metadados e links, sem inferir direito de streaming da flag histórica `streamable`. |

Todos os adaptadores usam HTTPS e endpoints fixos. URLs de paginação retornadas pelas
fontes não são requisitadas diretamente; o próximo offset/token é usado no endpoint
permitido. Fonte inválida, timeout ou bloqueio não interrompe as demais. Há no máximo
duas tentativas por chamada; 429 com Retry-After longo retorna estado de limite sem
prender a busca. As taxas acima são da documentação; intervalos locais são escolhas
conservadoras do aplicativo, não garantias de quota por IP entre vários processos.

## Redirecionamentos e candidatos adicionais

Os 12 atalhos da interface não consultam resultados: codificam os termos e abrem o
site escolhido. A navegação e seus parâmetros ainda podem mudar; não foram feitos
testes de ponta a ponta em todos esses sites. Bloqueios não foram contornados.

| Fonte / referência oficial visitada | Categoria e busca | Acesso / API / paginação / limites | Classificação e razão |
|---|---|---|---|
| [Bandcamp](https://bandcamp.com/developer) | Independente; pesquisa pública de faixas/álbuns | API oficial é para contas de selos/fulfillment, OAuth e aprovação; não é busca pública geral. Limites não relevantes para o atalho | **Somente pesquisa externa**. Página de resultados com termos; licenças e aquisição dependem de cada artista. |
| [Deezer](https://developers.deezer.com/) | Comercial; pesquisa no site | Portal/documentação atual não puderam ser validados; não se presume acesso à API a partir de endpoints antigos | **Somente pesquisa externa; API sujeita a validação**. Sem áudio ou preview extraído. |
| [YouTube Music](https://music.youtube.com/) | Comercial/vídeos; pesquisa no site | Nenhuma API separada de YouTube Music foi adotada; YouTube Data é outro adaptador | **Somente pesquisa externa**. Não usa endpoints internos nem bibliotecas de sessão. |
| [Free Music Archive](https://freemusicarchive.org/) | Licenças abertas; pesquisa no site | Página respondeu 403 pela ferramenta de pesquisa; API atual não verificada; limites desconhecidos | **Somente pesquisa externa**. Licença precisa ser conferida por faixa; parte do catálogo pode aparecer em Openverse. |
| [Musopen](https://musopen.org/music/) | Clássica/acervos; busca pública | Navegação e filtros públicos; API de busca apropriada não validada, limites de conta/download variáveis | **Somente pesquisa externa**. Licenças indicadas na página; não pressupor ausência de restrições para toda gravação. |
| [Newgrounds Audio](https://www.newgrounds.com/audio) | Música independente e outros áudios; campo público de busca | Busca no site; API pública de descoberta musical não verificada; limites desconhecidos | **Somente pesquisa externa**. Direitos dependem da publicação; sem scraping. |
| [Audiomack](https://audiomack.com/) | Independente; faixas e álbuns | Site público; acesso API autorizado e quotas não validados | **Somente pesquisa externa**. Não reproduz/offline fora dos recursos da plataforma. |
| [SoundClick](https://www.soundclick.com/) | Independente; pesquisa no site | Página não acessível pela ferramenta; API e parâmetros de navegação sujeitos a validação | **Somente pesquisa externa**, atalho não confirmado no navegador. Condições por artista. |
| [Library of Congress](https://www.loc.gov/apis/json-and-yaml/requests/endpoints/) | Acervo público/histórico; `/audio/` e busca | API oficial pública, `fo=json`, `q`, `c`, `sp`; quota não confirmada. Teste JSON respondeu 403 neste ambiente | **API possível, sujeita a validação; atalho externo**. Direitos dependem do item, não presumir domínio público de todo acervo. |
| [Discogs](https://www.discogs.com/developers/) | Metadados de lançamentos, não acervo de áudio | Portal respondeu 403; busca de base exige acesso conforme política, quotas atuais não confirmadas | **Somente pesquisa externa; adaptador futuro dependente de validação**. Não recebe resultados de áudio. |
| [setlist.fm](https://api.setlist.fm/docs/) | Setlists de apresentações; não gravações | API oficial exige chave, gratuita para projetos não comerciais; paginação e limites devem ser avaliados por método | **Somente pesquisa externa**. API integrável para shows, pouco adequada ao modelo de resultado de faixa com áudio. |
| [Live Music Archive](https://archive.org/details/etree) | Shows autorizados conforme política de cada coleção/artista | Mesmo mecanismo público do Internet Archive; paginação e limites conforme API acima | **Incluído no adaptador Archive**, mais atalho focado na coleção etree. Resultado é show/item, não música individual garantida. |
| [Relisten](https://relisten.net/) | Apresentações ao vivo | Página respondeu 403; API específica não validada; limites desconhecidos | **Possível integração sujeita a validação**; não há adaptador/atalho específico. Parte dos acervos já é pesquisável no Archive. |
| [Funkwhale](https://www.funkwhale.audio/) | Descentralizada; bibliotecas de instâncias | API e acesso dependem do servidor escolhido, permissões e versão. Não existe um catálogo público universal presumido | **Possível integração sujeita a validação** e escolha de instância autorizada; não implementado. URLs arbitrárias não aceitas neste MVP. |
| [UCSB Cylinder Archive](https://cylinders.library.ucsb.edu/) | Gravações históricas | Resposta 403; API de busca não validada; limites desconhecidos | **Possível integração sujeita a validação**. Sem prometer status de domínio público global ou scraping autorizado. |
| Espelhos, ferramentas e provedores restantes do [inventário FMHY](fmhy-audio-links.json) | Mistura de catálogos, players, conversores, rádio e downloads | Acesso, API, quotas e licença **não avaliados individualmente** | **Não integrados**. Não inventar endpoints, autorização ou disponibilidade. Ferramentas sem busca não servem como fonte de faixas. |

Nenhuma fonte foi declarada permanentemente incompatível apenas porque respondeu com
erro de rede. O relatório distingue bloqueio atual, falta de credenciais, falta de
API adequada e candidato ainda não avaliado. Não existe garantia de localizar toda
música ou gravação rara. Metadados indexados e conteúdos enviados por terceiros
podem estar incorretos; os links preservam a origem para conferência.
