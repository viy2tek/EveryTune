import Base

def markup() -> String:
  "<section id=\"search-view\"><a class=\"skip-link\" href=\"#results-title\">Ir para resultados</a>\n" ++
  "\n" ++
  "<form id=\"search-form\" role=\"search\"><h1><label for=\"query\">Buscar música ou artista</label></h1>\n" ++
  "\n" ++
  "<div class=\"searchbox\"><svg aria-hidden=\"true\" fill=\"none\" stroke=\"currentColor\" stroke-width=\"1.8\" viewbox=\"0 0 24 24\"><circle cx=\"10.5\" cy=\"10.5\" r=\"6.5\"></circle><path d=\"m16 16 5 5\"></path></svg><input autocomplete=\"off\" id=\"query\" maxlength=\"300\" placeholder=\"Artista ou Artista - Faixa\"/><button id=\"search-button\" type=\"submit\">Buscar</button></div>\n" ++
  "<div class=\"search-foot\"><button hidden=\"\" id=\"cancel\" type=\"button\">Cancelar busca</button></div>\n" ++
  "\n" ++
  "\n" ++
  "<div class=\"search-toolbar\"><label class=\"provider-scope\">Fontes<select id=\"provider-scope\"><option value=\"both\">Ambas</option><option value=\"streaming\">Streaming</option><option value=\"community\">Comunidade</option></select></label><button aria-controls=\"source-controls\" aria-expanded=\"false\" class=\"text-button\" id=\"options-toggle\" type=\"button\">Opções de busca</button></div><p class=\"search-context\"><span id=\"search-summary\"></span> · <span class=\"small muted\" id=\"scope-summary\" role=\"status\"></span></p><section aria-label=\"Opções de busca\" hidden=\"\" id=\"source-controls\"><div class=\"source-controls-body\"><div class=\"search-options\"><label for=\"search-mode\">Pesquisar por<select id=\"search-mode\"><option value=\"source\">Resultados da fonte</option><option value=\"auto\">Nome completo / artista e faixa</option><option value=\"track\">Faixa exata</option><option value=\"credits\">Pessoa e créditos</option></select></label><p id=\"mode-help\" class=\"small muted\"></p></div><div class=\"precise-fields\"><div class=\"precise-name-fields\"><p class=\"muted small\">Campos preenchidos definem a busca e substituem a interpretação do texto acima. Use-os para nomes com hífen ou outra ordem.</p><div class=\"precise-inputs\"><label for=\"search-artist\">Artista exato<input autocomplete=\"off\" id=\"search-artist\" maxlength=\"300\" placeholder=\"Ex.: Soft Pillow Kisses\"/></label><label for=\"search-title\">Título exato da faixa<input autocomplete=\"off\" id=\"search-title\" maxlength=\"300\" placeholder=\"Ex.: Stolen Flowers\"/></label></div></div><div class=\"display-toggles search-versions\"><label><input checked=\"\" id=\"exclude-covers\" type=\"checkbox\"/>Excluir covers identificados</label></div><p class=\"small muted\">Covers são identificados por marcações explícitas nos metadados. Remixes mantêm sua identificação. A autoria de um upload não é comprovada apenas pelo título; uma licença informada também não comprova upload oficial.</p></div>\n" ++
  "<div class=\"section-line\"><h2>Fontes da pesquisa</h2><button class=\"text-button\" id=\"select-all\" type=\"button\">Selecionar todas</button></div>\n" ++
  "<p class=\"muted small\">As fontes disponíveis respondem em paralelo.</p>\n" ++
  "\n" ++
  "<div id=\"source-list\"></div>\n" ++
  "<button class=\"manage\" id=\"manage-sources\" type=\"button\">Gerenciar fontes <span aria-hidden=\"true\">↗</span></button>\n" ++
  "</div></section></form>\n" ++
  "<div aria-label=\"Buscas recentes\" class=\"history\" id=\"history\"></div>\n" ++
  "<div class=\"workspace\">\n" ++
  "\n" ++
  "<section aria-label=\"Resultados da busca\" class=\"results-area\" hidden=\"\">\n" ++
  "<div class=\"section-line\"><h2 id=\"results-title\" tabindex=\"-1\">Resultados</h2><span class=\"muted small\" id=\"result-count\"></span></div>\n" ++
  "<a class=\"skip-link\" href=\"#source-controls\">Ir para fontes</a>\n" ++
  "<p class=\"muted small\" hidden=\"\" id=\"interpretation\" role=\"status\"></p>\n" ++
  "<div hidden=\"\" id=\"progress-area\"><progress aria-label=\"Fontes consultadas\" id=\"progress\" max=\"1\" value=\"0\"></progress><p id=\"progress-label\" role=\"status\"></p></div>\n" ++
  "<p class=\"error\" hidden=\"\" id=\"error\" role=\"alert\"></p>\n" ++
  "<div aria-label=\"Identidades encontradas\" class=\"people\" hidden=\"\" id=\"people\"></div>\n" ++
  "<details class=\"source-notices\" hidden=\"\" id=\"source-notices\"><summary id=\"source-notices-summary\">Detalhes das fontes</summary><div id=\"source-notices-body\"></div></details>\n" ++
  "<details hidden=\"\" id=\"filters\"><summary>Filtrar resultados</summary><div class=\"filters\">\n" ++
  "<label>Plataforma<select id=\"filter-platform\"><option value=\"\">Todas</option></select></label>\n" ++
  "<label>Categoria<select id=\"filter-category\"><option value=\"\">Todas</option></select></label>\n" ++
  "<label>Artista<input id=\"filter-artist\" placeholder=\"Filtrar artista\"/></label>\n" ++
  "<label>Papel nos créditos<select id=\"filter-role\"><option value=\"\">Todos</option></select></label>\n" ++
  "<label>Tipo<select id=\"filter-kind\"><option value=\"\">Todos</option><option value=\"track\">Faixas</option><option value=\"album\">Álbuns / lançamentos</option><option value=\"catalogue_post\">Páginas de catálogo</option><option value=\"work\">Obras</option><option value=\"archive_item\">Acervos</option><option value=\"mix\">Mixes</option></select></label>\n" ++
  "<label>Disponibilidade<select id=\"filter-availability\"><option value=\"\">Áudio disponível</option></select></label>\n" ++
  "</div></details>\n" ++
  "<div id=\"results\"></div>\n" ++
  "<button class=\"secondary\" hidden=\"\" id=\"more\" type=\"button\">Carregar próxima página das fontes</button>\n" ++
  "<details hidden=\"\" id=\"external\"><summary>Continuar a pesquisa em outros catálogos <span id=\"external-count\"></span></summary><p class=\"muted small\">Atalhos para pesquisar nos sites. Não são faixas encontradas pela busca integrada.</p><div id=\"external-links\"></div></details>\n" ++
  "</section>\n" ++
  "</div>\n" ++
  "</section>\n"

def result_label(kind: U32) -> String:
  match kind:
    case 1: "Nomes não conferidos"
    case 2: "Artista e faixa conferidos"
    case 3: "Artista conferido"
    case 4: "Título conferido"
    case 5: "Álbum conferido"
    case 6: "Crédito conferido"
    case 7: "Menção em página"
    case _: "Nomes conferidos"

def cover_summary(covers: U32) -> String:
  match covers:
    case 0: "covers incluídos"
    case _: "covers identificados ocultos"

def summary(mode: U32, covers: U32) -> String:
  match mode:
    case 0: "Áudio para baixar · nomes conferidos · " ++ cover_summary(covers)
    case 1: "Áudio para baixar · faixa exata · " ++ cover_summary(covers)
    case 2: "Áudio para baixar · pessoa e créditos · " ++ cover_summary(covers)
    case _: "Áudio para baixar · nomes não conferidos · " ++ cover_summary(covers)
