# Componentes e conteúdo de terceiros

A licença MIT do EveryTune cobre o código original do projeto. Não concede
direitos sobre músicas, capas, metadados ou marcas dos sites consultados.
Cada resultado preserva sua origem e os termos informados por ela.

O aplicativo usa Python, FastAPI, Uvicorn, HTTPX, Pydantic, Beautiful Soup,
Soup Sieve e suas dependências. O executável Windows é empacotado pelo
PyInstaller. O executável incorpora os avisos de licença disponíveis nas distribuições
instaladas, acessíveis pelo link Licenças e instruções no rodapé. O ZIP opcional
também os inclui dentro de `third-party/`; as licenças desses componentes
continuam aplicáveis. Consulte também os avisos da distribuição Python usada.

A interface contém módulos gerados a partir do código Bend 2 do repositório.
Bend, Node e WSL são ferramentas de desenvolvimento e não são incluídos no
executável. FFprobe é opcional, utilizado somente quando instalado na máquina
do usuário; sua distribuição não integra este pacote.

O inventário de fontes registra links e observações de pesquisa com base no
[FMHY Audio](https://fmhy.net/audio). Uma fonte listada ou um formulário observado
não representa integração testada, disponibilidade de áudio ou licença universal.
Capturas HTML brutas de sites externos são evidências locais e ficam fora do Git.
