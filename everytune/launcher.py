import argparse
import logging
from logging.handlers import RotatingFileHandler
import socket
import threading
import time
import urllib.request
import webbrowser

import uvicorn

from .app import create_app
from .storage import data_directory


def reserve_port(port: int) -> socket.socket:
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    try:
        sock.bind(("127.0.0.1", port))
    except OSError:
        sock.bind(("127.0.0.1", 0))
    sock.listen(128)
    return sock


def main():
    parser = argparse.ArgumentParser(description="EveryTune — busca musical local")
    parser.add_argument("--port", type=int, default=8765)
    parser.add_argument("--no-browser", action="store_true")
    args = parser.parse_args()
    if not 0 <= args.port <= 65535:
        parser.error("A porta deve estar entre 0 e 65535")
    directory = data_directory()
    directory.mkdir(parents=True, exist_ok=True)
    logger = logging.getLogger("everytune")
    logger.setLevel(logging.DEBUG)
    handler = RotatingFileHandler(directory / "everytune.log", maxBytes=1_000_000, backupCount=2, encoding="utf-8")
    handler.setFormatter(logging.Formatter("%(asctime)s %(levelname)s %(message)s"))
    logger.addHandler(handler)
    # Never enable HTTPX debug logs: they can contain authentication URLs.
    logging.getLogger("httpx").setLevel(logging.WARNING)
    sock = reserve_port(args.port)
    port = sock.getsockname()[1]
    url = f"http://127.0.0.1:{port}"
    app = create_app(directory)
    server = uvicorn.Server(uvicorn.Config(app, host="127.0.0.1", port=port, log_level="warning", access_log=False,
                                         timeout_graceful_shutdown=5))
    app.state.shutdown = lambda: setattr(server, "should_exit", True)
    stop = threading.Event()

    def open_when_ready():
        for _ in range(100):
            if stop.wait(0.1):
                return
            try:
                with urllib.request.urlopen(url + "/api/health", timeout=0.5) as response:
                    if response.status == 200:
                        webbrowser.open(url)
                        return
            except OSError:
                continue
        logger.error("Browser launch readiness timed out")

    if not args.no_browser:
        threading.Thread(target=open_when_ready, daemon=True).start()
    print(f"EveryTune em {url}\nDados: {directory}\nCtrl+C ou Encerrar nas configurações para sair.", flush=True)
    try:
        server.run(sockets=[sock])
    finally:
        stop.set()
        sock.close()
        handler.close()
        logger.removeHandler(handler)


if __name__ == "__main__":
    main()
