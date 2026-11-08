# EveryTune

Pesquise músicas em várias fontes e baixe os arquivos disponíveis em uma única interface local.

**[Baixar para Windows x64](https://github.com/viy2tek/EveryTune/releases/download/v0.4.0-beta.2/EveryTune-v0.4.0-beta.2-windows-x64.exe)** · [Todas as versões](https://github.com/viy2tek/EveryTune/releases)

## Usar

1. Baixe e abra o `.exe`. A interface abre no navegador, sem instalador ou extração de ZIP.
2. Pesquise um artista ou digite **Artista - Faixa**. Em **Opções de busca**, escolha as fontes e o modo de pesquisa.
3. Abra **Ver arquivos**, selecione os áudios e imagens e prepare arquivos separados ou um ZIP. Quando estiver pronto, clique em **Salvar arquivo**.

Exemplo de busca:

```text
Magic Juand - Rockstars (Instrumental) [Produced by Magic Juand]
```

Em **Ajustes**, salve o formato e o tipo de pacote preferidos. As opções continuam disponíveis para revisão antes de baixar.

Para encerrar, use **Ajustes → Encerrar EveryTune** ou Ctrl+C na janela do aplicativo. Fechar apenas a aba mantém o servidor ativo.

O executável não exige Python, Bend, Node ou WSL. Esta é uma beta sem assinatura digital.

## Fontes e arquivos

- Só entram nos resultados áudios com disponibilidade confirmada pelo conector. Itens apenas de catálogo ficam fora da contagem.
- A busca depende do acesso e dos metadados de cada fonte; não há garantia de encontrar todas as músicas. A disponibilidade pode mudar até o download.
- Algumas fontes exigem credenciais próprias, configuradas em **Ajustes → Fontes instaladas**. **Como foi a busca** mostra falhas e motivos de descarte.

Preferências e histórico do app ficam no seu computador; as consultas são enviadas às fontes selecionadas. É necessário acesso à internet para pesquisar e baixar.

Os dados técnicos dos arquivos dependem das informações disponíveis. A leitura local com FFprobe é opcional e não impede downloads quando ausente. [Detalhes de formatos e qualidade](docs/AUDIO_QUALITY_2026-11-07.md).

## Executar pelo código

Requer Git e **Python 3.12 ou superior**.

**Windows — PowerShell**

```powershell
git clone https://github.com/viy2tek/EveryTune.git
cd EveryTune
python -m venv .venv
.\.venv\Scripts\python -m pip install -r requirements.txt
.\.venv\Scripts\python -m everytune
```

**Linux**

```sh
git clone https://github.com/viy2tek/EveryTune.git
cd EveryTune
python3 -m venv .venv
.venv/bin/python -m pip install -r requirements.txt
.venv/bin/python -m everytune
```

O servidor aceita conexões apenas do próprio computador. Para iniciar sem abrir o navegador, acrescente `--no-browser` ao comando de execução.

Para testes, build e contribuição, veja [CONTRIBUTING.md](CONTRIBUTING.md).

## Licença

Código original sob [MIT](LICENSE). As músicas, imagens e dependências mantêm seus próprios termos; consulte os [avisos de terceiros](THIRD_PARTY_NOTICES.md).
