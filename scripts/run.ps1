param([int]$Port = 8765, [switch]$NoBrowser)
$ErrorActionPreference = 'Stop'
Set-Location -LiteralPath (Split-Path -Parent $PSScriptRoot)
if (-not (Test-Path -LiteralPath '.venv/Scripts/python.exe')) {
    python -m venv .venv
    if ($LASTEXITCODE -ne 0) { throw 'Python 3.12+ deve estar instalado.' }
}
& ./.venv/Scripts/python.exe -m pip install -r requirements.txt
if ($LASTEXITCODE -ne 0) { throw 'Falha na instalação das dependências.' }
$launchArgs = @('-m', 'everytune', '--port', $Port)
if ($NoBrowser) { $launchArgs += '--no-browser' }
& ./.venv/Scripts/python.exe @launchArgs
exit $LASTEXITCODE
