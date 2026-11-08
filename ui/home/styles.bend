import Base

def css() -> String:
  "body.home .quality-details{margin:8px 0 0;padding:0;border:0}body.home .quality-details summary{font-size:.875rem;min-height:36px}body.home .audio-quality{font-size:.875rem;line-height:1.6;overflow-wrap:anywhere}" ++
  "body.home{--home-gap:24px;font-size:16px}" ++
  "body.home main{max-width:1080px;padding:0 24px;margin:auto}" ++
  "body.home .topbar{max-width:1080px;margin:auto;padding:24px;gap:24px}" ++
  "body.home .topbar nav{margin-left:auto;gap:8px}" ++
  "body.home .brand.active{background:none}" ++
  "body.home .nav{font-size:.875rem;min-height:44px}" ++
  "body.home #search-view{padding-top:56px}" ++
  "body.home #search-form h1{font-size:clamp(1.5rem,3vw,2rem);line-height:1.3;margin-bottom:24px;letter-spacing:-.02em}" ++
  "body.home .searchbox{box-shadow:none;border-radius:8px;padding:8px}" ++
  "body.home .searchbox input{font-size:1rem}" ++
  "body.home .searchbox button{padding:14px 24px}" ++
  "body.home .search-toolbar{display:flex;align-items:center;justify-content:space-between;gap:16px;flex-wrap:wrap;margin-top:16px}" ++
  "body.home .provider-scope{display:flex;align-items:center;gap:12px;margin:0;font-size:.875rem}" ++
  "body.home .provider-scope select{width:auto;min-width:150px;font-size:.875rem}" ++
  "body.home .search-context{font-size:.875rem;color:var(--muted);line-height:1.6;margin-top:12px}" ++
  "body.home .search-context #scope-summary{display:inline}" ++
  "body.home .search-foot{margin:8px 0 0;min-height:0}" ++
  "body.home .search-foot:has(#cancel[hidden]){display:none}" ++
  "body.home .workspace{display:block;margin:32px 0 64px}" ++
  "body.home .results-area{width:100%;min-width:0}" ++
  "body.home .results-area>.section-line{margin-bottom:12px}" ++
  "body.home #results-title{font-size:1.125rem}" ++
  "body.home #result-count{font-size:.875rem}" ++
  "body.home #source-controls{padding:24px 0;margin-top:16px;border-top:1px solid var(--line);border-bottom:1px solid var(--line)}" ++
  "body.home .source-controls-body{display:block}" ++
  "body.home .search-options{margin:0 0 16px;gap:24px}" ++
  "body.home .search-options label{font-size:.875rem}" ++
  "body.home .search-options p{font-size:.875rem}" ++
  "body.home .precise-fields{margin:0 0 24px}" ++
  "body.home .precise-fields>p{font-size:.875rem;line-height:1.6;max-width:75ch}" ++
  "body.home .precise-inputs{margin-top:16px}" ++
  "body.home .search-versions{margin:16px 0}" ++
  "body.home #source-list{display:grid;grid-template-columns:repeat(2,minmax(0,1fr));gap:32px;max-height:420px;overflow:auto;padding:8px 6px;scrollbar-gutter:stable}" ++
  "body.home .provider-group{margin:0;min-width:0}" ++
  "body.home .provider-heading{margin-bottom:8px}" ++
  "body.home .source-option{font-size:.875rem;padding:10px 0}" ++
  "body.home .source-option .state{font-size:.75rem}" ++
  "body.home .manage{padding:12px 0;margin-top:12px}" ++
  "body.home .history{margin-top:24px;gap:8px}" ++
  "body.home .history button{font-size:.875rem;padding:8px 12px}" ++
  "body.home.has-search .history{display:none}" ++
  "body.home .skip-link{position:absolute;left:-10000px;top:auto;width:1px;height:1px;overflow:hidden}" ++
  "body.home .skip-link:focus{position:static;width:auto;height:auto;padding:12px;display:inline-block}" ++
  "body.home #filters{margin:8px 0 16px}" ++
  "body.home #filters>summary{font-size:.875rem}" ++
  "body.home .track-group{padding:24px 0}" ++
  "body.home .track-main{align-items:flex-start;gap:16px;flex-wrap:wrap}" ++
  "body.home .track-info{min-width:160px}" ++
  "body.home .track-info h3{font-size:1rem}" ++
  "body.home .track-info p{font-size:.875rem}" ++
  "body.home .cover{width:52px;height:52px}" ++
  "body.home .match{font-size:.75rem;max-width:100%;white-space:normal;line-height:1.5}" ++
  "body.home .origins{margin:12px 0 0 68px;gap:12px}" ++
  "body.home .origin{font-size:.875rem;gap:12px;align-items:center}" ++
  "body.home .source-icon{display:none}" ++
  "body.home .origin small{font-size:.75rem}" ++
  "body.home .origin .text-button{margin-left:auto;min-height:44px;padding:10px 16px;border:1px solid var(--control-border);border-radius:6px;text-align:center}" ++
  "body.home .result-details{margin-top:12px;padding-top:0;border:0}" ++
  "body.home .result-details summary{font-size:.875rem;font-weight:400;min-height:36px}" ++
  "body.home .credit-list{margin-top:8px}" ++
  "body.home .license{margin-top:12px}" ++
  "body.home #download-dialog.inline-downloads{position:static;inset:auto;width:100%;max-width:100%;max-height:none;margin:20px 0 0;padding:24px 0;border:0;border-top:1px solid var(--line);border-radius:0;background:transparent;overflow:visible}" ++
  "body.home #download-dialog.inline-downloads .download-heading{position:static;background:transparent}" ++
  "body.home #download-dialog.inline-downloads #download-options{max-height:none;overflow:visible}" ++
  "body.home #download-dialog.inline-downloads .download-queue{margin-top:16px}" ++
  "body.home #download-dialog.inline-downloads .download-filters{margin-top:16px}" ++
  "body.home #download-dialog.inline-downloads .download-heading h2{font-size:1rem}" ++
  "body.home footer{max-width:1080px;margin:auto;font-size:.75rem;padding:24px}" ++
  "body.home .startup-error{padding:24px;line-height:1.7}" ++
  "body.home .results-grid{gap:24px}" ++
  "body.home .results-grid .origins{margin-left:0}" ++
  "@media(max-width:700px){body.home main{padding:0 20px}" ++
  "body.home .topbar{padding:16px 20px;gap:12px}" ++
  "body.home #search-view{padding-top:28px}" ++
  "body.home #search-form h1{margin-bottom:20px}" ++
  "body.home .searchbox svg{display:none}" ++
  "body.home .searchbox input{padding-left:8px;min-width:0}" ++
  "body.home .searchbox button{padding:12px 16px}" ++
  "body.home .search-toolbar{gap:8px}" ++
  "body.home .provider-scope{gap:8px;font-size:.875rem}" ++
  "body.home .provider-scope select{min-width:0;max-width:160px;font-size:1rem}" ++
  "body.home #options-toggle{font-size:.875rem;padding:8px 0}" ++
  "body.home .search-context{font-size:.75rem}" ++
  "body.home #source-list{grid-template-columns:minmax(0,1fr);gap:24px;max-height:420px}" ++
  "body.home .source-option{display:grid;grid-template-columns:20px minmax(0,1fr);padding:10px}" ++
  "body.home .source-option .state{grid-column:2;text-align:left}" ++
  "body.home .workspace{margin-top:24px}" ++
  "body.home .track-main{gap:12px}" ++
  "body.home .track-info{min-width:140px}" ++
  "body.home .match{flex-basis:100%;text-align:left}" ++
  "body.home .origins{margin-left:0}" ++
  "body.home .origin .text-button{margin-left:0}" ++
  "body.home #download-dialog.inline-downloads{padding-top:20px}" ++
  "body.home .results-grid{grid-template-columns:1fr}" ++
  "body.home .download-selection{gap:12px}" ++
  "body.home .source-controls-body .search-options{display:block}" ++
  "body.home .source-controls-body .search-options label{display:grid}}" ++
  "@media(prefers-reduced-motion:no-preference){body.home .track-group{animation:none}" ++
  "body.home #source-controls{animation:homeReveal .16s ease-out}" ++
  "@keyframes homeReveal{from{opacity:.7;transform:translateY(-3px)}" ++
  "to{opacity:1;transform:none}}}"
