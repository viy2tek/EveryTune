# Dados técnicos dos áudios

## Apresentação

- Antes de preparar: bitrate e taxa de amostragem declarados pelo Openverse, quando presentes, são preservados individualmente por opção. Dados de uma versão não são copiados para alternativas. A interface identifica os dados como **informados pela fonte**; campos ausentes permanecem desconhecidos.
- Após preparar um original: ffprobe opcional lê codec, bitrate quando disponível no stream, taxa de amostragem, profundidade em bits quando o formato informa e canais no arquivo local já fechado. A interface identifica **lido no arquivo**.
- Para ZIP criado pelo aplicativo: durante a transferência é guardado no máximo o prefixo de 512 KiB de cada áudio, analisado separadamente e removido. O ZIP não é extraído; os bytes dos arquivos não são alterados. A interface identifica **lido nos cabeçalhos**. Formatos cujo índice fica fora do prefixo podem não ser identificados; não há promessa de análise integral do ZIP ou de bitrate médio calculado sobre todo o áudio.
- Dados declarados e lidos aparecem separados, inclusive quando divergem. Não há conversão, ganho de qualidade, classificação subjetiva, selo de upload oficial ou comprovação de que um formato sem perdas não veio de conversão anterior.
- MP3/AAC não recebem profundidade de bits inferida do formato de amostras do decodificador. Uma saída float de 32 bits do decodificador não vira alegação de “MP3 32 bits”.

## Implementação e limites

`everytune/audio_quality.py` normaliza metadados e executa o ffprobe localizado no PATH. Não instala nem inclui outra distribuição do FFmpeg no executável. Quando não existe ffprobe ou a inspeção falha, a preparação continua e os dados desconhecidos são identificados como tal.

O processo usa argumentos fixos, sem shell; entrada local com demuxer forçado conforme o formato, protocolo somente file, referências externas MOV desativadas, análise limitada, alocação individual limitada e timeout de cinco segundos. Cancelamento/timeout mata e aguarda o processo filho. stderr não é devolvido ao usuário. A leitura de qualidade ocorre somente durante/depois da preparação, sem baixar áudio adicional durante a pesquisa.

`ui/home/quality.bend` concentra os textos e unidades apresentados pela interface, compilados no módulo da home. Backend Python faz a integração local e recebe somente os campos técnicos normalizados; o ffprobe não substitui as validações de download.

A inspeção lê dados técnicos do contêiner/stream. Não certifica integridade completa, master original, ausência de perdas históricas ou qualidade perceptiva. Nem todos os campos se aplicam a todos os formatos. Imagens mantêm formato e tamanho existentes; esta implementação analisa os dados técnicos de áudio.

## Verificação

- Suíte Python: 192 testes passaram. Executável `dist/quality/EveryTune.exe` validado no navegador e em transferência real, com leitura técnica pelo ffprobe instalado.
- Falha de armazenamento temporário dos cabeçalhos não impede gerar o ZIP; os dados técnicos ficam desconhecidos.
- Testes de metadados inválidos, alternativas independentes, profundidade não inventada, ffprobe ausente, timeout e cancelamento.
- Áudio WAV real gerado localmente (PCM 24 bits, 96.000 Hz, estéreo): leitura do original e dos cabeçalhos no ZIP, mantendo bytes idênticos. Nomes com colisão no ZIP mantêm a associação correta com o relatório técnico.
- Testes de interface verificam rótulo da fonte, leitura dos cabeçalhos, seleção e continuidade dos painéis.
- A transferência real de Rockstars usada nas verificações anteriores retornou: codec MP3, 44.100 Hz, dois canais, bitrate de stream reportado de 210.237 bit/s, com o mesmo SHA-256 do arquivo anterior. Esses dados vêm do ffprobe, não de preenchimento dos campos vazios do Openverse.

Referências: [campos de áudio do Openverse](https://docs.openverse.org/meta/media_properties/api.html), [documentação ffprobe](https://www.ffmpeg.org/ffprobe.html).
