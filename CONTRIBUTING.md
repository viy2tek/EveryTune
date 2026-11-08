# Desenvolvimento

Use Python 3.12+ e Node disponível no PATH para exercitar os módulos JavaScript
emitidos. Usuários do aplicativo não precisam de Node. Não envie credenciais,
bancos, logs, executáveis locais ou capturas HTML de terceiros ao Git.

## Testes

No Windows, após criar `.venv`:

```powershell
.\.venv\Scripts\python -m pip install -r requirements-dev.txt
.\.venv\Scripts\python -m pip check
.\.venv\Scripts\python -m pytest -q
.\.venv\Scripts\python scripts/smoke.py
```

No Linux, substitua o Python por `.venv/bin/python`. A suíte usa respostas
controladas; alguns testes de qualidade são ignorados se FFprobe não existir.
O workflow de testes executa Python 3.12 e 3.14 em Windows e Linux. Sua primeira
execução remota só acontecerá depois da publicação do repositório.

Para verificar a interface no Edge instalado (Windows):

```powershell
.\.venv\Scripts\python -m pip install playwright
.\.venv\Scripts\python scripts/home_browser_smoke.py
```

Esse teste usa dados isolados. O teste de rede/transferência atual é
`scripts/music_download_smoke.py`; `--coverage` acrescenta três consultas em seis
fontes. Ele depende de internet e da disponibilidade dos provedores. Scripts
antigos de pesquisa em `scripts/` podem depender de evidências locais em
`artifacts/` ou de capturas não publicadas; não são requisitos para executar o app.

## Bend 2 e interface

A home e seus estilos vêm de `ui/home/`, e a política do editor de
`ui_policy.bend`. Edite essas fontes e regenere os artefatos usados pelo navegador:

```powershell
bend guide
.\.venv\Scripts\python scripts/build_ui_policy.py
```

Versão usada: Bend 2.0.40. O build também reconhece o launcher Windows
`%USERPROFILE%\.bend\bin\bend.cmd`, que executa Bend via WSL. Node deve estar no
PATH para emitir o HTML/CSS. Não é necessário instalar Bend para rodar o código
com os artefatos já incluídos.

Leia `LAWS.bend` antes de alterar busca, agrupamento, federação ou downloads.
Os requisitos 1–42 são comentários; as leis formais cobrem somente guardas
parciais da interface. `PROOF.bend` é verificado no build pelo compilador.
`--verdict` exige também o kernel/Lean compatível e não foi validado neste ambiente.
Provas parciais não substituem testes Python, DOM, rede ou disco.

## Executável e pacote

Gere Windows x64 no próprio Windows, em pasta separada do executável aberto:

```powershell
.\.venv\Scripts\python scripts/build.py --distpath dist/beta
.\.venv\Scripts\python scripts/home_browser_smoke.py --executable dist/beta/EveryTune.exe
.\.venv\Scripts\python scripts/music_download_smoke.py --executable dist/beta/EveryTune.exe
.\.venv\Scripts\python scripts/package_release.py --executable dist/beta/EveryTune.exe
```

O pacote fica em `dist/releases/`, com licença do projeto, instruções, avisos
disponíveis das dependências e SHA-256. Ele não inclui credenciais ou dados do
usuário. O script não publica nada no GitHub. Use `docs/RELEASE_NOTES.md` como
texto da pré-release e marque a publicação como beta.

Ao relatar um problema, informe versão, sistema, fonte, consulta de exemplo e
mensagem exibida. Remova tokens, histórico pessoal e outros dados privados de
qualquer arquivo antes de anexá-lo.
