# Viabilidade de Bend 2 para a home

Data: 2026-11-06. Escopo: pesquisa e recomendação; nenhuma implementação da home.

## Conclusão

É viável colocar o estado e as decisões da home em Bend 2, compilados para o navegador, preservando o servidor Python. A evidência consultada **não sustenta prometer uma interface web integralmente escrita em Bend, sem HTML/CSS e sem uma ponte com JavaScript**. Se “toda a implementação em Bend 2” proíbe essa ponte, a restrição permanece sem solução demonstrada e deve ser resolvida antes de implementar.

## Evidências primárias

| Pergunta | Achado e limite | Fonte |
| --- | --- | --- |
| Qual versão está instalada? | O launcher Windows chama `/home/user/.bend/bin/bend` no Ubuntu/WSL. `--help` informa Bend 2.0.40. | Inspeção local de `C:/Users/User/.bend/bin/bend.cmd` e execução em 2026-11-06. |
| Pode gerar código para navegador? | O guia documenta emissão `.mjs` com funções não IO importáveis por JS. Não equivale a um framework DOM. | [Guia oficial, IO e ferramentas](https://github.com/bendlang/bend/blob/main/guide/GUIDE.md). |
| Pode empacotar uma página? | `bend page.html -o dist` é comando real da CLI instalada. A implementação oficial usa `Bun.build`, alvo `browser`, loader HTML e plugin para `.bend`. O ponto de entrada continua sendo HTML. | [CLI oficial, `cli_bundle`](https://github.com/bendlang/bend/blob/main/bend2/main.ts#L542-L627). |
| Pode chamar DOM, eventos e CSS diretamente? | Na listagem instalada `bend base --types` não apareceu API de DOM/HTML/CSS. O mecanismo documentado para efeitos externos são imports JS/C; isso permite construir uma ponte, mas não elimina a implementação externa. Ausência nessa consulta não prova inexistência de todo pacote possível. | Listagem local de Base; [guia oficial, IO](https://github.com/bendlang/bend/blob/main/guide/GUIDE.md#io-and-concurrency). |
| `App.run` resolve uma home web? | Base oferece `App`, `Image`, `Event` e `Window`; são gráficos de imagem, não controles HTML semânticos. `Window.open` importa código externo. | [Base oficial](https://github.com/bendlang/bend/blob/main/bend2/base.bend#L488-L496), listagem local de tipos. |
| A janela gráfica funciona no alvo JS? | O arquivo instalado `effs/window_open.js` devolve erro de ausência de display e solicita compilação nativa. O upstream consultado apresenta o mesmo limite central, embora o arquivo local tenha validações adicionais. Logo `App.run` não é um caminho demonstrado para renderizar a home no navegador. | Arquivo local `/home/user/.bend/bend2/effs/window_open.js`; [implementação oficial](https://github.com/bendlang/bend/blob/main/bend2/effs/window_open.js). |
| Haverá paralelismo GPU no navegador? | O guia informa execução sequencial no alvo JavaScript. Não há motivo para prometer aceleração da home por GPU. | [Guia oficial, paralelismo](https://github.com/bendlang/bend/blob/main/guide/GUIDE.md#parallelism). |

## Evidências no EveryTune

- `ui_policy.bend` já fornece decisões puras compiladas em `everytune/static/ui-policy.mjs`; `preferences.js` importa esse módulo. É precedente de integração, não prova de que a home inteira foi migrada.
- `scripts/build_ui_policy.py` verifica `PROOF.bend` antes de emitir o módulo real. `tests/test_ui_policy.py` exercita o módulo emitido por Node. Esses arquivos foram lidos; os testes não foram executados nesta pesquisa.
- `everytune/app.py` serve `/` a partir de `static/index.html`, registra MIME JavaScript para `.mjs` e mantém CSP com scripts, estilos e conexões na própria origem. A migração não exige trocar o backend nem publicar outro servidor.
- `LAWS.bend` atualmente contém sete leis formais `ui_*` para a política do editor. Os requisitos 1–42 continuam documentados em comentários, sem prova formal integral. Essa cobertura parcial não prova DOM, Python, rede ou acessibilidade.

## Recomendação para o plano

1. Tratar a compatibilidade da restrição de linguagem como decisão anterior à implementação: Bend para toda lógica nova da home, aceitando explicitamente HTML/CSS e um adaptador de navegador, ou pausar a migração literal até existir um caminho verificado sem esse adaptador. Não chamar a primeira alternativa de “100% Bend”.
2. Se a ponte for aceita, manter controles HTML semânticos e CSS responsivo; modelar em Bend o estado da home, as transições, a seleção de modos e as decisões de apresentação. O adaptador recebe eventos, chama o módulo compilado, atualiza DOM com texto seguro e conversa com a API Python existente.
3. Preservar busca, cancelamento, streaming, seleção de fontes e navegação para os painéis existentes. Alterar somente a superfície da home, sem reescrever provedores, armazenamento, downloads, preferências ou launcher. A propriedade de cada evento assíncrono precisa continuar vinculada à busca ativa.
4. Gerar o módulo em build, aproveitando o padrão atual; distribuir o artefato compilado. Usuários finais não precisam de Bend/WSL. Avaliar o bundler HTML apenas se necessário, sem adicionar ferramenta por antecipação.
5. Provar apenas invariantes puros que chamem a implementação Bend realmente importada pela home. Novas leis ou mudanças de significado dependem de revisão do responsável. Antes de qualquer commit Bend, executar `bend PROOF.bend` e exigir o veredito completo; manter testes Python e verificações do navegador para as fronteiras.

## Verificação futura e limites

O primeiro trabalho de implementação deve validar importação do módulo no navegador sob a CSP atual e equivalência dos contratos da home. Depois: testes Python afetados, teste do módulo emitido, busca com respostas atrasadas/cancelamento, teclado/foco, tela pequena e mensagens de estado. Usar dados externos maliciosos para verificar renderização segura, conforme requisitos 39–41.

Não foi criado protótipo, compilado novo módulo, instalado pacote, alterado código do aplicativo ou executada suíte nesta pesquisa. O suporte documental a `.mjs` e bundle HTML está confirmado; o funcionamento de uma nova home Bend ainda exige validação real. Fontes upstream `main` são mutáveis e podem divergir da distribuição instalada.
