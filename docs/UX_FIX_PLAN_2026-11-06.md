# Correções da auditoria UX/UI

Escopo autorizado: R01–R13 de UX_UI_AUDIT_2026-11-06.md. Preservar identidade visual, contratos de busca e downloads e os requisitos de LAWS.bend.

1. app.js: preservar foco por identidade lógica nas listas reconstruídas; adicionar atalhos para resultados/fontes e destino explícito de Gerenciar fontes; nomes contextuais nas ações.
2. index.html e CSS: fontes recolhíveis no celular, filtros recolhíveis, resumo visível; fontes empilhadas sem rolagem horizontal; tipografia, contraste de controles e alvos maiores.
3. preferences.js: revisão explícita antes de restaurar; exportar cópia antes de confirmar; visibilidade condicional do editor com ui_policy.bend compilado para módulo JS. Preservar valores ao alternar e normalizar campos incompatíveis ao enviar.
4. downloads.js: preservar foco nas atualizações, rótulos clicáveis por arquivo, nomes contextuais e anúncio somente de transições de estado.
5. Provas Bend para a política realmente importada pelo editor; testes do módulo emitido e testes Python existentes. Navegador com dados isolados: foco, mobile/desktop, temas, formulário e restauração. Atualizar executável se o empacotamento existente estiver disponível.

Bend não prova DOM, rede, disco, Python ou conformidade WCAG. Os requisitos 1–42 de LAWS.bend continuam comentários; sete leis parciais de UI importam a implementação real e recebem provas em PROOF.bend. Não introduzir Bend no runtime do servidor nem substituir o frontend.
