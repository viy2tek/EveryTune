# Direção visual
Modo Operate. Biblioteca de pesquisa musical: fundo claro quente, texto tinta,
verde petróleo e detalhes em laranja queimado. Busca ampla, lista densa porém legível,
status detalhado das fontes dentro de Opções de busca. A tipografia usa fontes locais do sistema para manter o app
independente de conexões para carregar a interface. Ícones SVG simples e monogramas
de fontes. Home de uma coluna em todas as larguras: busca dominante, foco entre grupos
visível, opções avançadas recolhidas e resultados somente após consultar. Arquivos
abrem no contexto do resultado; a fila global permanece em Downloads. Estados e foco explícitos.

Composição e estilos novos da home são autorados em `ui/home/view.bend` e
`ui/home/styles.bend`. O build emite HTML/CSS e `home.mjs`; não editar os artefatos
gerados manualmente. `model.bend` concentra fases e guardas parciais; JavaScript
continua fazendo a ponte DOM/HTTP e reutilizando a reconciliação existente.
