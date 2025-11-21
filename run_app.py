"""Standalone launcher for the translateppt Flask application."""
from __future__ import annotations

import os
import socket
import threading
import time
import webbrowser

from backend.app import create_app


def _wait_for_server(host: str, port: int, timeout: float = 15.0) -> bool:
    """Poll the HTTP port until it is reachable or timeout occurs."""
    deadline = time.time() + timeout
    while time.time() < deadline:
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
            sock.settimeout(0.5)
            try:
                sock.connect((host, port))
            except OSError:
                time.sleep(0.3)
                continue
            return True
    return False


def _open_browser(host: str, port: int) -> None:
    url = f"http://{host}:{port}"
    if _wait_for_server(host, port):
        webbrowser.open(url)


def main() -> None:
    host = os.getenv("HOST", "localhost")  # Use localhost for consistency with main site
    port = int(os.getenv("PORT", "5000"))

    app = create_app()

    if os.getenv("AUTO_OPEN_BROWSER", "1") not in {"0", "false", "False"}:
        threading.Thread(target=_open_browser, args=(host, port), daemon=True).start()

    print(f"TranslatePPT is running at http://{host}:{port}\nPress CTRL+C to stop.")
    app.run(host=host, port=port, debug=False, use_reloader=False)


if __name__ == "__main__":
    main()
