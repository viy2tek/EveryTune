# Beta 2: executável direto

Distribuição principal: `EveryTune-v0.4.0-beta.2-windows-x64.exe`.
Não exige extração de ZIP nem instalação de Python, Bend, Node ou WSL.
O ZIP permanece opcional; SHA256SUMS.txt lista ambos os arquivos.

O build reúne os documentos da release e avisos disponíveis das dependências
em HTML escapado, incorporado ao executável por PyInstaller. O invólucro da página,
os estilos e o rodapé são emitidos pelo Bend usado pela interface. Licenças e
instruções ficam acessíveis no rodapé, sem conexão com um servidor externo.
Os textos originais também acompanham o ZIP opcional.

Verificações locais:
- 202 testes Python passaram, incluindo geração do EXE direto/checksums e escape do texto das licenças.
- PROOF.bend passou na checagem do compilador durante o build; as provas continuam parciais e sem rechecagem Lean.
- Testes de navegador no executável passaram, incluindo acesso à página de licenças.
- O EXE publicado pelo empacotador é idêntico ao build verificado.
- Inicialização, arquivos estáticos, licenças e encerramento passaram com PATH
  restrito ao System32, sem ferramentas de desenvolvimento ou FFprobe no PATH.

Isso não certifica funcionamento em outro computador. O executável continua sem
assinatura digital, precisa de internet para consultar fontes e usa dados locais
persistidos fora do binário. FFprobe continua opcional e não distribuído.
