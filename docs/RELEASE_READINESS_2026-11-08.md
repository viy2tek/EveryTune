# Preparação da beta 0.4.0b1

## Verificações locais

- Dependências instaladas em venv nova, a partir de `requirements-dev.txt`.
- Cópia do código contendo somente arquivos previstos para o Git, sem `.git`,
  `.venv`, temporários, executáveis ou dados locais: 201 testes passaram.
- Inicialização e encerramento do servidor a partir dessa cópia: passaram.
- PROOF.bend verificado pelo compilador durante o build; guardas parciais da UI,
  sem prova integral dos requisitos Python/rede/disco e sem rechecagem Lean.
- Executável beta Windows x64: testes de interface passaram, sem erro JavaScript,
  incluindo seleção, ZIP/originais, falhas parciais, cobertura e cancelamento.
- Transferência real do MP3 de referência concluída pelo executável.
- ZIP de distribuição extraído e conferido contra o executável original; inicialização
  passou com PATH restrito ao System32, sem depender de Python/Node/Bend/FFprobe no PATH.
- Pacote inclui licença MIT, guia, alterações e avisos de licença disponíveis das
  dependências e do Python. SHA256SUMS.txt acompanha os arquivos distribuídos.
- Verificação básica de padrões de credenciais nos arquivos destinados ao Git:
  nenhuma correspondência. Isso não constitui auditoria completa de segurança.

## Repositório e documentação

README reescrito para a política atual de áudio/imagens e fontes com acesso real;
versão sincronizada em pyproject.toml e no aplicativo; licença MIT escolhida pelo
responsável. `.gitignore` exclui ambientes, banco, logs, chaves e HTML bruto de
terceiros; `.gitattributes` mantém finais de linha consistentes. Workflow de testes
inclui Python 3.12/3.14 em Windows/Linux, ações oficiais fixadas por commit e acesso
somente de leitura. Seu resultado remoto deve ser consultado no GitHub.

## Limites mantidos

Uma venv nova na mesma máquina não substitui teste em outro computador. Executável
sem assinatura digital; funcionamento de fontes externas e disponibilidade de
artistas continuam variáveis. Nenhum binário Linux/macOS é distribuído nesta beta.
Publicação como pré-release não constitui declaração de estabilidade ou auditoria WCAG.
