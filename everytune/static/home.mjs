function word_to_u32(w) {
  let x = 0;
  for (let i = 0; w.$ === "WCon"; i++) {
    x |= Number(w.head) << i;
    w = w.tail;
  }
  return x >>> 0;
}

function u32_to_word(x) {
  let w = {$: "WNil"};
  for (let i = 31; i >= 0; i--) {
    w = {$: "WCon", head: ((x >>> i) & 1) === 1, tail: w};
  }
  return w;
}

function cmp_new(a, b) {
  return {$: a < b ? "LT" : a === b ? "EQ" : "GT"};
}

function tup_new(a, b) {
  return {$: "Tuple", fst: a, snd: b};
}

function nat_divmod(a, b) {
  return tup_new(b && Math.trunc(a / b), b ? a % b : a);
}

function nat_chk(n) {
  if (n > 281474976710655) {
    throw "bend: a Nat past the largest immediate 2^48-1";
  }
  return n;
}

function nat_in(n) {
  if (!Number.isInteger(n) || n < 0 || n > 2 ** 53) {
    throw "bend: expected a Nat host number: an integer from 0 to 2^53";
  }
  return n;
}

function f32_show(x) {
  let s = "nan";
  for (let p = 1; x === x && p <= 9 && f32_round(s) !== x; p += 1) {
    s = String(Number(x.toExponential(p - 1)));
  }
  return (Object.is(x, -0) ? "-0" : s).replace("Infinity", "inf");
}

function f32_bits(x) {
  return new Uint32Array(new Float32Array([x]).buffer)[0];
}

function f32_from_bits(u) {
  return new Float32Array(new Uint32Array([u]).buffer)[0];
}

function f32_read(s) {
  const re = /^[\t\n\v\f\r ]*[+-]?((\d+(?:\.\d*)?|\.\d+)(e[+-]?\d+)?|inf(inity)?|nan)$/i;
  return re.test(s) ? {$: "Some", value: f32_round(
    s.replace(/inf\w*/i, "Infinity"))} : {$: "None"};
}

const f32_round = function f32_round(s) {
  const d = Number(s);
  const a = Math.abs(d);
  const f = Math.fround(a);
  const g = 2 * a - Math.min(f, 2 ** 128);
  if (g === f || Math.fround(g) !== g || g === Infinity) {
    return Math.sign(d) * f;
  }
  let k = 0;
  while (a * 2 ** k % 1 !== 0) {
    k += 1;
  }
  const [, i, r, e] = /(\d*)\.?(\d*)(?:e([+-]?\d+))?$/i.exec(s);
  const n = Number(e ?? 0) - r.length;
  const x = BigInt(i + r) * 2n ** BigInt(k) * 10n ** BigInt(Math.max(n, 0));
  const y = BigInt(a * 2 ** k) * 10n ** BigInt(Math.max(-n, 0));
  return Math.sign(d) * (x === y || x > y !== g > f ? f : g);
};

const char_new = function char_new(c) {
  return c < 55296 || c >= 57344 && c <= 1114111 ? String.fromCodePoint(c) : String.fromCharCode(56320, c >>> 22, c >>> 11 & 2047, c & 2047);
};

function char_len(s, at = 0) {
  return s[at] === "\uDC00" ? 4 : s.codePointAt(at) > 0xFFFF ? 2 : 1;
}

function char_code(s) {
  return s.length < 4 ? s.codePointAt(0)
    : (s.charCodeAt(1) << 22 | s.charCodeAt(2) << 11 | s.charCodeAt(3)) >>> 0;
}

function string_contains(s, p) {
  // A match starts at a Char, not inside a packed U32 code.
  for (let at = 0; at <= s.length; at += char_len(s, at)) {
    if (s.startsWith(p, at)) {
      return true;
    }
  }
  return false;
}

function str_out(s) {
  return s.replace(/\uDC00[^]{3}/gu, "\uFFFD");
}

function str_in(s) {
  return s.replace(/\p{Cs}/gu, "\uFFFD");
}

// Array
// =====

function array_new(d, v, lgs) {
  if (d > 31 - lgs) {
    throw "bend: an array past the deepest block class 31 (depth + log2 words per cell)";
  }
  return Array(2 ** d).fill(v);
}

function array_node(a, b) {
  if (a.length !== b.length) {
    throw "bend: runtime fail-stop";
  }
  return a.concat(b);
}

function array_rmw(a, i, f) {
  const old = a[i %= a.length];
  a[i] = f(old);
  return tup_new(a, old);
}

// Run
// ===

function run_tail(f, x) {
  return {$: "$JMP", f: f.j?.f === f ? f.j : f, x};
}

function run_clo(j) {
  const f = (x) => run_loop(j(x));
  f.j = j;
  j.f = f;
  return f;
}

function run_loop(r) {
  while (r !== null && typeof r === "object" && r.$ === "$JMP") {
    r = r.f(r.x);
  }
  return r;
}

function run_lib(f, n) {
  return (...a) => a.length < n ? run_lib((...b) => f(...a, ...b), n - a.length)
    : run_loop(f(...a));
}

// Effect
// ======

const $0eff = Object.create(null);
const io_file_append = new Set();

function io_eff(k, run) {
  if (arguments.length > 2) {
    throw new Error("bend: " + k + " takes no need: an effect that waits parks itself");
  }
  if (k in $0eff) {
    throw new Error("bend: two effects register " + k);
  }
  $0eff[k] = run;
}
// Program
// =======

function $model_transition(_current_0, _event_0) {
  if (_event_0 == 0) {
    return 0;
  } else if ((_event_0 & 15) == 0) {
    return _current_0;
  } else if (_event_0 == 8) {
    return 8;
  } else if ((_event_0 & 15) == 8) {
    return _current_0;
  } else if (_event_0 == 4) {
    return 4;
  } else if ((_event_0 & 7) == 4) {
    return _current_0;
  } else if (_event_0 == 2) {
    return 2;
  } else if ((_event_0 & 7) == 2) {
    return _current_0;
  } else if (_event_0 == 6) {
    return 6;
  } else if ((_event_0 & 7) == 6) {
    return _current_0;
  } else if (_event_0 == 1) {
    return 1;
  } else if ((_event_0 & 7) == 1) {
    return _current_0;
  } else if (_event_0 == 5) {
    return 5;
  } else if ((_event_0 & 7) == 5) {
    return _current_0;
  } else if (_event_0 == 3) {
    return 3;
  } else if ((_event_0 & 7) == 3) {
    return _current_0;
  } else if (_event_0 == 7) {
    return 7;
  } else {
    return _current_0;
  }
}

function $model_accepts(_active_0, _received_0) {
  return $Bool_to_u32((_active_0 === _received_0));
}

function $model_can_zip(_count_0) {
  return TAB_0[Math.min(_count_0, 1)];
}

function $model_file_action(_catalogue_0, _reference_0) {
  if (_catalogue_0 == 1) {
    return 0;
  } else {
    return _reference_0;
  }
}

function $model_can_save(_status_0) {
  if (_status_0 == 7) {
    return 1;
  } else {
    return 0;
  }
}

function $model_toggle(_open_0) {
  return TAB_1[Math.min(_open_0, 1)];
}

function $model_audio_result(_available_0) {
  if (_available_0 == 1) {
    return 1;
  } else {
    return 0;
  }
}

function $model_allowed_file(_kind_0) {
  return TAB_2[Math.min(_kind_0, 3)];
}

function $view_markup() {
  const _x_0 = ("</div>\n" + "</section>\n");
  const _x_1 = ("</section>\n" + _x_0);
  const _x_2 = ("<details hidden=\"\" id=\"external\"><summary>Continuar a pesquisa em outros catálogos <span id=\"external-count\"></span></summary><p class=\"muted small\">Atalhos para pesquisar nos sites. Não são faixas encontradas pela busca integrada.</p><div id=\"external-links\"></div></details>\n" + _x_1);
  const _x_3 = ("<button class=\"secondary\" hidden=\"\" id=\"more\" type=\"button\">Carregar próxima página das fontes</button>\n" + _x_2);
  const _x_4 = ("<div id=\"results\"></div>\n" + _x_3);
  const _x_5 = ("</div></details>\n" + _x_4);
  const _x_6 = ("<label>Disponibilidade<select id=\"filter-availability\"><option value=\"\">Áudio disponível</option></select></label>\n" + _x_5);
  const _x_7 = ("<label>Tipo<select id=\"filter-kind\"><option value=\"\">Todos</option><option value=\"track\">Faixas</option><option value=\"album\">Álbuns / lançamentos</option><option value=\"catalogue_post\">Páginas de catálogo</option><option value=\"work\">Obras</option><option value=\"archive_item\">Acervos</option><option value=\"mix\">Mixes</option></select></label>\n" + _x_6);
  const _x_8 = ("<label>Papel nos créditos<select id=\"filter-role\"><option value=\"\">Todos</option></select></label>\n" + _x_7);
  const _x_9 = ("<label>Artista<input id=\"filter-artist\" placeholder=\"Filtrar artista\"/></label>\n" + _x_8);
  const _x_10 = ("<label>Categoria<select id=\"filter-category\"><option value=\"\">Todas</option></select></label>\n" + _x_9);
  const _x_11 = ("<label>Plataforma<select id=\"filter-platform\"><option value=\"\">Todas</option></select></label>\n" + _x_10);
  const _x_12 = ("<details hidden=\"\" id=\"filters\"><summary>Filtrar resultados</summary><div class=\"filters\">\n" + _x_11);
  const _x_13 = ("<details class=\"source-notices\" hidden=\"\" id=\"source-notices\"><summary id=\"source-notices-summary\">Detalhes das fontes</summary><div id=\"source-notices-body\"></div></details>\n" + _x_12);
  const _x_14 = ("<div aria-label=\"Identidades encontradas\" class=\"people\" hidden=\"\" id=\"people\"></div>\n" + _x_13);
  const _x_15 = ("<p class=\"error\" hidden=\"\" id=\"error\" role=\"alert\"></p>\n" + _x_14);
  const _x_16 = ("<div hidden=\"\" id=\"progress-area\"><progress aria-label=\"Fontes consultadas\" id=\"progress\" max=\"1\" value=\"0\"></progress><p id=\"progress-label\" role=\"status\"></p></div>\n" + _x_15);
  const _x_17 = ("<p class=\"muted small\" hidden=\"\" id=\"interpretation\" role=\"status\"></p>\n" + _x_16);
  const _x_18 = ("<a class=\"skip-link\" href=\"#source-controls\">Ir para fontes</a>\n" + _x_17);
  const _x_19 = ("<div class=\"section-line\"><h2 id=\"results-title\" tabindex=\"-1\">Resultados</h2><span class=\"muted small\" id=\"result-count\"></span></div>\n" + _x_18);
  const _x_20 = ("<section aria-label=\"Resultados da busca\" class=\"results-area\" hidden=\"\">\n" + _x_19);
  const _x_21 = ("\n" + _x_20);
  const _x_22 = ("<div class=\"workspace\">\n" + _x_21);
  const _x_23 = ("<div aria-label=\"Buscas recentes\" class=\"history\" id=\"history\"></div>\n" + _x_22);
  const _x_24 = ("</div></section></form>\n" + _x_23);
  const _x_25 = ("<button class=\"manage\" id=\"manage-sources\" type=\"button\">Gerenciar fontes <span aria-hidden=\"true\">↗</span></button>\n" + _x_24);
  const _x_26 = ("<div id=\"source-list\"></div>\n" + _x_25);
  const _x_27 = ("\n" + _x_26);
  const _x_28 = ("<p class=\"muted small\">As fontes disponíveis respondem em paralelo.</p>\n" + _x_27);
  const _x_29 = ("<div class=\"section-line\"><h2>Fontes da pesquisa</h2><button class=\"text-button\" id=\"select-all\" type=\"button\">Selecionar todas</button></div>\n" + _x_28);
  const _x_30 = ("<div class=\"search-toolbar\"><label class=\"provider-scope\">Fontes<select id=\"provider-scope\"><option value=\"both\">Ambas</option><option value=\"streaming\">Streaming</option><option value=\"community\">Comunidade</option></select></label><button aria-controls=\"source-controls\" aria-expanded=\"false\" class=\"text-button\" id=\"options-toggle\" type=\"button\">Opções de busca</button></div><p class=\"search-context\"><span id=\"search-summary\"></span> · <span class=\"small muted\" id=\"scope-summary\" role=\"status\"></span></p><section aria-label=\"Opções de busca\" hidden=\"\" id=\"source-controls\"><div class=\"source-controls-body\"><div class=\"search-options\"><label for=\"search-mode\">Pesquisar por<select id=\"search-mode\"><option value=\"source\">Resultados da fonte</option><option value=\"auto\">Nome completo / artista e faixa</option><option value=\"track\">Faixa exata</option><option value=\"credits\">Pessoa e créditos</option></select></label><p id=\"mode-help\" class=\"small muted\"></p></div><div class=\"precise-fields\"><div class=\"precise-name-fields\"><p class=\"muted small\">Campos preenchidos definem a busca e substituem a interpretação do texto acima. Use-os para nomes com hífen ou outra ordem.</p><div class=\"precise-inputs\"><label for=\"search-artist\">Artista exato<input autocomplete=\"off\" id=\"search-artist\" maxlength=\"300\" placeholder=\"Ex.: Soft Pillow Kisses\"/></label><label for=\"search-title\">Título exato da faixa<input autocomplete=\"off\" id=\"search-title\" maxlength=\"300\" placeholder=\"Ex.: Stolen Flowers\"/></label></div></div><div class=\"display-toggles search-versions\"><label><input checked=\"\" id=\"exclude-covers\" type=\"checkbox\"/>Excluir covers identificados</label></div><p class=\"small muted\">Covers são identificados por marcações explícitas nos metadados. Remixes mantêm sua identificação. A autoria de um upload não é comprovada apenas pelo título; uma licença informada também não comprova upload oficial.</p></div>\n" + _x_29);
  const _x_31 = ("\n" + _x_30);
  const _x_32 = ("\n" + _x_31);
  const _x_33 = ("<div class=\"search-foot\"><button hidden=\"\" id=\"cancel\" type=\"button\">Cancelar busca</button></div>\n" + _x_32);
  const _x_34 = ("<div class=\"searchbox\"><svg aria-hidden=\"true\" fill=\"none\" stroke=\"currentColor\" stroke-width=\"1.8\" viewbox=\"0 0 24 24\"><circle cx=\"10.5\" cy=\"10.5\" r=\"6.5\"></circle><path d=\"m16 16 5 5\"></path></svg><input autocomplete=\"off\" id=\"query\" maxlength=\"300\" placeholder=\"Artista ou Artista - Faixa\"/><button id=\"search-button\" type=\"submit\">Buscar</button></div>\n" + _x_33);
  const _x_35 = ("\n" + _x_34);
  const _x_36 = ("<form id=\"search-form\" role=\"search\"><h1><label for=\"query\">Buscar música ou artista</label></h1>\n" + _x_35);
  const _x_37 = ("\n" + _x_36);
  return ("<section id=\"search-view\"><a class=\"skip-link\" href=\"#results-title\">Ir para resultados</a>\n" + _x_37);
}

function $view_result_label(_kind_0) {
  if (_kind_0 == 1) {
    return "Nomes não conferidos";
  } else if ((_kind_0 & 7) == 1) {
    return "Nomes conferidos";
  } else if (_kind_0 == 5) {
    return "Álbum conferido";
  } else if ((_kind_0 & 7) == 5) {
    return "Nomes conferidos";
  } else if (_kind_0 == 3) {
    return "Artista conferido";
  } else if ((_kind_0 & 7) == 3) {
    return "Nomes conferidos";
  } else if (_kind_0 == 7) {
    return "Menção em página";
  } else if ((_kind_0 & 7) == 7) {
    return "Nomes conferidos";
  } else if (_kind_0 == 2) {
    return "Artista e faixa conferidos";
  } else if ((_kind_0 & 7) == 2) {
    return "Nomes conferidos";
  } else if (_kind_0 == 6) {
    return "Crédito conferido";
  } else if ((_kind_0 & 7) == 6) {
    return "Nomes conferidos";
  } else if (_kind_0 == 4) {
    return "Título conferido";
  } else {
    return "Nomes conferidos";
  }
}

function $view_cover_summary(_covers_0) {
  if (_covers_0 == 0) {
    return "covers incluídos";
  } else {
    return "covers identificados ocultos";
  }
}

function $view_summary(_mode_0, _covers_0) {
  if (_mode_0 == 0) {
    const _x_0 = $$view_cover_summary(_covers_0);
    return ("Áudio para baixar · nomes conferidos · " + _x_0);
  } else if ((_mode_0 & 3) == 0) {
    const _x_1 = $$view_cover_summary(_covers_0);
    return ("Áudio para baixar · nomes não conferidos · " + _x_1);
  } else if (_mode_0 == 2) {
    const _x_2 = $$view_cover_summary(_covers_0);
    return ("Áudio para baixar · pessoa e créditos · " + _x_2);
  } else if ((_mode_0 & 3) == 2) {
    const _x_3 = $$view_cover_summary(_covers_0);
    return ("Áudio para baixar · nomes não conferidos · " + _x_3);
  } else if (_mode_0 == 1) {
    const _x_4 = $$view_cover_summary(_covers_0);
    return ("Áudio para baixar · faixa exata · " + _x_4);
  } else {
    const _x_5 = $$view_cover_summary(_covers_0);
    return ("Áudio para baixar · nomes não conferidos · " + _x_5);
  }
}

function $styles_css() {
  const _x_0 = ("@keyframes homeReveal{from{opacity:.7;transform:translateY(-3px)}" + "to{opacity:1;transform:none}}}");
  const _x_1 = ("body.home #source-controls{animation:homeReveal .16s ease-out}" + _x_0);
  const _x_2 = ("@media(prefers-reduced-motion:no-preference){body.home .track-group{animation:none}" + _x_1);
  const _x_3 = ("body.home .source-controls-body .search-options label{display:grid}}" + _x_2);
  const _x_4 = ("body.home .source-controls-body .search-options{display:block}" + _x_3);
  const _x_5 = ("body.home .download-selection{gap:12px}" + _x_4);
  const _x_6 = ("body.home .results-grid{grid-template-columns:1fr}" + _x_5);
  const _x_7 = ("body.home #download-dialog.inline-downloads{padding-top:20px}" + _x_6);
  const _x_8 = ("body.home .origin .text-button{margin-left:0}" + _x_7);
  const _x_9 = ("body.home .origins{margin-left:0}" + _x_8);
  const _x_10 = ("body.home .match{flex-basis:100%;text-align:left}" + _x_9);
  const _x_11 = ("body.home .track-info{min-width:140px}" + _x_10);
  const _x_12 = ("body.home .track-main{gap:12px}" + _x_11);
  const _x_13 = ("body.home .workspace{margin-top:24px}" + _x_12);
  const _x_14 = ("body.home .source-option .state{grid-column:2;text-align:left}" + _x_13);
  const _x_15 = ("body.home .source-option{display:grid;grid-template-columns:20px minmax(0,1fr);padding:10px}" + _x_14);
  const _x_16 = ("body.home #source-list{grid-template-columns:minmax(0,1fr);gap:24px;max-height:420px}" + _x_15);
  const _x_17 = ("body.home .search-context{font-size:.75rem}" + _x_16);
  const _x_18 = ("body.home #options-toggle{font-size:.875rem;padding:8px 0}" + _x_17);
  const _x_19 = ("body.home .provider-scope select{min-width:0;max-width:160px;font-size:1rem}" + _x_18);
  const _x_20 = ("body.home .provider-scope{gap:8px;font-size:.875rem}" + _x_19);
  const _x_21 = ("body.home .search-toolbar{gap:8px}" + _x_20);
  const _x_22 = ("body.home .searchbox button{padding:12px 16px}" + _x_21);
  const _x_23 = ("body.home .searchbox input{padding-left:8px;min-width:0}" + _x_22);
  const _x_24 = ("body.home .searchbox svg{display:none}" + _x_23);
  const _x_25 = ("body.home #search-form h1{margin-bottom:20px}" + _x_24);
  const _x_26 = ("body.home #search-view{padding-top:28px}" + _x_25);
  const _x_27 = ("body.home .topbar{padding:16px 20px;gap:12px}" + _x_26);
  const _x_28 = ("@media(max-width:700px){body.home main{padding:0 20px}" + _x_27);
  const _x_29 = ("body.home .results-grid .origins{margin-left:0}" + _x_28);
  const _x_30 = ("body.home .results-grid{gap:24px}" + _x_29);
  const _x_31 = ("body.home .startup-error{padding:24px;line-height:1.7}" + _x_30);
  const _x_32 = ("body.home footer{max-width:1080px;margin:auto;font-size:.75rem;padding:24px}" + _x_31);
  const _x_33 = ("body.home #download-dialog.inline-downloads .download-heading h2{font-size:1rem}" + _x_32);
  const _x_34 = ("body.home #download-dialog.inline-downloads .download-filters{margin-top:16px}" + _x_33);
  const _x_35 = ("body.home #download-dialog.inline-downloads .download-queue{margin-top:16px}" + _x_34);
  const _x_36 = ("body.home #download-dialog.inline-downloads #download-options{max-height:none;overflow:visible}" + _x_35);
  const _x_37 = ("body.home #download-dialog.inline-downloads .download-heading{position:static;background:transparent}" + _x_36);
  const _x_38 = ("body.home #download-dialog.inline-downloads{position:static;inset:auto;width:100%;max-width:100%;max-height:none;margin:20px 0 0;padding:24px 0;border:0;border-top:1px solid var(--line);border-radius:0;background:transparent;overflow:visible}" + _x_37);
  const _x_39 = ("body.home .license{margin-top:12px}" + _x_38);
  const _x_40 = ("body.home .credit-list{margin-top:8px}" + _x_39);
  const _x_41 = ("body.home .result-details summary{font-size:.875rem;font-weight:400;min-height:36px}" + _x_40);
  const _x_42 = ("body.home .result-details{margin-top:12px;padding-top:0;border:0}" + _x_41);
  const _x_43 = ("body.home .origin .text-button{margin-left:auto;min-height:44px;padding:10px 16px;border:1px solid var(--control-border);border-radius:6px;text-align:center}" + _x_42);
  const _x_44 = ("body.home .origin small{font-size:.75rem}" + _x_43);
  const _x_45 = ("body.home .source-icon{display:none}" + _x_44);
  const _x_46 = ("body.home .origin{font-size:.875rem;gap:12px;align-items:center}" + _x_45);
  const _x_47 = ("body.home .origins{margin:12px 0 0 68px;gap:12px}" + _x_46);
  const _x_48 = ("body.home .match{font-size:.75rem;max-width:100%;white-space:normal;line-height:1.5}" + _x_47);
  const _x_49 = ("body.home .cover{width:52px;height:52px}" + _x_48);
  const _x_50 = ("body.home .track-info p{font-size:.875rem}" + _x_49);
  const _x_51 = ("body.home .track-info h3{font-size:1rem}" + _x_50);
  const _x_52 = ("body.home .track-info{min-width:160px}" + _x_51);
  const _x_53 = ("body.home .track-main{align-items:flex-start;gap:16px;flex-wrap:wrap}" + _x_52);
  const _x_54 = ("body.home .track-group{padding:24px 0}" + _x_53);
  const _x_55 = ("body.home #filters>summary{font-size:.875rem}" + _x_54);
  const _x_56 = ("body.home #filters{margin:8px 0 16px}" + _x_55);
  const _x_57 = ("body.home .skip-link:focus{position:static;width:auto;height:auto;padding:12px;display:inline-block}" + _x_56);
  const _x_58 = ("body.home .skip-link{position:absolute;left:-10000px;top:auto;width:1px;height:1px;overflow:hidden}" + _x_57);
  const _x_59 = ("body.home.has-search .history{display:none}" + _x_58);
  const _x_60 = ("body.home .history button{font-size:.875rem;padding:8px 12px}" + _x_59);
  const _x_61 = ("body.home .history{margin-top:24px;gap:8px}" + _x_60);
  const _x_62 = ("body.home .manage{padding:12px 0;margin-top:12px}" + _x_61);
  const _x_63 = ("body.home .source-option .state{font-size:.75rem}" + _x_62);
  const _x_64 = ("body.home .source-option{font-size:.875rem;padding:10px 0}" + _x_63);
  const _x_65 = ("body.home .provider-heading{margin-bottom:8px}" + _x_64);
  const _x_66 = ("body.home .provider-group{margin:0;min-width:0}" + _x_65);
  const _x_67 = ("body.home #source-list{display:grid;grid-template-columns:repeat(2,minmax(0,1fr));gap:32px;max-height:420px;overflow:auto;padding:8px 6px;scrollbar-gutter:stable}" + _x_66);
  const _x_68 = ("body.home .search-versions{margin:16px 0}" + _x_67);
  const _x_69 = ("body.home .precise-inputs{margin-top:16px}" + _x_68);
  const _x_70 = ("body.home .precise-fields>p{font-size:.875rem;line-height:1.6;max-width:75ch}" + _x_69);
  const _x_71 = ("body.home .precise-fields{margin:0 0 24px}" + _x_70);
  const _x_72 = ("body.home .search-options p{font-size:.875rem}" + _x_71);
  const _x_73 = ("body.home .search-options label{font-size:.875rem}" + _x_72);
  const _x_74 = ("body.home .search-options{margin:0 0 16px;gap:24px}" + _x_73);
  const _x_75 = ("body.home .source-controls-body{display:block}" + _x_74);
  const _x_76 = ("body.home #source-controls{padding:24px 0;margin-top:16px;border-top:1px solid var(--line);border-bottom:1px solid var(--line)}" + _x_75);
  const _x_77 = ("body.home #result-count{font-size:.875rem}" + _x_76);
  const _x_78 = ("body.home #results-title{font-size:1.125rem}" + _x_77);
  const _x_79 = ("body.home .results-area>.section-line{margin-bottom:12px}" + _x_78);
  const _x_80 = ("body.home .results-area{width:100%;min-width:0}" + _x_79);
  const _x_81 = ("body.home .workspace{display:block;margin:32px 0 64px}" + _x_80);
  const _x_82 = ("body.home .search-foot:has(#cancel[hidden]){display:none}" + _x_81);
  const _x_83 = ("body.home .search-foot{margin:8px 0 0;min-height:0}" + _x_82);
  const _x_84 = ("body.home .search-context #scope-summary{display:inline}" + _x_83);
  const _x_85 = ("body.home .search-context{font-size:.875rem;color:var(--muted);line-height:1.6;margin-top:12px}" + _x_84);
  const _x_86 = ("body.home .provider-scope select{width:auto;min-width:150px;font-size:.875rem}" + _x_85);
  const _x_87 = ("body.home .provider-scope{display:flex;align-items:center;gap:12px;margin:0;font-size:.875rem}" + _x_86);
  const _x_88 = ("body.home .search-toolbar{display:flex;align-items:center;justify-content:space-between;gap:16px;flex-wrap:wrap;margin-top:16px}" + _x_87);
  const _x_89 = ("body.home .searchbox button{padding:14px 24px}" + _x_88);
  const _x_90 = ("body.home .searchbox input{font-size:1rem}" + _x_89);
  const _x_91 = ("body.home .searchbox{box-shadow:none;border-radius:8px;padding:8px}" + _x_90);
  const _x_92 = ("body.home #search-form h1{font-size:clamp(1.5rem,3vw,2rem);line-height:1.3;margin-bottom:24px;letter-spacing:-.02em}" + _x_91);
  const _x_93 = ("body.home #search-view{padding-top:56px}" + _x_92);
  const _x_94 = ("body.home .nav{font-size:.875rem;min-height:44px}" + _x_93);
  const _x_95 = ("body.home .brand.active{background:none}" + _x_94);
  const _x_96 = ("body.home .topbar nav{margin-left:auto;gap:8px}" + _x_95);
  const _x_97 = ("body.home .topbar{max-width:1080px;margin:auto;padding:24px;gap:24px}" + _x_96);
  const _x_98 = ("body.home main{max-width:1080px;padding:0 24px;margin:auto}" + _x_97);
  const _x_99 = ("body.home{--home-gap:24px;font-size:16px}" + _x_98);
  return ("body.home .quality-details{margin:8px 0 0;padding:0;border:0}body.home .quality-details summary{font-size:.875rem;min-height:36px}body.home .audio-quality{font-size:.875rem;line-height:1.6;overflow-wrap:anywhere}" + _x_99);
}

function $quality_codec(_value_0) {
  if (_value_0 === "") {
    return "";
  } else {
    const _h_0 = _value_0.slice(0, char_len(_value_0));
    const _t_0 = _value_0.slice(char_len(_value_0));
    const _x_0 = (_h_0 + _t_0);
    return (_x_0 + " · ");
  }
}

function $quality_bitrate_value(_value_0, _remainder_0) {
  if (_remainder_0 == 0) {
    const _x_0 = $$U32_show((1000 === 0 ? 0 : (_value_0 / 1000) >>> 0));
    return (_x_0 + " kbps · ");
  } else {
    const _x_1 = $$U32_show(_value_0);
    return (_x_1 + " bit/s · ");
  }
}

function $quality_bitrate(_value_0) {
  if (_value_0 == 0) {
    return "";
  } else {
    return $quality_bitrate_value(_value_0, (1000 === 0 ? _value_0 : _value_0 % 1000));
  }
}

function $quality_sample_rate(_value_0) {
  if (_value_0 == 0) {
    return "";
  } else {
    const _x_0 = $$U32_show(_value_0);
    return (_x_0 + " Hz · ");
  }
}

function $quality_depth(_value_0) {
  if (_value_0 == 0) {
    return "";
  } else {
    const _x_0 = $$U32_show(_value_0);
    return (_x_0 + " bits · ");
  }
}

function $quality_channels(_value_0) {
  if (_value_0 == 0) {
    return "";
  } else if ((_value_0 & 3) == 0) {
    const _x_0 = $$U32_show(_value_0);
    return (_x_0 + " canais · ");
  } else if (_value_0 == 2) {
    return "estéreo · ";
  } else if ((_value_0 & 3) == 2) {
    const _x_1 = $$U32_show(_value_0);
    return (_x_1 + " canais · ");
  } else if (_value_0 == 1) {
    return "mono · ";
  } else {
    const _x_2 = $$U32_show(_value_0);
    return (_x_2 + " canais · ");
  }
}

function $quality_basis(_value_0) {
  if (_value_0 == 1) {
    return "lido no arquivo";
  } else if ((_value_0 & 1) == 1) {
    return "informado pela fonte";
  } else if (_value_0 == 2) {
    return "lido nos cabeçalhos";
  } else {
    return "informado pela fonte";
  }
}

function $quality_label(_c_0, _b_0, _s_0, _d_0, _n_0, _origin_0) {
  const _x_0 = $$quality_channels(_n_0);
  const _x_1 = $$quality_basis(_origin_0);
  const _x_2 = $$quality_depth(_d_0);
  const _x_3 = (_x_0 + _x_1);
  const _x_4 = $$quality_sample_rate(_s_0);
  const _x_5 = (_x_2 + _x_3);
  const _x_6 = $$quality_bitrate(_b_0);
  const _x_7 = (_x_4 + _x_5);
  const _x_8 = $$quality_codec(_c_0);
  const _x_9 = (_x_6 + _x_7);
  return (_x_8 + _x_9);
}

function $quality_unknown() {
  return "Dados técnicos não identificados";
}

function $workflow_preferences() {
  const _x_0 = ("<label><input type=\"checkbox\" id=\"pref-download-images\"/>Marcar imagens junto com o formato preferido</label></fieldset>" + "<p class=\"small muted\">Preferências apenas marcam arquivos para revisão. Nada é baixado automaticamente; formato ausente exige escolha. Não há conversão.</p>");
  const _x_1 = ("<label>Preparar seleção como<select id=\"pref-download-pack\"><option value=\"zip\">ZIP único</option><option value=\"original\">Arquivos separados</option></select></label>" + _x_0);
  const _x_2 = ("<label>Formato preferido<select id=\"pref-download-format\"><option value=\"\">Escolher a cada vez</option><option>MP3</option><option>FLAC</option><option>WAV</option><option>M4A</option><option>AAC</option><option>OGG</option><option>OPUS</option><option>AIFF</option><option>ALAC</option><option>APE</option><option>WV</option><option>WMA</option><option>DSF</option><option>DFF</option></select></label>" + _x_1);
  return ("<fieldset class=\"general-settings\"><legend>Downloads</legend>" + _x_2);
}

function $workflow_coverage() {
  const _x_0 = ("<p class=\"small muted\">Usa modo automático e exclui covers identificados. Confirma disponibilidade por metadados e cabeçalhos, sem transferir áudio. Pode usar cache e respeita os limites das fontes. As consultas entram no histórico local existente.</p>" + "<div class=\"profile-actions\"><button type=\"button\" id=\"coverage-run\">Testar lista</button><button type=\"button\" class=\"secondary\" id=\"coverage-cancel\" hidden>Cancelar teste</button></div><p id=\"coverage-status\" role=\"status\"></p><div id=\"coverage-results\"></div></details></section>");
  const _x_1 = ("<label for=\"coverage-queries\">Uma busca por linha, até 10. Para conferir nomes, use Artista - Faixa.</label><textarea id=\"coverage-queries\" rows=\"5\" maxlength=\"3010\">xxxtentacion\nSoft Pillow Kisses - Stolen Flowers\nMagic Juand - Rockstars (Instrumental) [Produced by Magic Juand]</textarea>" + _x_0);
  const _x_2 = ("<details class=\"coverage-sample\"><summary>Comparar com uma lista de buscas</summary><p class=\"small muted\" id=\"coverage-scope\"></p>" + _x_1);
  const _x_3 = ("<div class=\"profile-actions\"><button type=\"button\" class=\"secondary\" id=\"coverage-refresh\">Atualizar medições</button><button type=\"button\" class=\"text-button\" id=\"coverage-clear\">Limpar medições</button></div>" + _x_2);
  const _x_4 = ("<p id=\"coverage-summary\" role=\"status\"></p><div class=\"coverage-scroll\" tabindex=\"0\" role=\"region\" aria-label=\"Cobertura por fonte\"><table class=\"coverage-table\"><caption>Consultas e preparações por fonte</caption><thead><tr><th scope=\"col\">Fonte</th><th scope=\"col\">Com áudio / consultas</th><th scope=\"col\">Cache</th><th scope=\"col\">Problemas</th><th scope=\"col\">Preparações prontas / tentativas</th></tr></thead><tbody id=\"coverage-sources\"></tbody></table></div>" + _x_3);
  const _x_5 = ("<p class=\"muted\">Medições locais das buscas com áudio confirmado e das preparações. Uma amostra não comprova o catálogo inteiro, autoria ou identidade da gravação.</p>" + _x_4);
  return ("<section class=\"settings-panel\" id=\"panel-coverage\" hidden><h2>Cobertura de áudio</h2>" + _x_5);
}

function $workflow_selection() {
  return "<p class=\"small muted\" id=\"download-preference-note\" role=\"status\"></p><div class=\"download-selection\"><span class=\"small\" id=\"download-selection-count\"></span><label>Preparar como<select id=\"download-pack\"><option value=\"zip\">ZIP único</option><option value=\"original\">Arquivos separados</option></select></label><button disabled id=\"download-zip\" type=\"button\">Preparar ZIP selecionado</button></div>";
}

function $workflow_select_file(_direct_0, _kind_0, _preferred_0, _images_0) {
  if (_direct_0 == 1) {
    if (_kind_0 == 1) {
      return _preferred_0;
    } else if ((_kind_0 & 1) == 1) {
      return 0;
    } else if (_kind_0 == 2) {
      return _images_0;
    } else {
      return 0;
    }
  } else {
    return 0;
  }
}

function $workflow_diagnostic_label(_kind_0) {
  if (_kind_0 == 1) {
    return "nomes ou versões diferentes";
  } else if ((_kind_0 & 3) == 1) {
    return "candidatos não exibidos";
  } else if (_kind_0 == 3) {
    return "falha ao verificar áudio";
  } else if ((_kind_0 & 3) == 3) {
    return "candidatos não exibidos";
  } else if (_kind_0 == 2) {
    return "sem áudio confirmado";
  } else if ((_kind_0 & 3) == 2) {
    return "candidatos não exibidos";
  } else if (_kind_0 == 4) {
    return "verificação de áudio sem concluir no prazo";
  } else {
    return "candidatos não exibidos";
  }
}

function $workflow_grouped_note() {
  return "Opções agrupadas por metadados iguais; não é uma comparação do som. Cada origem mantém seus arquivos e sua licença.";
}

function $workflow_css() {
  return ".coverage-scroll{max-width:100%;overflow:auto;margin:20px 0}.coverage-table{width:100%;min-width:680px;border-collapse:collapse;font-size:.875rem}.coverage-table caption{text-align:left;padding:8px 0}.coverage-table th,.coverage-table td{text-align:left;padding:12px;border-bottom:1px solid var(--line);vertical-align:top}.coverage-sample{margin-top:24px}.coverage-sample>label{display:block;line-height:1.6}.coverage-sample textarea{display:block;width:100%;margin:12px 0;padding:12px;resize:vertical;font:inherit;line-height:1.6;color:var(--ink);background:var(--surface);border:1px solid var(--line);border-radius:6px}.coverage-case{padding:12px 0;border-bottom:1px solid var(--line)}.coverage-case p{margin:6px 0}.grouped-note{margin:12px 0;font-size:.8125rem;color:var(--muted)}.source-diagnostic{padding:10px 0;border-bottom:1px solid var(--line)}.source-diagnostic p{margin:4px 0}.download-selection label{display:grid;gap:6px;font-size:.875rem}";
}

function $transition(_current_0, _event_0) {
  return $model_transition(_current_0, _event_0);
}

function $accepts(_active_0, _received_0) {
  return $model_accepts(_active_0, _received_0);
}

function $can_zip(_count_0) {
  return $model_can_zip(_count_0);
}

function $file_action(_catalogue_0, _reference_0) {
  return $model_file_action(_catalogue_0, _reference_0);
}

function $can_save(_status_0) {
  return $model_can_save(_status_0);
}

function $toggle(_open_0) {
  return $model_toggle(_open_0);
}

function $audio_result(_available_0) {
  return $model_audio_result(_available_0);
}

function $allowed_file(_kind_0) {
  return $model_allowed_file(_kind_0);
}

function $markup() {
  return $view_markup();
}

function $css() {
  const _x_0 = $$styles_css();
  const _x_1 = $$workflow_css();
  return (_x_0 + _x_1);
}

function $result_label(_kind_0) {
  return $view_result_label(_kind_0);
}

function $summary(_mode_0, _covers_0) {
  return $view_summary(_mode_0, _covers_0);
}

function $quality(_c_0, _b_0, _s_0, _d_0, _n_0, _origin_0) {
  return $quality_label(_c_0, _b_0, _s_0, _d_0, _n_0, _origin_0);
}

function $quality_unknown_1() {
  return $quality_unknown();
}

function $download_preferences_markup() {
  return $workflow_preferences();
}

function $coverage_markup() {
  return $workflow_coverage();
}

function $selection_markup() {
  return $workflow_selection();
}

function $select_file(_kind_0, _direct_0, _preferred_0, _images_0) {
  return $workflow_select_file(_direct_0, _kind_0, _preferred_0, _images_0);
}

function $diagnostic_label(_kind_0) {
  return $workflow_diagnostic_label(_kind_0);
}

function $grouped_note() {
  return $workflow_grouped_note();
}

function $Bool_to_u32(_b_0) {
  if (!_b_0) {
    return 0;
  } else {
    return 1;
  }
}

function $U32_show(_a_0) {
  const _b_0 = _a_0;
  return $U32_show_if(_b_0, (_b_0 === 0));
}

function $U32_show_if(_a_0, _z_0) {
  if (_z_0) {
    return "0";
  } else {
    return $U32_show_go(10, _a_0, "");
  }
}

function $U32_show_go($0, $1, $2, $3) {
  let $pc = 0;
  for (;;) switch ($pc) {
    case 0: {
      const _f_0 = $0;
      const _n_0 = $1;
      const _acc_0 = $2;
      if (_f_0 == 0) {
        return _acc_0;
      } else {
        const _g_0 = (_f_0 - 1);
        $0 = _g_0;
        $1 = _acc_0;
        $2 = _n_0;
        $3 = (_n_0 === 0);
        $pc = 1; continue;
      }
    }
    case 1: {
      const _g_0 = $0;
      const _acc_0 = $1;
      const _n_0 = $2;
      const _z_0 = $3;
      if (_z_0) {
        return _acc_0;
      } else {
        const _x_0 = (10 === 0 ? _n_0 : _n_0 % 10);
        $0 = _g_0;
        $1 = (10 === 0 ? 0 : (_n_0 / 10) >>> 0);
        $2 = (char_new(((48 + _x_0) >>> 0)) + _acc_0);
        $pc = 0; continue;
      }
    }
  }
}

function $U32_show_fin($0, $1, $2, $3) {
  let $pc = 1;
  for (;;) switch ($pc) {
    case 0: {
      const _f_0 = $0;
      const _n_0 = $1;
      const _acc_0 = $2;
      if (_f_0 == 0) {
        return _acc_0;
      } else {
        const _g_0 = (_f_0 - 1);
        $0 = _g_0;
        $1 = _acc_0;
        $2 = _n_0;
        $3 = (_n_0 === 0);
        $pc = 1; continue;
      }
    }
    case 1: {
      const _g_0 = $0;
      const _acc_0 = $1;
      const _n_0 = $2;
      const _z_0 = $3;
      if (_z_0) {
        return _acc_0;
      } else {
        const _x_0 = (10 === 0 ? _n_0 : _n_0 % 10);
        $0 = _g_0;
        $1 = (10 === 0 ? 0 : (_n_0 / 10) >>> 0);
        $2 = (char_new(((48 + _x_0) >>> 0)) + _acc_0);
        $pc = 0; continue;
      }
    }
  }
}

const $$view_cover_summary = $view_cover_summary;
const $$U32_show = $U32_show;
const $$quality_codec = $quality_codec;
const $$quality_bitrate = $quality_bitrate;
const $$quality_sample_rate = $quality_sample_rate;
const $$quality_depth = $quality_depth;
const $$quality_channels = $quality_channels;
const $$quality_basis = $quality_basis;
const $$styles_css = $styles_css;
const $$workflow_css = $workflow_css;
const TAB_0 = [0, 1];
const TAB_1 = [1, 0];
const TAB_2 = [0, 1, 1, 0];export default {
  "model:transition": run_lib((a0,a1) => run_loop($model_transition(a0,a1)), 2),
  "model:accepts": run_lib((a0,a1) => run_loop($model_accepts(a0,a1)), 2),
  "model:can_zip": run_lib((a0) => run_loop($model_can_zip(a0)), 1),
  "model:file_action": run_lib((a0,a1) => run_loop($model_file_action(a0,a1)), 2),
  "model:can_save": run_lib((a0) => run_loop($model_can_save(a0)), 1),
  "model:toggle": run_lib((a0) => run_loop($model_toggle(a0)), 1),
  "model:audio_result": run_lib((a0) => run_loop($model_audio_result(a0)), 1),
  "model:allowed_file": run_lib((a0) => run_loop($model_allowed_file(a0)), 1),
  "view:markup": run_lib(() => str_out(run_loop($view_markup())), 0),
  "view:result_label": run_lib((a0) => str_out(run_loop($view_result_label(a0))), 1),
  "view:cover_summary": run_lib((a0) => str_out(run_loop($view_cover_summary(a0))), 1),
  "view:summary": run_lib((a0,a1) => str_out(run_loop($view_summary(a0,a1))), 2),
  "styles:css": run_lib(() => str_out(run_loop($styles_css())), 0),
  "quality:codec": run_lib((a0) => str_out(run_loop($quality_codec(str_in(a0)))), 1),
  "quality:bitrate_value": run_lib((a0,a1) => str_out(run_loop($quality_bitrate_value(a0,a1))), 2),
  "quality:bitrate": run_lib((a0) => str_out(run_loop($quality_bitrate(a0))), 1),
  "quality:sample_rate": run_lib((a0) => str_out(run_loop($quality_sample_rate(a0))), 1),
  "quality:depth": run_lib((a0) => str_out(run_loop($quality_depth(a0))), 1),
  "quality:channels": run_lib((a0) => str_out(run_loop($quality_channels(a0))), 1),
  "quality:basis": run_lib((a0) => str_out(run_loop($quality_basis(a0))), 1),
  "quality:label": run_lib((a0,a1,a2,a3,a4,a5) => str_out(run_loop($quality_label(str_in(a0),a1,a2,a3,a4,a5))), 6),
  "quality:unknown": run_lib(() => str_out(run_loop($quality_unknown())), 0),
  "workflow:preferences": run_lib(() => str_out(run_loop($workflow_preferences())), 0),
  "workflow:coverage": run_lib(() => str_out(run_loop($workflow_coverage())), 0),
  "workflow:selection": run_lib(() => str_out(run_loop($workflow_selection())), 0),
  "workflow:select_file": run_lib((a0,a1,a2,a3) => run_loop($workflow_select_file(a0,a1,a2,a3)), 4),
  "workflow:diagnostic_label": run_lib((a0) => str_out(run_loop($workflow_diagnostic_label(a0))), 1),
  "workflow:grouped_note": run_lib(() => str_out(run_loop($workflow_grouped_note())), 0),
  "workflow:css": run_lib(() => str_out(run_loop($workflow_css())), 0),
  "transition": run_lib((a0,a1) => run_loop($transition(a0,a1)), 2),
  "accepts": run_lib((a0,a1) => run_loop($accepts(a0,a1)), 2),
  "can_zip": run_lib((a0) => run_loop($can_zip(a0)), 1),
  "file_action": run_lib((a0,a1) => run_loop($file_action(a0,a1)), 2),
  "can_save": run_lib((a0) => run_loop($can_save(a0)), 1),
  "toggle": run_lib((a0) => run_loop($toggle(a0)), 1),
  "audio_result": run_lib((a0) => run_loop($audio_result(a0)), 1),
  "allowed_file": run_lib((a0) => run_loop($allowed_file(a0)), 1),
  "markup": run_lib(() => str_out(run_loop($markup())), 0),
  "css": run_lib(() => str_out(run_loop($css())), 0),
  "result_label": run_lib((a0) => str_out(run_loop($result_label(a0))), 1),
  "summary": run_lib((a0,a1) => str_out(run_loop($summary(a0,a1))), 2),
  "quality": run_lib((a0,a1,a2,a3,a4,a5) => str_out(run_loop($quality(str_in(a0),a1,a2,a3,a4,a5))), 6),
  "quality_unknown": run_lib(() => str_out(run_loop($quality_unknown_1())), 0),
  "download_preferences_markup": run_lib(() => str_out(run_loop($download_preferences_markup())), 0),
  "coverage_markup": run_lib(() => str_out(run_loop($coverage_markup())), 0),
  "selection_markup": run_lib(() => str_out(run_loop($selection_markup())), 0),
  "select_file": run_lib((a0,a1,a2,a3) => run_loop($select_file(a0,a1,a2,a3)), 4),
  "diagnostic_label": run_lib((a0) => str_out(run_loop($diagnostic_label(a0))), 1),
  "grouped_note": run_lib(() => str_out(run_loop($grouped_note())), 0),
};
