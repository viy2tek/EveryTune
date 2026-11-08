# Correções da auditoria UX/UI — 06/11/2026

Escopo: os 13 achados de UX_UI_AUDIT_2026-11-06.md, preservando a identidade visual e os contratos de busca e preparação de arquivos.

| Achado | Correção |
|---|---|
| R01 — foco perdido | Reutilização dos cartões inalterados e restauração por identidade nos cartões alterados/reordenados, fontes e identidades. Ações da fila persistem entre atualizações; diálogos devolvem foco à ação correspondente. |
| R02 — fontes a 320 px | Grupos empilhados, títulos flexíveis e remoção da rolagem horizontal da lista. |
| R03 — resultados distantes | Fontes recolhidas no celular, resumo da seleção, filtros recolhíveis e remoção da introdução após pesquisar em telas pequenas. |
| R04 — restauração sem revisão | Diálogo explícito, foco inicial em manter configurações, cancelamento por Escape e exportação opcional antes da confirmação. Não há desfazer automático; a cópia exportada permite reimportação sem credenciais. |
| R05 — status da fila | Região de status estável anuncia transições, sem repetir cada atualização de bytes. |
| R06 — bordas claras | Token próprio para contornos dos controles nos dois temas, sem escurecer divisórias decorativas. |
| R07 — acesso oculto | Estados das fontes permanecem visíveis no celular quando o painel é aberto. |
| R08 — caminho longo por Tab | Atalhos explícitos para resultados e para fontes, sem índices positivos de Tab. |
| R09 — tipografia pequena | Estados, créditos e metadados auxiliares ajustados; ações de grupo ampliadas. |
| R10 — precisão de toque | Ações auxiliares com mais área clicável; rótulo de cada arquivo alterna a seleção. |
| R11 — destino de Gerenciar fontes | Abre Fontes instaladas e foca o controle correspondente. |
| R12 — editor confuso | Política Bend mostra campos de resultados, corpo POST e autenticação somente quando aplicáveis. Trocar opções preserva os valores na edição; o envio normaliza o atalho externo para GET sem autenticação. Parâmetros avançados pertinentes continuam editáveis. |
| R13 — ações genéricas | Nomes acessíveis incluem arquivo, fonte ou identidade, preservando os rótulos visíveis. |

## Integração Bend real

`ui_policy.bend` é compilado para `everytune/static/ui-policy.mjs`, importado diretamente por `preferences.js`. O servidor Python e os demais fluxos continuam na implementação existente. O executável inclui o módulo compilado; o usuário final não precisa instalar Bend ou WSL.

As sete leis `ui_*` em `LAWS.bend` importam essa implementação, e suas provas ficam em `PROOF.bend`. Elas cobrem a ausência de campos incompatíveis: atalhos externos não usam mapeamento, corpo POST ou autenticação; JSON/HTML por GET não usam corpo POST; JSON/HTML sem chave não usam nome de autenticação. Os requisitos 1–42 continuam requisitos em comentários, sem prova formal integral. As cinco regras iniciais foram preservadas.

`scripts/build_ui_policy.py` verifica as provas e emite o módulo antes de `scripts/build.py` empacotar o aplicativo. O teste `tests/test_ui_policy.py` executa o módulo emitido via Node; a regressão de navegador também verifica os efeitos reais no formulário e a definição enviada à API.

Verificador Bend 2.0.40: `ALL PROOFS CHECK`. A checagem adicional `--verdict` não foi concluída: falta o Lean v4.34.0 exigido pelo kernel BendTT neste ambiente. Não se atribui à integração prova de DOM, Python, transporte, disco ou conformidade WCAG.

## Verificação

- 174 testes Python passaram, incluindo o módulo emitido e o MIME JavaScript de `.mjs` no Windows.
- Regressão de navegador em Edge/Windows com dados isolados, larguras 1440/1024/768/600/390/320 e temas claro/escuro. Resultados, manifests e estados de preparação são controlados; não foram baixadas músicas nem usadas contas.
- Executável `dist/EveryTune.exe` recompilado e aprovado pela mesma regressão de navegador, incluindo importação do módulo Bend emitido. A execução final não registrou erros JavaScript nos estados cobertos.
- Fluxos cobertos: atualização e reordenação com foco, navegação direta, estados móveis, campos condicionais, envio de atalho externo, cancelamento/restauração/exportação real do perfil temporário, seleção por rótulo, fila, anúncios e retorno de foco do diálogo.
- Evidências: `artifacts/ux-fixes-2026-11-06/checks.json` e capturas na mesma pasta. Build: `artifacts/ux-fixes-build.log`.

Os testes também detectaram um defeito anterior na revogação de downloads: marcar uma referência com tempo zero não a expirava quando o relógio monotônico tinha menos de duas horas. A invalidação agora remove a referência e seu índice diretamente. O teste existente foi reforçado com relógio baixo, preservando a regra de revogação sem depender do tempo desde a inicialização do Windows.

Limites: não houve teste em Safari, dispositivos físicos ou leitor de tela real. A região de anúncio foi validada no DOM e por transições, não pela saída de um leitor de tela. Não há declaração de conformidade WCAG integral.
