# JUMO-DL e pesquisa por créditos — 05/11/2026

## O que foi observado

A [página JUMO-DL](https://jumo-dl.pages.dev/) respondeu HTTP 200, versão exibida 2.0.9.
O HTML e o JavaScript público foram inspecionados como texto; nenhuma implementação
foi copiada para o EveryTune. A interface possui busca de álbuns/faixas, região,
qualidade e preferências de nomes, metadados, capas, encartes e empacotamento.
Essas opções de salvamento não demonstram uma licença para redistribuição de áudio.

O frontend foi aberto em Edge headless e usado normalmente: preencher `viy2tek` e
pressionar Enter. Requisições de mídia/arquivos de áudio foram bloqueadas pelo teste;
nenhum botão de download foi acionado, nenhuma credencial foi fornecida ou extraída.

| Operação observada no próprio frontend | Resultado |
|---|---|
| GET `/symdofufvpjpgkmru` | 200; objeto com `regions` e `default`; US disponível |
| GET `/qggybiqvrmvapbsrfrlg?query=viy2tek&offset=0&limit=30&region=US&view=ui` | 403; objeto de erro `Invalid request context.` |
| Preenchimento da barra sem Enter | A mesma rota de pesquisa respondeu 403; a UI mostrou sugestões indisponíveis |
| Enter após preencher a busca | A mesma rota respondeu 403; a UI mostrou erro |

O endereço visível permaneceu na homepage durante esse fluxo. **Nenhum deep-link de
pesquisa foi comprovado.** Portanto, o atalho seguro é apenas a homepage, sem inventar
`?q=`, `?query=` ou fragmento. A falha de pesquisa impediu observar uma página de
resultados bem-sucedida, então não se afirma ausência permanente de deep-links.

O endpoint acima é **interno, ofuscado, não documentado como API pública**. Sua presença
no JavaScript não equivale a uma autorização ou contrato estável. O 403 não foi
contornado: não se reproduziram assinaturas, cookies, cabeçalhos de contexto, tokens
compartilhados ou mecanismos antiabuso. O teste não identifica a causa exata do 403
nem prova que o serviço falhe para todos os visitantes.

## O que permanece inferido ou desconhecido

O diretório FMHY identifica JUMO como ferramenta associada a Qobuz, mas **a execução
observada não recebeu metadados suficientes para confirmar a origem do catálogo**.
O bundle é ofuscado; a inspeção estática não revelou uma API de catálogo utilizável
nem um repositório/documentação pública do operador dentro do limite examinado.
Os prints fornecidos pelo usuário demonstram resultados anteriores, mas não provam
qual índice, licença ou regra de correspondência foi usado.

Não foi possível confirmar se o nome pesquisado é encontrado em créditos de produção,
créditos principais, compositor, texto livre ou outro índice. A presença de um nome em
uma lista de resultados não permite atribuir a ele o papel de produtor/engenheiro.
O EveryTune deve exibir o papel real sustentado pelos metadados, com a evidência.

A página antiga de API Qobuz `/api.shtml` retornou 404 neste ambiente. O documento
primário disponível [Qobuz API Terms of Use](https://static.qobuz.com/apps/api/QobuzAPI-TermsofUse.pdf)
é datado de 2011 e exige identificadores próprios emitidos pelo serviço. Não se adotou
uma chave extraída de aplicativos alheios nem se presumiu elegibilidade atual. Uma
integração Qobuz direta precisa de acesso próprio e contrato atual validado.

**Classificação JUMO:** pesquisa externa na interface original; integração de resultados
bloqueada/não validada. Pode ser referência de organização de preferências, sem ser
apresentado como adaptador funcional ou API oficial.

## Alternativa concreta: Discogs

O [portal de desenvolvedores Discogs](https://www.discogs.com/developers/) respondeu
403 nesta sessão, mas a API pública respondeu sem autenticação. O [cliente publicado
pela organização Discogs](https://github.com/discogs/discogs_client/blob/master/discogs_client/models.py)
contém `Artist.releases` e créditos `extraartists`; esse cliente está arquivado desde
2020 e serve como referência de contrato, não como dependência adotada.

Verificações reais, com User-Agent identificável e pausas entre chamadas:

- `GET https://api.discogs.com/database/search?q=viy2tek&type=artist`: 200, lista vazia.
  Isso não prova inexistência do artista em outros catálogos.
- Pesquisa de `Rick Rubin`: 200, artista `68211` com nome exato, além de homônimos
  numerados. A pessoa precisa ser resolvida por ID; não juntar todos por similaridade.
- `GET https://api.discogs.com/artists/68211/releases?per_page=3&page=1`: 200,
  paginação com 1.707 itens; os primeiros registros evidenciam papéis Main e Remix.
- Uma página de 100 itens também evidenciou `Producer`. Esse papel veio do catálogo;
  não foi inferido do nome, do gênero musical ou da posição do álbum nos resultados.
- Cabeçalhos observados: `X-Discogs-Ratelimit: 25`, `Remaining: 22`, `Used: 3` em uma
  chamada. Isso descreve essa resposta, não garante uma quota eterna por aplicação/IP.
- Um detalhe de master consultado não tinha `extraartists`; o catálogo não deve
  inventar subpapéis quando só a relação resumida está disponível.

O adaptador recomendado resolve a pessoa, pede seleção quando há ambiguidade e só
então pagina seus lançamentos, mantendo a evidência de ID e o papel original. Main
significa crédito principal, não produtor; Remix não significa engenheiro. A classificação
de lançamento/master é preservada, sem fingir que cada item é uma faixa individual.
Nenhuma das 1.707 entradas foi varrida integralmente nesta verificação.

As [diretrizes primárias de créditos Discogs](https://support.discogs.com/hc/en-us/articles/360005006834-Database-Guidelines-10-Credits)
distinguem créditos de lançamento e de faixa. O [guia de pesquisa](https://support.discogs.com/hc/en-us/articles/360003622014-How-To-Browse-Search-In-The-Database)
explica a separação entre artistas, lançamentos e detalhes. Dados são comunitários,
podem estar incompletos e não concedem autorização para reprodução/download.

### Adaptador Discogs entregue

`everytune/sources/discogs.py` implementa `DiscogsCredits`, sem dependência nova. Ele só
consulta créditos no modo correspondente; a busca de faixa exata permanece inalterada.
Sem ID, devolve identidades para escolha e mantém homônimos numerados separados. Com
ID, valida o nome e o ID na API antes de consultar lançamentos; não admite caminhos
arbitrários ou uma mudança silenciosa de pessoa. Cada crédito contém pessoa, ID,
papel resumido e link de evidência. Paginação é explícita e o intervalo é de 3 segundos.

**8 testes com mocks passaram** em `tests/test_discogs.py`. Cobrem modo de faixa sem
chamadas, seleção de homônimos, papéis reais, vínculo por ID, paginação, entradas
inválidas, troca indevida de identidade e resposta vazia. Um teste real do próprio
adaptador para `Rick Rubin`, ID `68211`, devolveu 3 lançamentos e cursor `2`, com os
papéis Main, Main e Remix. Extrato: `artifacts/jumo-discogs-adapter-live.json`.
A integração no registro e na interface é responsabilidade do trabalho principal.

MusicBrainz é uma alternativa complementar: seu [modelo de dados](https://musicbrainz.org/doc/MusicBrainz_Database/Schema)
inclui profissionais da música e relacionamentos, em vez de presumir que toda pessoa
seja intérprete. Para uma consulta por produtor/engenheiro, nomes devem resolver uma
identidade e relações explícitas devem sustentar os resultados. A inspeção desta tarefa
não fez uma varredura adicional do MusicBrainz, evitando sobrepor consultas do outro
trabalho na mesma sessão e exceder seu limite por IP.

## Evidência reproduzível e limites

- `artifacts/jumo/index.html`, `artifacts/jumo/Pe2qwLIQ.js`: arquivos públicos observados.
- `artifacts/jumo-runtime.json`: destinos, parâmetros de busca e respostas sanitizadas;
  não contém cookies/cabeçalhos de autenticação ou URLs de áudio.
- `artifacts/jumo_probe.py`, `artifacts/jumo-search.png`: roteiro e captura do teste.
- `artifacts/jumo-discogs-live.json`, `artifacts/jumo-discogs-credits.json`: extratos reais.
- REA: análise-pai `ev_78abbd67d696314c0bc88478c3114aaafb39c3395838223925c4f8f3946ac69f`;
  resumo `ev_aac363298038ce9bc050b79faf94e97ba90c282a847deb702f1b353870304ff8`.
  Dois arquivos inventariados; um JavaScript analisado sem falha de parsing. Inventário
  completo dentro da pasta; grafo semântico parcial por atingir teto de 100.000 nós.
  A análise estática não prova execução; as observações de HTTP vieram do teste de navegador.

Não se validaram downloads, direitos de áudio, funcionamento em outro navegador/IP,
credenciais Qobuz nem completude de créditos. O 403 deve continuar visível como limitação.
