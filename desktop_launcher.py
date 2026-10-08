from __future__ import annotations

from pathlib import Path
from threading import Thread
import time
import webbrowser

from proforma_app.server import create_server


def main() -> None:
    server = create_server(host="127.0.0.1", port=0)
    port = server.server_address[1]

    thread = Thread(target=server.serve_forever, daemon=True)
    thread.start()

    url = f"http://127.0.0.1:{port}"
    print("App de proformas iniciada.")
    print(f"Abriendo {url}")
    webbrowser.open(url)

    try:
        while True:
            time.sleep(0.5)
    except KeyboardInterrupt:
        pass
    finally:
        server.shutdown()
        server.server_close()


if __name__ == "__main__":
    main()
