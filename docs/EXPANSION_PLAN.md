# Expansão de fontes e créditos

Pedido de 05/11/2026: auditar todos os links de áudio do FMHY, integrar pesquisas
viáveis, encontrar pessoas nos créditos e permitir configuração pelo usuário.
Confirmado pelo usuário: busca, créditos e configurações; sem downloads nesta etapa.

1. Auditoria retomável de todas as URLs, respeitando robots, acesso e tipo de conteúdo.
   Evidência por página, forms GET observados, bloqueios e candidatos; sem confundir
   descoberta automática com adapter validado.
2. Inspeção JUMO read-only: identificar mecanismos de pesquisa públicos, documentar
   limitações e não usar credenciais compartilhadas ou superar restrições.
3. Modos de busca explícitos: preservar faixa/artista exatos e acrescentar pessoa/créditos,
   com papéis e evidência. Homônimos exigem escolha quando a fonte fornece identidades.
4. Fontes do usuário: conectores JSON/HTML públicos e links externos configuráveis,
   mapeamento declarativo, sem execução de código. Credenciais de sessão separadas;
   HTTPS público validado/pinado, limites de resposta e redirects sem repassar segredos.
5. Preferências: tema, grade/lista, país, capas/metadados visíveis, perfis exportáveis
   sem segredos e restauração dos padrões. Sem controles fictícios de qualidade de áudio.
6. Testes de segurança, seleção de pessoas, rejeição de falsos créditos, parsers,
   import/export, interface e pacote Windows. Relatório distingue o que funciona de
   candidatos/bloqueios, sem promessa de cobertura universal.

Entrega 0.2.0: etapas de auditoria, mecanismos de busca, configurações e testes concluídas. Integração universal não foi alcançada: bloqueios e buscas não verificadas estão individualizados em [FREE_WEBSITES.md](FREE_WEBSITES.md). O requisito final exclui cobrança de créditos/tokens, preservando os créditos musicais.

Atualização 0.3.0: 41 conectores adicionais com teste positivo/negativo; modo Resultados da fonte, POST formulário/JSON, feeds pesquisáveis, migração sem reset e validação da ordem contra a interface FreeMIDI. Total específico das seções: 57 conectores; pendências detalhadas no relatório atual.
