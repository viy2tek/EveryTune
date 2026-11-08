# EveryTune v0.4.0-beta.1

Primeira beta: busca musical local em várias fontes, com resultados que tenham
áudio confirmado pelo conector e preparação de arquivos para salvar pelo navegador.

## Windows x64

Baixe `EveryTune-v0.4.0-beta.1-windows-x64.zip`, extraia e abra `EveryTune.exe`.
Não precisa instalar Python, Bend, Node ou WSL. O arquivo `SHA256SUMS.txt` permite
conferir o pacote. FFprobe é opcional e não acompanha a distribuição.

O servidor escuta em `127.0.0.1`; o navegador abre quando ele estiver pronto.
Para encerrar, use Ajustes → Encerrar EveryTune ou Ctrl+C na janela do aplicativo.
Fechar a aba não encerra o servidor.

## Incluído

- Seleção de fontes e foco entre streaming/comunidade.
- Busca por artista/faixa, exploração de resultados e exclusão de covers identificados.
- Somente áudio confirmado nos resultados; áudio e imagens na seleção de arquivos.
- Arquivos separados ou ZIP por origem; preferências persistidas e seleção revisável.
- Formatos listados e dados técnicos disponíveis, com distinção entre fonte e arquivo.
- Diagnóstico e cobertura local, temas claro/escuro e interface em português.

## Limitações da beta

- Nenhuma promessa de encontrar todos os artistas ou de download em todas as fontes.
- Credenciais, região e mudanças nos serviços afetam o acesso.
- Metadados/HEAD não comprovam upload oficial, identidade acústica ou sucesso da transferência.
- Executável sem assinatura digital; teste em outra máquina ainda pendente.
- Sem prévia, conversão ou exportação de conteúdo offline protegido de streaming.
- Código original MIT; conteúdo e dependências têm seus próprios termos.

O código-fonte pode ser executado com Python 3.12+, conforme o README.
