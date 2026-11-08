# Relatório de implementação — 05/11/2026

> Atualização 0.4.0: [grupos de provedores, downloads e ZIP selecionado](PROVIDERS_DOWNLOADS.md).
> As restrições de catálogo exclusivamente gratuito da versão anterior foram substituídas pelo novo escopo solicitado.


> Atualização 0.3.0: [fontes gratuitas, créditos e configurações](FREE_WEBSITES.md).
> As contagens e APIs pagas abaixo descrevem a entrega inicial e foram substituídas pelo relatório atual.


## Entrega efetiva

O projeto era uma pasta Git vazia. Foi implementado um aplicativo completo em Python
com FastAPI/HTTPX/Pydantic/SQLite e HTML/CSS/JavaScript sem framework, preservando a
stack solicitada. O Python disponível é 3.14.6; o projeto declara mínimo 3.12.

- Launcher: reserva socket em loopback, escolhe porta livre se necessário, verifica
  readiness, abre navegador e mantém o servidor até Ctrl+C ou encerramento pela interface.
- 13 adaptadores independentes, registrados sem alteração do motor central.
- 7 APIs públicas consultáveis sem credenciais; 6 APIs com acesso opcional configurável.
- 12 atalhos externos explicitamente separados de resultados encontrados.
- Consultas paralelas, limite de concorrência, timeout por fonte, duas tentativas para
  falhas transitórias, Retry-After e bloqueio temporário por fonte após 429.
- SQLite persistente com cache por fonte/consulta/página, ajustes, histórico e estados;
  limites de tamanho e expiração. Credenciais não são persistidas no banco.
- Normalização de acentos, capitalização e pontuação para conferência estrita de nomes.
  Artista e título precisam coincidir no mesmo registro. Não há score fuzzy permitindo
  resultados alheios, nem identificação acústica da gravação.
- Correspondências agrupadas por título/artista/tipo preservam os links de todas as
  fontes; desconhecidos e itens de acervo não são agrupados por título sozinho.
- Eventos NDJSON progressivos, cancelamento e paginação independente das fontes.
- UI responsiva com filtros, seleção, ajustes, credenciais de sessão, estados, cache,
  histórico, consulta de logs e encerramento. Usa texto seguro do DOM, sem HTML dos provedores.
- Fronteira local: Host/Origin, rejeição cross-site, cabeçalho para alterações, CSP,
  validação de entrada e ausência de proxy genérico. Não existe opção de bind público.
- Build PyInstaller nativo Windows x64 com estáticos incluídos e caminhos persistentes
  fora da extração temporária. Scripts de execução para Windows e Linux.

## Pesquisa e cobertura

[SOURCES.md](SOURCES.md) registra documentação oficial, data, categoria, pesquisa,
acesso, paginação, limites conhecidos/desconhecidos, restrições, dados e viabilidade.
[fmhy-audio-links.json](fmhy-audio-links.json) preserva 1.188 URLs externas extraídas
do catálogo em 05/11/2026; isso inclui ferramentas e espelhos e não representa 1.188
fontes de busca integradas ou individualmente aprovadas.

Funcionais sem chave, com dados reais: **iTunes, MusicBrainz, Internet Archive, Audius,
Openverse, Wikimedia Commons e Mixcloud**. MusicBrainz também apresentou um 503
transitório numa execução anterior; as outras fontes continuaram entregando resultados.

Implementadas e testadas por mocks, mas **sem validação real por falta de credenciais**:
**Jamendo, YouTube, Spotify, SoundCloud, Apple Music API e Last.fm**. Uma chave não
garante elegibilidade da aplicação nem autorização de reprodução. SoundCloud e Apple
exigem token válido fornecido pelo usuário e renovação manual; Spotify obtém/renova
Client Credentials no backend.

Library of Congress tem API documentada, mas retornou 403 neste ambiente: permanece
como atalho. Funkwhale precisa de instância/autorização definida; Relisten e UCSB
precisam de acesso e documentação validados. Bandcamp tem API oficial que não oferece
a busca pública geral necessária. Deezer tem atalho, com API atual não validada.
Não foi tentado contornar nenhum bloqueio.

## Evidências de validação

- **68 testes automatizados**: modelos, URLs, campos ausentes, todos os 13 adaptadores
  isolados, payloads vazios, paginação, respostas inválidas, paralelismo, teto de
  concorrência, cancelamento/limpeza, timeout, rede, cache/TTL, SQLite, histórico,
  HTTP 401/403/404/429/500, credenciais ausentes, ranking, agrupamento e preservação
  de links; API local, estáticos, Host/Origin, não devolução/persistência de segredos.
- `node --check everytune/static/app.js`: análise sintática de JavaScript.
- Verificação mecânica da interface pelo Impeccable: nenhuma ocorrência reportada.
- Teste real de processo em [live-smoke.json](live-smoke.json): servidor, HTML, JS,
  CSS, ícone, OpenAPI, buscas reais e encerramento limpo. O script agora usa combinações
  explícitas de artista/faixa e reproduz a regressão de resultados alheios.
- Teste do executável em [executable-smoke.json](executable-smoke.json): mesmos checks
  no binário, inclusive arquivos estáticos extraídos e consultas externas reais.
- Teste de navegador com Edge headless em `scripts/browser_smoke.py`: busca real,
  filtro de plataforma, próxima página preservando atalhos externos, ajustes e
  credenciais sem eco, limpeza de cache, logs, ausência de overflow em 390px e de
  erros JavaScript. Capturas e relatório em `artifacts/`, não versionados.
- Revisão visual independente das quatro capturas: **aprovado**, sem achados materiais
  ou correções necessárias. Limites da revisão: não mediu contraste, não testou leitor
  de tela/teclado nem todo o conteúdo abaixo do recorte. Links distintos da mesma
  plataforma podem ter rótulos iguais quando agrupados.

O pytest emite um aviso de depreciação do Starlette sobre a futura troca do transporte
do TestClient de HTTPX para HTTPX2. Os testes continuam passando com as versões fixadas;
HTTPX é mantido no aplicativo conforme a stack solicitada. Python 3.12, Linux e Windows
11 não foram executados neste ambiente; a compatibilidade declarada ainda requer CI
ou testes nativos nesses destinos. Não se afirma sucesso de build Linux.

## Limitações técnicas, acesso e direitos

- Não cobre automaticamente todos os links do FMHY. O inventário é descoberto, não
  um registro de endpoints. Não há scraping de resultados, bibliotecas comunitárias
  de sessão, DRM, autenticação contornada, stream extraído ou arquivo de música hospedado.
- APIs mudam e serviços podem bloquear/regionalizar consultas. A saúde no painel é
  o estado da última consulta, não uma monitorização ativa ou SLA.
- iTunes não tem paginação documentada no método usado; Spotify limita páginas a 10;
  Apple a 25. Uma página cheia pode sugerir próxima página vazia em APIs sem total.
- A busca de metadados varia por fonte: MusicBrainz consulta gravação/artista/release;
  Last.fm usa nome de faixa. Mixcloud pesquisa programas, não cada faixa interna.
  Archive inclui áudio que pode não ser música; Commons pode devolver sons e discursos.
- A conferência é textual, não garante a mesma gravação/master nem distingue artistas
  homônimos sem identidade adicional. A busca estrita pode omitir aliases, créditos
  diferentes, versões não solicitadas e resultados sem artista verificável.
- Permissões nulas não significam negação: significam desconhecidas. Indicadores de
  áudio/download são dados do provedor e não um parecer sobre direitos territoriais.
  Conteúdo do usuário pode conter metadados/licenças incorretos. Verifique a página original.
- Sem reprodução ou download integrados; prévias não são apresentadas ou consumidas.
  Arte promocional, atribuições e marcas continuam sujeitas aos termos dos provedores.
- Credenciais em memória/ambiente são acessíveis ao próprio usuário/processo local.
  Não existe cofre de segredos persistente. Histórico é informação pessoal guardada
  no SQLite local; o usuário pode apagar o diretório com o app encerrado.
- Limites por fonte são por processo. Várias instâncias/programas usando o mesmo IP
  podem somar tráfego além da quota. Sem autenticação multiusuário ou exposição em LAN.
- Atalhos externos não foram todos testados em navegador; sites podem ignorar termos,
  exigir conta ou mudar rotas. São identificados como navegação externa, nunca resultados.
- Binário sem assinatura e sem instalador/updater. Distribuição em outras máquinas
  precisa de validação nativa. Fechar a aba não encerra o servidor.

## Execução, distribuição e decisões pendentes

Abra `dist/EveryTune.exe` no Windows ou execute `python -m everytune` no ambiente virtual.
Para modo manual: `python -m everytune --no-browser --port 8765`. Gere um novo binário
com `python scripts/build.py`, após instalar `requirements-dev.txt`; faça o build Linux
no próprio Linux. O [README](../README.md) contém todos os comandos e a árvore de arquivos.

**Nenhuma decisão é necessária para usar a busca básica.** Opcionalmente, o usuário
pode fornecer credenciais das seis plataformas, escolher uma instância Funkwhale
autorizada para expansão e decidir se precisa distribuir builds assinados em outros
sistemas. Essas opções não bloqueiam o executável e as fontes públicas já entregues.
