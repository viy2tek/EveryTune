# EveryTune — leis do projeto
# Estado: requisitos 1–42 documentados; provas gerais pendentes.
# As sete leis ui_* abaixo formalizam somente a política de campos do editor.
# As nove leis home_* formalizam guardas parciais da home emitida.
# Os requisitos 1–42 são comentários; as sete leis ui_* são declarações formais.
# O servidor é Python; o editor importa o JS compilado de ui_policy.bend.
# As provas da política UI não garantem os requisitos completos nem o app Python.
# Todas as regras abaixo são requisitos, não afirmações de conformidade auditada.
# Cobertura: comportamento atual e invariantes desejados do EveryTune; sem recursos novos.
# Lógica pura pode receber leis Bend após integração. Rede, disco, interface e
# empacotamento também exigem testes de integração ou verificações manuais.
# Os limites numéricos pertencem à configuração/código: este catálogo não os duplica.
# As cinco primeiras regras são mantidas; as demais detalham invariantes distintos.
# Referência: https://github.com/bendlang/bend/blob/main/guide/GUIDE.md
#
# 1. strict_search_identity — Busca estrita preserva a identidade da faixa.
# Regra: aceite um candidato somente quando todos os campos solicitados
# (artista e/ou título, incluindo a versão indicada no título) corresponderem
# no mesmo registro, usando a normalização documentada do projeto.
# Não remova marcadores como Live, Remix ou Remastered para forçar igualdade.
# Preserve o comportamento próprio dos modos source, auto e credits.
# Por quê: evita entregar covers, homônimos e versões diferentes como exatas.
# Aplicação atual: everytune/models.py (normalize, rank); tests/test_precise_search.py.
#
# 2. grouping_preserves_provenance — Agrupamento preserva as origens.
# Regra: agrupar resultados mantém cada referência (source, source_id, url),
# com créditos, licença e disponibilidade associados à origem que os informou.
# Campos desconhecidos permanecem desconhecidos. Igualdade de título isolada
# não autoriza unir artistas desconhecidos ou gravações de versões distintas.
# Por quê: evita perder links e atribuir permissões ou créditos de outra fonte.
# Aplicação atual: everytune/models.py (rank, TrackResult) e apresentação dos grupos.
#
# 3. federation_preserves_success — Falhas ficam isoladas por fonte.
# Regra: uma falha ou timeout de uma fonte preserva os resultados válidos
# das demais. Para as mesmas respostas finais, permutar a ordem de chegada
# preserva o conjunto de resultados e suas origens, ignorando tempos e ordem visual.
# Não prometa igualdade entre respostas reais obtidas em momentos diferentes.
# Por quê: uma plataforma indisponível não deve inutilizar toda a pesquisa.
# Aplicação atual: everytune/engine.py (search_source, events).
#
# 4. download_matches_selection — Preparação respeita seleção e limites.
# Regra: uma preparação concluída contém exatamente as opções validadas que
# o usuário selecionou, identificadas por seus IDs, com nomes de arquivo seguros.
# Respeite permissões explícitas exigidas pelo conector e o limite de bytes
# durante a escrita. Falha ou cancelamento não pode resultar em sucesso parcial
# apresentado como completo; remova os arquivos parciais.
# Disponibilidade offline de streaming não significa permissão de exportação.
# Por quê: evita baixar itens extras, exceder limites e entregar pacotes incompletos.
# Aplicação atual: everytune/downloads.py (prepare, _write, _run, cancel).
#
# 5. outbound_requests_are_validated — Transferências usam destinos permitidos.
# Regra: o transporte de consulta/transferência externa exige HTTPS, porta 443,
# ausência de credenciais na URL e endereços IP públicos verificados via DNS.
# Revalide cada redirecionamento e conecte ao endereço efetivamente validado.
# Encaminhe credenciais somente ao destino autorizado a recebê-las.
# Esta regra não bloqueia o servidor local 127.0.0.1 usado pela interface.
# Por quê: impede que links externos provoquem acesso à rede privada ou vazem tokens.
# Aplicação atual: everytune/public_http.py e everytune/downloads.py (_get).
#
# Busca, identidade e interpretação
#
# 6. normalization_is_stable — Normalização previsível.
# Regra: normalizar duas vezes equivale a normalizar uma vez; diferenças aceitas
# de caixa, acentos e pontuação não autorizam correspondência por semelhança.
# Por quê: o mesmo nome deve ser comparado de forma consistente, inclusive no cache.
# Onde/verificar: everytune/models.py; tests/test_models.py; tests/test_precise_search.py.
#
# 7. source_mode_is_unverified — Resultados da fonte não são confirmação.
# Regra: no modo source, preserve o texto recebido após o trim de entrada e a
# ordem de candidatos de cada fonte; não rotule esses candidatos como nomes conferidos.
# A exclusão explícita de covers mantém a ordem dos candidatos restantes;
# essa filtragem de versão não transforma o modo source em conferência de identidade.
# Por quê: explorar a resposta original é diferente de verificar artista e faixa.
# Onde/verificar: everytune/models.py; tests/test_federated_search.py.
#
# 8. explicit_fields_are_authoritative — Campos explícitos prevalecem.
# Regra: artista e faixa informados separadamente não são reinterpretados por um
# separador no nome. Codifique consultas no componente correto da URL/corpo, sem injeção.
# Por quê: nomes com hífens e caracteres especiais não podem mudar a intenção da busca.
# Onde/verificar: everytune/models.py; everytune/sources/custom.py;
# tests/test_precise_search.py; tests/test_federated_search.py.
#
# 9. credits_require_evidence — Créditos vêm de evidência da fonte.
# Regra: aceite colaboração pelo nome individual ou ID fornecido pelo provedor;
# preserve o papel original. Não divida bandas por vírgula ou & para inventar pessoas.
# Por quê: aparecer na pesquisa ou ser artista principal não comprova produção/engenharia.
# Onde/verificar: everytune/sources/; tests/test_deezer.py; tests/test_discogs.py;
# tests/test_musicbrainz_credits.py; tests/test_precise_search.py.
#
# 10. selected_identity_is_bound — Homônimos permanecem distintos.
# Regra: apresente identidades ambíguas; após seleção, vincule o ID à sua fonte
# e valide-o antes de consultar. Não troque silenciosamente a pessoa escolhida.
# Por quê: pessoas com o mesmo nome não devem compartilhar créditos por engano.
# Onde/verificar: everytune/sources/; tests/test_musicbrainz_credits.py; tests/test_discogs.py.
#
# 11. mentions_are_not_tracks — Menção em página não comprova faixa.
# Regra: distinga posts, álbuns, vídeos, itens de acervo e faixas. Uma menção no
# título de uma página não satisfaz, por si só, uma busca estrita de faixa ou crédito.
# Por quê: evita apresentar matérias e páginas de catálogo como gravações confirmadas.
# Onde/verificar: everytune/models.py; tests/test_free_websites.py; tests/test_precise_search.py.
#
# Fontes, federação e cache
#
# 12. source_scope_is_enforced — Seleção vale também no servidor.
# Regra: consulte somente fontes conhecidas, habilitadas e incluídas no foco e
# na seleção efetiva. Seleção vazia explícita não equivale a seleção omitida.
# Por quê: evita consultas involuntárias e contornar filtros apenas mudando a interface.
# Onde/verificar: everytune/engine.py; everytune/providers.py; tests/test_provider_groups.py.
#
# 13. adapter_output_is_validated — Respostas externas não são confiáveis.
# Regra: valide tipos, campos e links de cada registro; descarte registros inválidos
# conforme o contrato do adaptador, sem inventar valores nem derrubar outras fontes.
# Por quê: um provedor pode mudar o formato ou retornar dados incompletos/maliciosos.
# Onde/verificar: everytune/models.py; everytune/sources/; tests/test_sources.py;
# tests/test_custom_sources.py; tests/test_engine.py.
#
# 14. pagination_is_query_scoped — Paginação pertence à consulta e à fonte.
# Regra: valide cursores; preserve consulta, identidade, país e modo ao paginar.
# Não siga URLs arbitrárias de paginação recebidas da origem. Preserve candidatos
# ainda não entregues quando a página externa exceder o limite local.
# Por quê: evita páginas de outra busca, acesso indevido e perda silenciosa de resultados.
# Onde/verificar: everytune/sources/; tests/test_sources.py; tests/test_free_websites.py;
# tests/test_musicbrainz_credits.py; tests/test_federated_search.py.
#
# 15. ordering_has_a_defined_contract — Ordenação respeita o modo.
# Regra: nos modos conferidos, use pontuação e desempates documentados estáveis;
# no modo source, preserve a ordem interna de cada fonte. Não exija ordem global
# de chegada fixa para consultas concorrentes; a regra 3 protege o conjunto final.
# Por quê: evita mudar resultados só porque uma plataforma respondeu antes.
# Onde/verificar: everytune/models.py; everytune/engine.py; tests/test_models.py;
# tests/test_federated_search.py. Desempates completos ainda precisam de validação.
#
# 16. requests_are_bounded — Consultas têm limites e respeitam a origem.
# Regra: respeite concorrência, timeout, intervalo por fonte e Retry-After;
# mantenha tentativas finitas. Esperas longas devem produzir estado útil por fonte.
# Por quê: evita travamentos, consultas excessivas e bloquear as demais plataformas.
# Onde/verificar: everytune/engine.py; everytune/sources/base.py; tests/test_engine.py;
# tests/test_sources.py; tests/test_federated_search.py.
#
# 17. search_cancellation_releases_work — Cancelamento encerra tarefas dependentes.
# Regra: ao fechar/cancelar o fluxo, cancele e aguarde as tarefas pendentes da
# pesquisa; libere recursos. A interface preserva resultados já recebidos quando aplicável.
# Por quê: uma busca abandonada não deve continuar consumindo conexões em segundo plano.
# Onde/verificar: everytune/engine.py; everytune/static/app.js; tests/test_engine.py.
#
# 18. cache_keys_separate_contexts — Cache não mistura contextos.
# Regra: a chave distingue fonte, termos interpretados, modo, identidade, país,
# limite, cursor e definição do conector. Segredos não entram em texto na chave.
# Por quê: evita reutilizar resultados de outra pessoa, página ou configuração.
# Onde/verificar: everytune/engine.py; tests/test_precise_search.py; tests/test_engine.py.
#
# 19. cache_is_expiring_and_rechecked — Cache não dispensa conferência.
# Regra: não use entradas expiradas; reaplique o filtro do modo aos candidatos
# em cache. Alterações de contexto/autorização devem invalidar o cache pertinente.
# Por quê: resultados antigos não podem escapar às regras atuais da pesquisa.
# Onde/verificar: everytune/storage.py; everytune/engine.py; everytune/app.py;
# tests/test_engine.py; tests/test_precise_search.py; tests/test_profile_security.py.
#
# Credenciais, conectores e perfis
#
# 20. secrets_stay_out_of_persistence — Segredos não vazam para dados comuns.
# Regra: credenciais configuradas pela API ficam na sessão; não exporte valores
# em perfis, respostas, SQLite, logs ou erros. Desative logs HTTP que revelem URLs autenticadas.
# Por quê: depuração e compartilhamento de perfil não devem expor acesso às contas.
# Onde/verificar: everytune/app.py; everytune/launcher.py; everytune/storage.py;
# tests/test_app.py; tests/test_custom_sources.py; tests/test_profile_security.py.
#
# 21. authorization_changes_revoke_stale_access — Mudanças invalidam acessos antigos.
# Regra: trocar/remover credenciais ou alterar/remover a fonte invalida opções e
# cancela transferências pendentes afetadas. Mudar destino/autenticação do conector
# não pode reutilizar seu token anterior; importar/restaurar perfil limpa tokens pertinentes.
# Por quê: acesso revogado não deve continuar ativo por referências ou tarefas antigas.
# Onde/verificar: everytune/app.py; everytune/downloads.py;
# tests/test_profile_security.py; tests/test_downloads.py; tests/test_custom_sources.py.
#
# 22. profile_updates_are_atomic — Perfil inválido não altera o estado válido.
# Regra: valide o perfil inteiro, IDs únicos, fontes e ajustes antes de substituir
# dados persistidos; em falha de gravação, preserve o perfil anterior por transação.
# Por quê: importar um arquivo defeituoso não deve destruir uma configuração funcional.
# Onde/verificar: everytune/app.py; everytune/storage.py; tests/test_custom_sources.py.
#
# 23. preset_migrations_preserve_user_choices — Atualizações preservam personalizações.
# Regra: instalar um novo pacote de fontes não sobrescreve edições nem reinstala
# fontes antigas removidas. Restaurar padrões ocorre apenas pela ação explícita correspondente.
# Por quê: uma atualização não deve desfazer escolhas feitas pelo usuário.
# Onde/verificar: everytune/storage.py; everytune/app.py; tests/test_federated_search.py.
#
# 24. connector_configuration_is_data — Configuração não executa código.
# Regra: valide endpoints, métodos, seletores, mapeamentos e templates permitidos;
# não aceite segredos em parâmetros comuns nem cabeçalhos de autenticação perigosos.
# Atalhos externos não recebem tokens e não se tornam consultas integradas automaticamente.
# Por quê: perfis e conectores importados atravessam uma fronteira de confiança.
# Onde/verificar: everytune/source_config.py; tests/test_custom_sources.py.
#
# 25. capabilities_and_status_are_honest — Catálogo não promete acesso inexistente.
# Regra: sem credenciais necessárias, não consulte a API protegida; apresente a
# necessidade de configuração. Diferencie sucesso vazio, sem correspondência, falha,
# timeout, limite e modo não suportado; assinatura não comprova elegibilidade à API.
# Por quê: o usuário precisa entender o que foi consultado e o que ficou indisponível.
# Onde/verificar: everytune/engine.py; everytune/sources/base.py; tests/test_engine.py;
# tests/test_profile_security.py; tests/test_app.py.
#
# Rede, descoberta de arquivos e preparação
#
# 26. automated_reading_respects_access — Leitura automatizada respeita restrições.
# Regra: nos caminhos que aplicam robots.txt, verifique a URL consultada e respeite
# suas regras/intervalos. Não execute scripts nem envie formulários de acesso/pagamento
# ou importe cookies para contornar restrições ao descobrir arquivos.
# Por quê: ler uma página não autoriza automatizar seu acesso restrito.
# Onde/verificar: everytune/sources/custom.py; everytune/downloads.py;
# tests/test_custom_sources.py; tests/test_federated_search.py; tests/test_downloads.py.
#
# 27. metadata_and_media_have_separate_transports — Pesquisa não baixa mídia.
# Regra: use transporte de metadados limitado e separado do transporte binário;
# recuse respostas incompatíveis e codificações não suportadas sem corpo ilimitado.
# Por quê: buscar nomes não deve iniciar transferências grandes ou consumir memória sem limite.
# Onde/verificar: everytune/public_http.py; everytune/app.py;
# tests/test_custom_sources.py; tests/test_downloads.py.
#
# 28. external_links_remain_external_until_verified — Espelho não é arquivo confirmado.
# Regra: mantenha páginas de acesso/espelho como links externos; a verificação HEAD
# não lê mídia e só promove a opção conforme evidência dos cabeçalhos. A transferência
# revalida a resposta. Inspeção manual exige domínio da fonte conhecida e habilitada.
# Por quê: evita tratar login, página HTML ou link arbitrário como áudio disponível.
# Onde/verificar: everytune/downloads.py; tests/test_downloads.py.
#
# 29. download_references_are_server_bound — IDs limitam o que pode ser transferido.
# Regra: preparar/servir arquivos exige referências emitidas pelo servidor, válidas
# e ligadas às opções daquela origem. Não aceite URL ou caminho arbitrário no lugar do ID.
# Referências expiradas, desconhecidas ou de fonte indisponível falham de forma explícita.
# Por quê: impede adulterar uma seleção para acessar outro recurso.
# Onde/verificar: everytune/app.py; everytune/downloads.py; tests/test_downloads.py.
#
# 30. filenames_and_archives_are_confined — Arquivos permanecem na área autorizada.
# Regra: sanitize nomes, caminhos, caracteres e dispositivos especiais do Windows;
# diferencie colisões de nomes no ZIP sem perder itens. Grave/remova somente dentro
# do diretório temporário próprio. Não extraia pacotes nem execute conteúdo baixado.
# Por quê: nomes externos não podem sobrescrever dados locais nem executar programas.
# Onde/verificar: everytune/downloads.py; tests/test_downloads.py.
#
# 31. file_metadata_is_not_quality_proof — Formato informado não comprova qualidade.
# Regra: preserve bytes do original/itens do ZIP; não converta nem renomeie para
# sugerir qualidade superior. Recuse HTML/JSON incompatível com o arquivo esperado.
# Extensão, MIME e rótulo não comprovam codec, integridade, licença ou qualidade sonora.
# Por quê: evita entregar uma página como música ou prometer FLAC real só pelo nome.
# Onde/verificar: everytune/downloads.py; tests/test_downloads.py; docs/PROVIDERS_DOWNLOADS.md.
#
# 32. transfer_accounting_uses_actual_bytes — Tamanho desconhecido continua limitado.
# Regra: confira tamanho anunciado e conte bytes durante a escrita; nenhum bloco
# pode ser gravado após exceder o limite de payload. Total desconhecido permanece
# desconhecido no progresso. Não confunda payload com overhead do contêiner ZIP.
# Por quê: Content-Length ausente/incorreto não pode desativar limites de transferência.
# Onde/verificar: everytune/downloads.py; tests/test_downloads.py.
#
# 33. preparation_lifecycle_is_consistent — Estado pronto exige artefato completo.
# Regra: ready só ocorre após concluir e fechar o artefato; só sirva arquivos prontos.
# Respeite fila, concorrência, quantidade de tarefas, espaço e timeout; erros/cancelamentos
# limpam parciais. Cancelar ou remover não apaga arquivo enquanto o navegador o recebe.
# Por quê: progresso e ações disponíveis precisam refletir o estado real da preparação.
# Onde/verificar: everytune/downloads.py; everytune/app.py; tests/test_downloads.py.
#
# 34. temporary_cleanup_preserves_saved_copies — Limpeza tem escopo e prazo.
# Regra: expire preparações inativas conforme a retenção e limpe temporários no
# encerramento; preserve transferências sendo servidas. Não remova a cópia definitiva
# salva pelo navegador; fechar o painel de downloads não equivale a cancelar a tarefa.
# Por quê: libera disco sem apagar arquivos do usuário nem interromper salvamentos.
# Onde/verificar: everytune/downloads.py; everytune/static/downloads.js;
# tests/test_downloads.py; scripts/providers_download_browser_smoke.py.
#
# Servidor local, persistência e interface
#
# 35. local_api_stays_local — A API não é publicada na rede.
# Regra: o launcher escuta em loopback; valide Host e Origin e recuse chamadas
# cross-site. Operações mutáveis exigem o cabeçalho local previsto; não amplie CORS
# nem exponha ajustes, credenciais, encerramento ou arquivos preparados à rede sem novo desenho.
# Por quê: sites visitados e outros computadores não devem controlar o aplicativo local.
# Onde/verificar: everytune/launcher.py; everytune/app.py; tests/test_app.py.
#
# 36. input_errors_are_bounded_and_private — Entrada inválida falha sem ecoar segredos.
# Regra: valide corpo, comprimentos, intervalos, IDs e campos permitidos no servidor;
# erros retornam diagnóstico seguro, sem valores sensíveis nem detalhes internos.
# Por quê: validação apenas no navegador não protege a API contra chamadas diretas.
# Onde/verificar: everytune/app.py; everytune/models.py; everytune/source_config.py;
# tests/test_app.py; tests/test_models.py; tests/test_custom_sources.py.
#
# 37. launcher_readiness_and_shutdown_are_real — Inicialização e encerramento confiáveis.
# Regra: reserve a porta usada pelo servidor, escolha outra livre em colisão e
# divulgue a URL real; abra o navegador após health responder. No encerramento,
# libere socket, tarefas, banco e temporários. Fechar a aba não significa parar o servidor.
# Por quê: evita abrir uma porta errada e deixar processos/arquivos abandonados.
# Onde/verificar: everytune/launcher.py; everytune/app.py; tests/test_app.py; scripts/smoke.py.
#
# 38. local_storage_is_bounded_and_selective — Persistência local tem escopo.
# Regra: respeite o diretório de dados escolhido e os limites de cache/histórico/logs;
# use consultas SQL parametrizadas. Limpar cache não apaga fontes, perfil ou arquivos
# salvos. Reiniciar preserva ajustes persistidos, sem prometer persistência de tokens da sessão.
# Por quê: evita crescimento ilimitado e perda de configuração ao limpar dados temporários.
# Onde/verificar: everytune/storage.py; everytune/app.py; tests/test_engine.py; tests/test_app.py.
#
# 39. upstream_text_is_not_executable_ui — Conteúdo externo é texto, não código.
# Regra: renderize nomes, créditos e mensagens sem interpretar HTML/scripts externos;
# valide URLs e preserve as proteções de navegação, CSP e ausência de referência sensível.
# Por quê: um título ou link fornecido por uma fonte não pode executar código no app local.
# Onde/verificar: everytune/static/; everytune/app.py; tests/test_app.py;
# scripts/browser_smoke.py. Validar payloads maliciosos em teste próprio quando esta área mudar.
#
# 40. async_ui_respects_active_context — Respostas antigas não alteram a busca nova.
# Regra: cada atualização assíncrona deve pertencer à pesquisa/inspeção ativa,
# inclusive último fragmento do stream e erros tardios. Paginar preserva o contexto;
# alternar o foco preserva marcações dos outros grupos e vale para a próxima pesquisa.
# Por quê: rede fora de ordem não pode misturar consultas ou alterar a seleção silenciosamente.
# Onde/verificar: everytune/static/app.js; everytune/static/downloads.js;
# scripts/federation_browser_smoke.py; scripts/providers_download_browser_smoke.py.
# Requisito a validar: não inferir conformidade apenas pela existência de AbortController.
#
# 41. interface_remains_operable — Atualizações preservam operação acessível.
# Regra: mantenha rótulos, navegação por teclado e foco útil ao atualizar resultados,
# fontes e tarefas; diálogos devolvem foco ao fechar. Estados/erros/progresso devem
# ser perceptíveis, sem depender apenas de cor; telas pequenas preservam ações essenciais.
# Por quê: busca e downloads precisam continuar utilizáveis durante atualizações e no celular.
# Onde/verificar: everytune/static/; scripts/audit_ux_layout.py; scripts/audit_ux_followup.py.
# Requisito a validar: auditorias podem encontrar pendências; isto não declara conformidade WCAG.
#
# 42. coverage_and_build_claims_match_evidence — Cobertura anunciada é verificável.
# Regra: diferencie fonte listada, atalho externo, conector instalado e acesso testado;
# uma amostra não comprova o catálogo inteiro. O executável inclui os recursos usados
# pelo app e só anuncia plataforma/funcionalidade validada; não promete busca universal.
# Por quê: quantidade de links e um build local não comprovam integração ou portabilidade.
# Onde/verificar: everytune/app.py; everytune/data/; EveryTune.spec; README.md;
# docs/PROVIDERS_DOWNLOADS.md; scripts/smoke.py; scripts/audit_sources.py.
#
# Como o Codex deve aplicar estas leis
# - Leia as regras das áreas afetadas antes de alterar o projeto.
# - Priorize segurança, credenciais e perda de dados; depois identidade e completude.
# - Use as referências como pontos de partida, não como prova de cobertura existente.
# - Requisitos 1–42: documentados, sem prova formal integral.
# - Regras sobre rede, disco, interface e empacotamento mantêm verificações externas
#   mesmo se a lógica de decisão correspondente ganhar provas Bend.
# - Preserve os requisitos no código Python e verifique os testes pertinentes.
# - Ao integrar Bend, execute `bend guide`, importe a implementação real aqui,
#   converta os requisitos em declarações `law` e prove-os em PROOF.bend.
# - PROOF.bend deve importar LAWS.bend. Execute `bend PROOF.bend` antes de
#   commits que alterem Bend e confira o veredito completo.
# - Só declare uma lei comprovada após verificar sua prova e a integração real.
# - Valide DNS, HTTP, disco e a ponte Python/Bend também com testes de integração.
# - Submeta mudanças de significado destas leis à revisão do responsável pelo projeto;
#   não enfraqueça requisitos para fazer código ou provas passarem.

# Política parcial da interface; não prova DOM, Python ou os requisitos completos.
import Base
import ./ui_policy.bend as UI
import ./ui/home/model.bend as Home
import ./ui/home/workflow.bend as Workflow

law ui_external_has_no_mapping:
  {UI.mapping(0) == 0 : U32}
law ui_external_has_no_post:
  for post: U32
  {UI.post_body(0, post) == 0 : U32}
law ui_external_has_no_auth:
  for auth: U32
  {UI.auth_name(0, auth) == 0 : U32}
law ui_json_get_has_no_body:
  {UI.post_body(1, 0) == 0 : U32}
law ui_html_get_has_no_body:
  {UI.post_body(2, 0) == 0 : U32}
law ui_json_no_key_has_no_name:
  {UI.auth_name(1, 0) == 0 : U32}
law ui_html_no_key_has_no_name:
  {UI.auth_name(2, 0) == 0 : U32}

# Guardas parciais da home, usadas pelo módulo emitido; não provam DOM/rede.
law home_empty_selection_cannot_zip:
  {Home.can_zip(0) == 0 : U32}
law home_catalogue_has_no_file_action:
  for reference: U32
  {Home.file_action(1, reference) == 0 : U32}
law home_preparing_cannot_save:
  {Home.can_save(6) == 0 : U32}
law home_ready_can_save:
  {Home.can_save(7) == 1 : U32}
law home_stale_query_is_rejected:
  {Home.accepts(2, 1) == 0 : U32}

# Política solicitada: só contar resultados com áudio confirmado pelo conector
# via metadados e HEAD. Imagens acompanham esses resultados. ZIP local é apenas
# embalagem dos áudios/imagens selecionados. HEAD não prova codec ou autoria.
law home_unconfirmed_audio_is_hidden:
  {Home.audio_result(0) == 0 : U32}
law home_other_file_is_hidden:
  {Home.allowed_file(0) == 0 : U32}

# Guardas de pré-seleção usadas pelo manifesto; não iniciam transferências.
law home_external_file_is_not_preselected:
  for kind: U32
  for preferred: U32
  for images: U32
  {Workflow.select_file(0, kind, preferred, images) == 0 : U32}
law home_other_file_is_not_preselected:
  for preferred: U32
  for images: U32
  {Workflow.select_file(1, 0, preferred, images) == 0 : U32}
