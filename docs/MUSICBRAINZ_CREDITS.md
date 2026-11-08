# Créditos MusicBrainz — verificação em 05/11/2026

Adaptador: `MusicBrainzCredits`, ID `musicbrainz_credits`. É uma consulta de metadados
e relações oficiais; não acessa áudio. Referência primária:
[MusicBrainz API](https://musicbrainz.org/doc/MusicBrainz_API), especialmente lookup,
relationships e subqueries (`recording-rels`, `release-rels`, `work-rels`). A ferramenta
de pesquisa recebeu 429 na página de documentação; o comportamento foi corroborado
diretamente nos endpoints HTTPS oficiais, sem chaves e respeitando o intervalo da fonte.

## Comportamento

1. Busca `/ws/2/artist/` com `query=artist:"nome"`, `fmt=json`, limite 100.
2. Exige nome completo normalizado. Não trata nome parecido como a mesma pessoa.
3. Havendo homônimos, retorna identidades e desambiguações para escolha antes dos créditos.
   Se a página de identidades é parcial, também não presume identidade única.
4. Uma identidade única ou selecionada é consultada em `/ws/2/artist/MBID` com
   `inc=recording-rels+release-rels+work-rels`. O nome do lookup é conferido novamente.
5. Relações fornecem gravações, lançamentos e obras, cada um com seu tipo e página
   original. Os papéis são os informados pelo MusicBrainz: producer, engineer, mix,
   writer, composer, instrument etc., preservando atributos adicionais quando presentes.
6. Relações múltiplas para o mesmo item são reunidas preservando todos os créditos.
   O intérprete fica nulo quando o lookup não o informa: produtor não vira intérprete.

`person_id` precisa ser UUID válido. Também aceita a identidade configurada para esta
fonte em `terms.identities`. Não consulta relações no modo de faixa/automático.

## Evidência real

Busca `Butch Vig` retornou uma identidade de nome exato:
[ba30915c-4d33-43c5-8c37-ead0b8061517](https://musicbrainz.org/artist/ba30915c-4d33-43c5-8c37-ead0b8061517).
O lookup oficial com os três includes retornou HTTP 200, 316.255 bytes e 671 relações.
Entre elas: 198 relações de produtor em gravações, 57 de engenheiro em gravações,
59 de produtor em lançamentos e 113 de writer em obras. Esses números são relações,
não quantidade de músicas únicas. Por exemplo, “Come as You Are” aparece com relação
de engenheiro; a evidência é a relação da identidade com o registro, não uma inferência
a partir do nome da música. O adaptador completo foi executado com dados reais e
normalizou 493 itens únicos desse conjunto, reunindo múltiplos papéis por item;
a primeira página de 3 teve `next_cursor=3`. A busca exata `viy2tek` retornou `count=0`
nesta fonte.

## Limites

O catálogo é colaborativo e incompleto; ausência não prova inexistência de crédito.
A paginação de itens é local sobre as relações entregues no lookup, não uma promessa
de catálogo completo. Cada página pode repetir as duas consultas oficiais, mantendo
limite de requisição por fonte e cache do motor. Não busca centenas de registros
individualmente para preencher intérprete/capa/dados ausentes. Relações de obras
não são apresentadas como arquivos de áudio ou gravações.

Os testes isolados usam fixtures para papéis explícitos, identidade ambígua, seleção,
UUID inválido, nome divergente, paginação, modo sem créditos e nome apenas parecido.
