from __future__ import annotations

from http import HTTPStatus
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from mimetypes import guess_type
from pathlib import Path
import json
import socket
from urllib.parse import urlparse

from .document_engine import ProformaData, build_docx, build_pdf


ROOT_DIR = Path(__file__).resolve().parent.parent
STATIC_DIR = ROOT_DIR / "static"


class ProformaRequestHandler(BaseHTTPRequestHandler):
    server_version = "ProformaBuilder/1.0"

    def do_GET(self) -> None:
        request_path = urlparse(self.path).path

        if request_path in {"/", "/index.html"}:
            self._serve_file(STATIC_DIR / "index.html")
            return

        if request_path.endswith("/manifest.webmanifest"):
            self._serve_file(STATIC_DIR / "manifest.webmanifest")
            return

        if request_path.endswith("/service-worker.js"):
            self._serve_file(STATIC_DIR / "service-worker.js")
            return

        if request_path.startswith("/static/"):
            requested = request_path.removeprefix("/static/")
            if self._serve_static_asset(requested):
                return

        if request_path == "/health":
            self._send_json({"status": "ok"})
            return

        if self._serve_static_asset(request_path.lstrip("/")):
            return

        self.send_error(HTTPStatus.NOT_FOUND, "Ruta no encontrada.")

    def do_POST(self) -> None:
        request_path = urlparse(self.path).path

        if request_path not in {"/api/export/pdf", "/api/export/docx"}:
            self.send_error(HTTPStatus.NOT_FOUND, "Ruta no encontrada.")
            return

        try:
            payload = self._read_json_body()
            data = ProformaData.from_payload(payload)
            if request_path.endswith("/pdf"):
                output_path = build_pdf(data)
                content_type = "application/pdf"
            else:
                output_path = build_docx(data)
                content_type = (
                    "application/vnd.openxmlformats-officedocument.wordprocessingml.document"
                )

            file_bytes = output_path.read_bytes()
            self.send_response(HTTPStatus.OK)
            self.send_header("Content-Type", content_type)
            self.send_header(
                "Content-Disposition",
                f'attachment; filename="{output_path.name}"',
            )
            self.send_header("Content-Length", str(len(file_bytes)))
            self.end_headers()
            self.wfile.write(file_bytes)
        except ValueError as error:
            self._send_json({"error": str(error)}, status=HTTPStatus.BAD_REQUEST)
        except json.JSONDecodeError:
            self._send_json({"error": "El cuerpo debe estar en formato JSON."}, status=HTTPStatus.BAD_REQUEST)
        except Exception as error:  # pragma: no cover - guardrail path
            self._send_json({"error": f"No se pudo generar el archivo: {error}"}, status=HTTPStatus.INTERNAL_SERVER_ERROR)

    def log_message(self, format_string: str, *args) -> None:
        return

    def _serve_file(self, file_path: Path) -> None:
        if not file_path.exists() or not file_path.is_file():
            self.send_error(HTTPStatus.NOT_FOUND, "Archivo no encontrado.")
            return

        data = file_path.read_bytes()
        content_type = guess_type(str(file_path))[0] or "application/octet-stream"
        self.send_response(HTTPStatus.OK)
        self.send_header("Content-Type", content_type)
        self.send_header("Content-Length", str(len(data)))
        self.end_headers()
        self.wfile.write(data)

    def _serve_static_asset(self, requested: str) -> bool:
        if not requested:
            return False

        safe_path = (STATIC_DIR / requested).resolve()
        if not str(safe_path).startswith(str(STATIC_DIR.resolve())):
            self.send_error(HTTPStatus.FORBIDDEN, "Ruta no permitida.")
            return True

        if safe_path.exists() and safe_path.is_file():
            self._serve_file(safe_path)
            return True

        return False

    def _read_json_body(self) -> dict:
        content_length = int(self.headers.get("Content-Length", "0"))
        raw_body = self.rfile.read(content_length)
        return json.loads(raw_body.decode("utf-8"))

    def _send_json(self, payload: dict, status: HTTPStatus = HTTPStatus.OK) -> None:
        body = json.dumps(payload, ensure_ascii=False).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)


def discover_local_ip() -> str:
    try:
        with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as sock:
            sock.connect(("8.8.8.8", 80))
            return sock.getsockname()[0]
    except OSError:
        return "127.0.0.1"


def create_server(host: str = "127.0.0.1", port: int = 8000) -> ThreadingHTTPServer:
    return ThreadingHTTPServer((host, port), ProformaRequestHandler)


def run_server(host: str = "127.0.0.1", port: int = 8000) -> None:
    server = create_server(host=host, port=port)
    active_port = server.server_address[1]
    local_ip = discover_local_ip()
    print("Servidor listo para la app de proformas.")
    print(f"Escritorio: http://{host}:{active_port}")
    print(f"Móvil en la misma red: http://{local_ip}:{active_port}")
    server.serve_forever()
