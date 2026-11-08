# Implementação da home

Base autorizada: HOME_REDESIGN_PLAN_2026-11-06.md. Execução inline, sem alterar contratos de busca e downloads do servidor.

- Bend será fonte da composição estática da home, estilos novos, transições e decisões de apresentação; módulo emitido importado pelo navegador. A ponte DOM/HTTP reutiliza as integrações existentes e mantém HTML semântico, renderização de texto seguro e reconciliação com foco. Não se afirma que o backend Python migrou para Bend.
- Manter markup gerado no pacote evita tela vazia enquanto o módulo carrega; um único build emite HTML/CSS e funções runtime da mesma origem Bend.
- Trocar sidebar por foco + Opções, reduzir histórico, esconder resultados antes da consulta e mover o painel de arquivos para o item. A fila global continua disponível.
- Preservar os requisitos de LAWS.bend; provar guardas puras utilizadas, testar ponte/módulo, Python e navegador. Não atribuir conformidade WCAG integral às provas.

Verificações e limitações serão registradas ao concluir.

## Resultado implementado

- Home inicial de uma coluna: campo dominante, foco Ambas/Streaming/Comunidade, resumo único e Opções recolhidas. Sem slogan, ilustração vazia, sugestões genéricas ou sidebar permanente. Histórico limitado a três entradas na home; dados históricos existentes preservados.
- Composição inicial e CSS autorados em Bend e gerados no build; labels, resumo, fases, aceitação de gerações, ação de arquivo, ZIP e salvar passam pelo módulo Bend realmente importado.
- Créditos/licença em detalhes por resultado. Catálogo sem exportação permanece identificado. Um único painel de arquivos não modal fica no item; seleção é preservada ao fechar e ao visitar a fila global para a mesma referência. A fila global mantém modal próprio, foco e estados.
- Inspeção manual de URL passa à área Adicionar fontes, sem concorrer com o caminho de um resultado.
- Reutilizados os renderizadores/reconciliação e transportes JavaScript existentes, sem reescrever o backend Python. Isso implementa a alternativa com ponte aprovada, não uma aplicação sem JavaScript.
- Revisão estática independente encontrou três problemas corrigidos: catch de busca antiga alterando progresso; polling sem geração; seleção perdida ao voltar da fila global. Guardas de geração usam a implementação Bend emitida. Testes de navegador forçam atraso de respostas para cobrir os dois primeiros e ida/volta da fila para o terceiro.
- A prova `home_stale_query_is_rejected` demonstra um caso concreto da função usada, não quantificação sobre todas as consultas; testes do módulo incluem IDs iguais/diferentes e limites de U32. As outras guardas têm o escopo declarado em LAWS.bend; não comprovam DOM, rede ou sucesso do áudio.

## Evidência de validação

- 181 testes Python, incluindo importação do módulo real e igualdade entre artefatos e fontes Bend emitidas.
- Provas Bend: 12 leis parciais (sete do editor + cinco da home), verificador com `ALL PROOFS CHECK`. Checagem adicional BendTT/Lean continua pendente conforme parecer anterior.
- `scripts/home_browser_smoke.py`: inicial e resultados em 1440/768/390/320, ambos os temas no estado inicial; seleção de fontes/créditos, busca via handlers reais com respostas controladas, arquivos inline, seleção exata do ZIP, fila, foco, disponibilidade de catálogo e corridas assíncronas. Evidências em `artifacts/home-redesign-2026-11-06`.
- `scripts/ux_regression.py`: regressões da auditoria anterior, incluindo restauração/exportação de perfil temporário e acesso ao editor.
- Build concluído em `dist/home/EveryTune.exe`, sem substituir a instância anterior em uso. O novo executável passou por `home_browser_smoke.py` com busca pela interface, seleção de arquivos e respostas atrasadas controladas, sem erros JavaScript registrados.
- `music_download_smoke.py --executable dist/home/EveryTune.exe` voltou a pesquisar metadados reais e preparar/servir o MP3 de Magic Juand (4.573.184 bytes, mesmo SHA-256 da verificação anterior), sem simulação de rede. Isso não comprova disponibilidade de originais de outros artistas.
- Scripts históricos de smoke foram ajustados aos controles recolhidos e novos rótulos; sua sintaxe foi verificada. Não foi repetida a auditoria live de cada provedor, que não mudou nesta implementação.

Não houve teste de usabilidade com participantes nem medição antes/depois de conversão. Não se atribui melhora percentual de desempenho da tarefa ao redesign. Safari, dispositivos físicos e leitores de tela reais não foram validados.
