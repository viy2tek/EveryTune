import Base

def preferences() -> String:
  "<fieldset class=\"general-settings\"><legend>Downloads</legend>" ++
  "<label>Formato preferido<select id=\"pref-download-format\"><option value=\"\">Escolher a cada vez</option><option>MP3</option><option>FLAC</option><option>WAV</option><option>M4A</option><option>AAC</option><option>OGG</option><option>OPUS</option><option>AIFF</option><option>ALAC</option><option>APE</option><option>WV</option><option>WMA</option><option>DSF</option><option>DFF</option></select></label>" ++
  "<label>Preparar seleção como<select id=\"pref-download-pack\"><option value=\"zip\">ZIP único</option><option value=\"original\">Arquivos separados</option></select></label>" ++
  "<label><input type=\"checkbox\" id=\"pref-download-images\"/>Marcar imagens junto com o formato preferido</label></fieldset>" ++
  "<p class=\"small muted\">Preferências apenas marcam arquivos para revisão. Nada é baixado automaticamente; formato ausente exige escolha. Não há conversão.</p>"

def coverage() -> String:
  "<section class=\"settings-panel\" id=\"panel-coverage\" hidden><h2>Cobertura de áudio</h2>" ++
  "<p class=\"muted\">Medições locais das buscas com áudio confirmado e das preparações. Uma amostra não comprova o catálogo inteiro, autoria ou identidade da gravação.</p>" ++
  "<p id=\"coverage-summary\" role=\"status\"></p><div class=\"coverage-scroll\" tabindex=\"0\" role=\"region\" aria-label=\"Cobertura por fonte\"><table class=\"coverage-table\"><caption>Consultas e preparações por fonte</caption><thead><tr><th scope=\"col\">Fonte</th><th scope=\"col\">Com áudio / consultas</th><th scope=\"col\">Cache</th><th scope=\"col\">Problemas</th><th scope=\"col\">Preparações prontas / tentativas</th></tr></thead><tbody id=\"coverage-sources\"></tbody></table></div>" ++
  "<div class=\"profile-actions\"><button type=\"button\" class=\"secondary\" id=\"coverage-refresh\">Atualizar medições</button><button type=\"button\" class=\"text-button\" id=\"coverage-clear\">Limpar medições</button></div>" ++
  "<details class=\"coverage-sample\"><summary>Comparar com uma lista de buscas</summary><p class=\"small muted\" id=\"coverage-scope\"></p>" ++
  "<label for=\"coverage-queries\">Uma busca por linha, até 10. Para conferir nomes, use Artista - Faixa.</label><textarea id=\"coverage-queries\" rows=\"5\" maxlength=\"3010\">xxxtentacion\nSoft Pillow Kisses - Stolen Flowers\nMagic Juand - Rockstars (Instrumental) [Produced by Magic Juand]</textarea>" ++
  "<p class=\"small muted\">Usa modo automático e exclui covers identificados. Confirma disponibilidade por metadados e cabeçalhos, sem transferir áudio. Pode usar cache e respeita os limites das fontes. As consultas entram no histórico local existente.</p>" ++
  "<div class=\"profile-actions\"><button type=\"button\" id=\"coverage-run\">Testar lista</button><button type=\"button\" class=\"secondary\" id=\"coverage-cancel\" hidden>Cancelar teste</button></div><p id=\"coverage-status\" role=\"status\"></p><div id=\"coverage-results\"></div></details></section>"

def selection() -> String:
  "<p class=\"small muted\" id=\"download-preference-note\" role=\"status\"></p><div class=\"download-selection\"><span class=\"small\" id=\"download-selection-count\"></span><label>Preparar como<select id=\"download-pack\"><option value=\"zip\">ZIP único</option><option value=\"original\">Arquivos separados</option></select></label><button disabled id=\"download-zip\" type=\"button\">Preparar ZIP selecionado</button></div>"

def select_file(direct: U32, kind: U32, preferred: U32, images: U32) -> U32:
  match direct:
    case 1:
      match kind:
        case 1: preferred
        case 2: images
        case _: 0
    case _: 0

def diagnostic_label(kind: U32) -> String:
  match kind:
    case 1: "nomes ou versões diferentes"
    case 2: "sem áudio confirmado"
    case 3: "falha ao verificar áudio"
    case 4: "verificação de áudio sem concluir no prazo"
    case _: "candidatos não exibidos"

def grouped_note() -> String:
  "Opções agrupadas por metadados iguais; não é uma comparação do som. Cada origem mantém seus arquivos e sua licença."

def css() -> String:
  ".coverage-scroll{max-width:100%;overflow:auto;margin:20px 0}.coverage-table{width:100%;min-width:680px;border-collapse:collapse;font-size:.875rem}.coverage-table caption{text-align:left;padding:8px 0}.coverage-table th,.coverage-table td{text-align:left;padding:12px;border-bottom:1px solid var(--line);vertical-align:top}.coverage-sample{margin-top:24px}.coverage-sample>label{display:block;line-height:1.6}.coverage-sample textarea{display:block;width:100%;margin:12px 0;padding:12px;resize:vertical;font:inherit;line-height:1.6;color:var(--ink);background:var(--surface);border:1px solid var(--line);border-radius:6px}.coverage-case{padding:12px 0;border-bottom:1px solid var(--line)}.coverage-case p{margin:6px 0}.grouped-note{margin:12px 0;font-size:.8125rem;color:var(--muted)}.source-diagnostic{padding:10px 0;border-bottom:1px solid var(--line)}.source-diagnostic p{margin:4px 0}.download-selection label{display:grid;gap:6px;font-size:.875rem}"
