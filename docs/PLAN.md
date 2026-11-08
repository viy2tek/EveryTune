# EveryTune — plano de execução

O pedido fornecido em 05/11/2026 é a especificação. Decisões técnicas delegadas pelo usuário.

## Arquitetura e alcance
Python 3.12+, FastAPI, HTTPX, Pydantic, SQLite e frontend sem framework. Adaptadores
retornam páginas normalizadas. Um motor central controla concorrência, timeout,
retry, cache e agrupamento. Interface consome eventos NDJSON progressivos pela API.
O launcher reserva uma porta de loopback antes de iniciar e abre o navegador após readiness.
PyInstaller inclui os estáticos; os dados persistem no diretório do usuário.

API oficial é a primeira opção: estável e documentada, mas sujeita a quota e credenciais.
Bibliotecas comunitárias acrescentariam dependências sem benefício neste MVP.
Scraping exige manutenção e permissão específica: usar links externos onde a API não atende.
Não há player nem downloader: a descoberta preserva links e permissões informadas pela fonte.

## Tarefas e verificações
- [x] Pesquisar fontes FMHY e documentação primária; registrar matriz em SOURCES.md.
- [x] Modelos, adapters e transport: mocks de payload, credenciais, paginação e HTTP inválido.
- [x] SQLite e motor: testes de normalização, duplicatas, isolamento, timeout, retry e cache.
- [x] API e segurança: testes REST, estáticos, origem/host e não divulgação de segredos.
- [x] Frontend responsivo: busca progressiva, filtros, painel, histórico e logs sanitizados.
- [x] Launcher, scripts e documentação: smoke real e build Windows com estáticos.

## Riscos a verificar
Payloads incompletos não podem derrubar outras fontes. Sites externos não são resultados.
Credenciais não podem aparecer em respostas ou logs. Host/origin locais previnem acesso
por páginas maliciosas. Paginação deve manter cursores por fonte. Metadados não concedem áudio.

Não existe promessa de cobrir cada link do FMHY: o catálogo inclui ferramentas, espelhos,
rádios e serviços sem busca de faixas. A matriz registra a cobertura e os limites reais.
