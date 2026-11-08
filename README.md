# EveryTune

Busque músicas em várias fontes e prepare os arquivos disponíveis para download,
a partir de um aplicativo que roda na sua máquina.

**Beta 0.4.0b2 · Windows x64 · interface em português · licença MIT**

O EveryTune inicia um servidor em `127.0.0.1` e abre o navegador. Não precisa de
conta EveryTune nem de hospedagem na internet. As consultas são enviadas às fontes
selecionadas; capas podem ser carregadas dos servidores delas.

## Começar

### Executável Windows

**[Baixar EveryTune.exe](https://github.com/viy2tek/EveryTune/releases/download/v0.4.0-beta.2/EveryTune-v0.4.0-beta.2-windows-x64.exe)**

Baixe o executável para Windows x64 e abra com dois cliques. Não precisa extrair
ZIP nem instalar o aplicativo. Licenças e instruções estão dentro do executável,
acessíveis pelo link **Licenças e instruções** no rodapé. O ZIP é uma alternativa
para quem prefere os avisos em arquivos separados. O código-fonte baixado pelo
botão Code não contém o executável; `dist/` não é versionado.

Não é necessário instalar Python, Bend, Node ou WSL para usar o executável.
Ele mantém uma janela de console. Para encerrar, use **Ajustes → Encerrar EveryTune**
ou Ctrl+C nessa janela. Fechar apenas a aba mantém o servidor ativo.

O executável não tem assinatura digital. A beta foi verificada no ambiente de
desenvolvimento; a execução em outra máquina ainda precisa de validação.

### Executar pelo código

Requer Python **3.12+**. Na pasta do projeto, no Windows/PowerShell:

```powershell
python -m venv .venv
.\.venv\Scripts\python -m pip install -r requirements.txt
.\.venv\Scripts\python -m everytune
```

Linux, para executar o código (sem binário Linux distribuído nesta beta):

```sh
python3 -m venv .venv
.venv/bin/python -m pip install -r requirements.txt
.venv/bin/python -m everytune
```

Para iniciar sem abrir o navegador, acrescente `--no-browser`. `--port 0` escolhe
uma porta livre. O aplicativo imprime a URL real. Os scripts `scripts/run.ps1` e
`scripts/run.sh` também preparam o ambiente e iniciam o app.

## Buscar e baixar

1. Digite um artista ou **Artista - Faixa**. Em **Opções de busca**, escolha fontes,
   modo e exclusão de covers identificados. **Nome completo / artista e faixa**
   confere os nomes; **Resultados da fonte** explora a resposta sem essa conferência.
2. Escolha o foco em **Streaming**, **Comunidade** ou **Ambas**. Só aparecem e são
   contados resultados com áudio confirmado pelo conector, usando metadados e
   cabeçalhos. Uma confirmação não garante que a transferência posterior terá sucesso.
3. Abra **Ver arquivos**. Revise os áudios e imagens, prepare arquivos separados
   ou um ZIP daquela origem e use **Salvar arquivo** quando estiver pronto.
4. Em **Downloads**, acompanhe as preparações. Elas são temporárias; preparar um
   arquivo não significa que o navegador já o salvou.

Em **Ajustes → Preferências → Downloads**, salve formato preferido, pacote e
inclusão de imagens. Isso apenas marca opções para revisão; não inicia downloads
nem substitui silenciosamente um formato ausente. Não há conversão de áudio.

As opções agrupadas preservam origem, licença e versão. Metadados coincidentes
não são prova de que duas gravações têm o mesmo som. Covers sem marcação explícita
não são detectados por análise de áudio, e nome/licença não comprovam upload oficial.

Dados técnicos aparecem como **informados pela fonte** ou **lidos no arquivo**.
FFprobe é opcional, localizado no PATH e não distribuído com o app. Sem ele,
downloads continuam disponíveis. Em ZIP, a leitura técnica é limitada aos cabeçalhos.

## Fontes e limites

A beta inclui **76 conectores de busca e 15 atalhos externos**. Desses conectores,
**66 permitem descoberta de arquivos**; isso não significa que todos devolvam
áudio para uma busca, funcionem sem configuração ou tenham sido testados em todo
o catálogo. Os restantes oferecem catálogo/metadados e não entram na busca com
áudio obrigatório. Atalhos externos também não viram resultados integrados.

- Não há promessa de busca universal ou disponibilidade de um artista específico.
- Região, credenciais, mudanças e limites de cada fonte afetam os resultados.
- **Como foi a busca** explica nomes/versões descartados, falta de áudio confirmado,
  erros, prazo excedido e fontes ignoradas.
- **Ajustes → Cobertura de áudio** mede respostas por fonte e permite testar uma lista
  editável de até dez consultas, sem transferir áudio. As medições são locais;
  amostras e respostas em cache não comprovam todo o catálogo.
- Assinatura de streaming e reprodução offline não são tratadas como exportação
  de áudio. Só são preparados arquivos oferecidos e aceitos pelo conector.
- A seleção aceita somente áudio e imagens. Não inclui documentos, vídeos,
  instaladores, torrents ou arquivos compactados oferecidos por terceiros.
- Não há prévia/player, conversão ou servidor público multiusuário.

Use os arquivos conforme os direitos e termos aplicáveis à origem. A licença MIT
do aplicativo não concede direitos sobre as músicas ou capas encontradas.

## Configuração e dados locais

Preferências, histórico e cache ficam em `%LOCALAPPDATA%\EveryTune` no Windows,
ou `$XDG_DATA_HOME/EveryTune` / `~/.local/share/EveryTune` no Linux.
`EVERYTUNE_DATA_DIR` permite escolher outro diretório.

Credenciais digitadas nos ajustes ficam apenas na sessão. Para reutilizar acesso,
configure as variáveis de ambiente do provedor antes de iniciar:

| Fonte | Variáveis |
|---|---|
| Jamendo | `EVERYTUNE_JAMENDO_CLIENT_ID` |
| SoundCloud | `EVERYTUNE_SOUNDCLOUD_ACCESS_TOKEN` |
| Spotify | `EVERYTUNE_SPOTIFY_CLIENT_ID`, `EVERYTUNE_SPOTIFY_CLIENT_SECRET` |
| Apple Music | `EVERYTUNE_APPLE_DEVELOPER_TOKEN` |
| YouTube | `EVERYTUNE_YOUTUBE_API_KEY` |
| Last.fm | `EVERYTUNE_LASTFM_API_KEY` |

Credenciais de catálogo não habilitam exportação de áudio. Obtenha acesso próprio
pelos canais do provedor. O app não inclui chaves compartilhadas, não carrega
`.env` automaticamente e não exporta segredos no perfil.

Downloads usam temporários com expiração de 30 minutos, duas preparações simultâneas
e limite inicial de 2.048 MB por preparação. A cópia definitiva é salva pelo navegador.
Não exponha o servidor por proxy reverso ou na rede: ele é destinado ao uso pessoal local.

## Desenvolvimento

Veja [CONTRIBUTING.md](CONTRIBUTING.md) para testes, Bend 2 e empacotamento.
A interface usa Bend 2 compilado para módulos JavaScript e HTML/CSS; o servidor e
os conectores são Python. Artefatos compilados já acompanham o código, portanto
Bend não é necessário para executar a versão distribuída.

A API interativa está em `/docs`, na URL local do app. Alterações exigem o cabeçalho
`X-EveryTune: 1`; a API permanece restrita a loopback.

- [Alterações desta beta](CHANGELOG.md)
- [Política de áudio e imagens](docs/AUDIO_ONLY_POLICY_2026-11-07.md)
- [Dados técnicos dos arquivos](docs/AUDIO_QUALITY_2026-11-07.md)
- [Cobertura e fluxo de downloads](docs/WORKFLOW_2026-11-08.md)
- [Busca estrita](docs/PRECISE_SEARCH.md)
- [Inventário de fontes e histórico de pesquisas](docs/SOURCES.md)

Relatórios datados em `docs/` descrevem o estado observado na época; este README
resume o comportamento atual. Conteúdo e disponibilidade das fontes podem mudar.

## Licença

Código original sob [MIT](LICENSE). Consulte [avisos de terceiros](THIRD_PARTY_NOTICES.md)
para dependências, conteúdo externo e inventário de fontes.
