#!/usr/bin/env python3
"""Loopback-only full-stack local prototype for verifying archived NDA reviews.

Run from any directory: python3 /path/to/scripts/web_lab.py
No model inference, arbitrary command execution, uploads, or general file serving.
"""
from __future__ import annotations

import argparse
import json
import os
import subprocess
import sys
import threading
from datetime import datetime, timezone
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import urlsplit

ROOT = Path(__file__).resolve().parents[1]
RUN_LAB = ROOT / "scripts" / "run_lab.py"
MAX_BODY = 1024
MAX_EVIDENCE = 4 * 1024 * 1024
TIMEOUT_SECONDS = 60
FILES = {
    "/": ("web_lab.html", "text/html; charset=utf-8"),
    "/evidence/repeatability.json": ("repeatability/results_summary.json", "application/json; charset=utf-8"),
    "/evidence/one-pager.pdf": ("repeatability/Repeatability_Results.pdf", "application/pdf"),
}


class CheckError(Exception):
    """A safe error code without subprocess output or local filesystem details."""


def safe_file(relative_path: str) -> Path:
    """Only callers using the fixed FILES map may select a file."""
    resolved = (ROOT / relative_path).resolve()
    if not resolved.is_relative_to(ROOT.resolve()) or not resolved.is_file():
        raise FileNotFoundError
    return resolved


def run_fixed_check() -> tuple[int, dict]:
    # This literal argument vector is never built from an HTTP request.
    try:
        completed = subprocess.run(
            [sys.executable, str(RUN_LAB), "check", "--require-repeats", "--json"],
            cwd=ROOT,
            capture_output=True,
            text=True,
            timeout=TIMEOUT_SECONDS,
            check=False,
            shell=False,
        )
    except subprocess.TimeoutExpired as exc:
        raise CheckError("check_timeout") from exc
    except OSError as exc:
        raise CheckError("check_unavailable") from exc
    try:
        payload = json.loads(completed.stdout)
    except (ValueError, TypeError) as exc:
        raise CheckError("check_failed_without_json") from exc
    if not isinstance(payload, dict) or payload.get("status") not in {"PASS", "FAIL"}:
        raise CheckError("invalid_check_result")
    return completed.returncode, payload


class LabServer(ThreadingHTTPServer):
    daemon_threads = True

    def __init__(self, port: int = 8765, runner=None):
        # No host option: this service can only bind IPv4 loopback.
        super().__init__(("127.0.0.1", port), LabHandler)
        self.runner = runner or run_fixed_check
        self.check_lock = threading.Lock()
        self.state_lock = threading.Lock()
        self.last_check = None

    @property
    def origin(self):
        return f"http://127.0.0.1:{self.server_port}"


class LabHandler(BaseHTTPRequestHandler):
    server_version = "LocalNDALab/1.0"
    sys_version = ""
    protocol_version = "HTTP/1.1"

    def log_message(self, format, *args):
        # Avoid logging arbitrary request headers, bodies, or source material.
        return

    def setup(self):
        super().setup()
        self.connection.settimeout(10)

    def send_error(self, code, message=None, explain=None):
        self.send_json(code, {"ok": False, "error": "invalid_http_request"})

    def send_bytes(self, status, payload, content_type):
        self.send_response(status)
        self.send_header("Content-Type", content_type)
        self.send_header("Content-Length", str(len(payload)))
        self.send_header("Cache-Control", "no-store")
        self.send_header("X-Content-Type-Options", "nosniff")
        self.send_header("Referrer-Policy", "no-referrer")
        self.send_header("Cross-Origin-Resource-Policy", "same-origin")
        self.send_header("Content-Security-Policy", "default-src 'none'; script-src 'unsafe-inline'; style-src 'unsafe-inline'; connect-src 'self'; img-src 'self'; base-uri 'none'; form-action 'none'; frame-ancestors 'none'")
        self.send_header("Connection", "close")
        self.end_headers()
        self.close_connection = True
        self.wfile.write(payload)

    def send_json(self, status, value):
        payload = json.dumps(value, ensure_ascii=False, allow_nan=False).encode("utf-8")
        self.send_bytes(status, payload, "application/json; charset=utf-8")

    def reject(self, status, code):
        self.send_json(status, {"ok": False, "error": code})

    def route(self):
        # Reject absolute-form URLs, duplicate Host, queries, and encoded paths.
        # Exact comparison provides no path traversal or directory-listing route.
        hosts = self.headers.get_all("Host", [])
        if hosts != [f"127.0.0.1:{self.server.server_port}"]:
            self.reject(400, "invalid_host")
            return None
        try:
            parsed = urlsplit(self.path)
        except ValueError:
            self.reject(404, "unknown_route")
            return None
        if parsed.scheme or parsed.netloc or parsed.query or parsed.fragment or parsed.path != self.path:
            self.reject(404, "unknown_route")
            return None
        return parsed.path

    def do_GET(self):
        route = self.route()
        if route is None:
            return
        if route == "/api/status":
            with self.server.state_lock:
                last_check = self.server.last_check
            saved = None
            try:
                path = safe_file(FILES["/evidence/repeatability.json"][0])
                if path.stat().st_size <= MAX_EVIDENCE:
                    saved = json.loads(path.read_text(encoding="utf-8"))
            except (OSError, ValueError):
                pass
            links = {}
            for url, (relative, _) in FILES.items():
                if url == "/":
                    continue
                try:
                    safe_file(relative)
                except OSError:
                    continue
                links["repeatability_json" if url.endswith(".json") else "one_pager"] = url
            self.send_json(200, {
                "ok": True,
                "mode": "full-stack local prototype",
                "operation": "deterministic checks of archived model outputs",
                "new_model_calls": 0,
                "last_check": last_check,
                "saved_repeatability": saved,
                "evidence_links": links,
            })
            return
        if route not in FILES:
            self.reject(404, "unknown_route")
            return
        relative, content_type = FILES[route]
        try:
            path = safe_file(relative)
            if path.stat().st_size > MAX_EVIDENCE:
                raise OSError
            payload = path.read_bytes()
        except OSError:
            self.reject(404, "evidence_unavailable")
            return
        self.send_bytes(200, payload, content_type)

    def do_POST(self):
        route = self.route()
        if route is None:
            return
        if route != "/api/check":
            self.reject(404, "unknown_route")
            return
        origins = self.headers.get_all("Origin", [])
        if origins and origins != [self.server.origin]:
            self.reject(403, "cross_origin_request_rejected")
            return
        if self.headers.get("Sec-Fetch-Site", "") == "cross-site":
            self.reject(403, "cross_origin_request_rejected")
            return
        if self.headers.get_all("Transfer-Encoding"):
            self.reject(400, "unsupported_transfer_encoding")
            return
        lengths = self.headers.get_all("Content-Length", [])
        if len(lengths) != 1 or not lengths[0].isascii() or not lengths[0].isdigit():
            self.reject(400, "invalid_content_length")
            return
        if len(lengths[0]) > len(str(MAX_BODY)):
            self.reject(413, "request_too_large")
            return
        length = int(lengths[0])
        if length > MAX_BODY:
            self.reject(413, "request_too_large")
            return
        types = self.headers.get_all("Content-Type", [])
        if len(types) != 1 or types[0].lower().replace(" ", "") not in {"application/json", "application/json;charset=utf-8"}:
            self.reject(415, "json_required")
            return
        try:
            raw = self.rfile.read(length)
            if len(raw) != length:
                raise ValueError
            body = json.loads(raw.decode("utf-8"))
        except (ValueError, UnicodeError, TimeoutError, OSError):
            self.reject(400, "invalid_json")
            return
        if body != {} or not isinstance(body, dict):
            self.reject(400, "empty_object_required")
            return
        if not self.server.check_lock.acquire(blocking=False):
            self.reject(409, "check_already_running")
            return
        try:
            try:
                returncode, payload = self.server.runner()
                passed = returncode == 0 and payload.get("status") == "PASS"
                result = {
                    "ok": passed,
                    "status": "PASS" if passed else "FAIL",
                    "checked_at": datetime.now(timezone.utc).isoformat(timespec="seconds"),
                    "exit_code": returncode,
                    "new_model_calls": 0,
                    "result": payload,
                }
                with self.server.state_lock:
                    self.server.last_check = result
                self.send_json(200, result)
            except CheckError as exc:
                code = str(exc) if str(exc) in {"check_timeout", "check_unavailable", "check_failed_without_json", "invalid_check_result"} else "check_failed"
                result = {"ok": False, "status": "ERROR", "error": code, "new_model_calls": 0}
                with self.server.state_lock:
                    self.server.last_check = result
                self.send_json(500, result)
            except Exception:
                # Never expose tracebacks, source content, or subprocess stderr.
                result = {"ok": False, "status": "ERROR", "error": "check_failed", "new_model_calls": 0}
                with self.server.state_lock:
                    self.server.last_check = result
                self.send_json(500, result)
        finally:
            self.server.check_lock.release()

    def do_OPTIONS(self):
        self.reject(405, "method_not_allowed")

    do_PUT = do_OPTIONS
    do_PATCH = do_OPTIONS
    do_DELETE = do_OPTIONS
    do_HEAD = do_OPTIONS


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--host", choices=["127.0.0.1"], default="127.0.0.1", help="Compatibility argument; only IPv4 loopback is allowed")
    parser.add_argument("--port", type=int, default=int(os.environ.get("PORT", "8765")), help="Loopback port, default PORT or 8765; 0 selects an available port")
    parser.add_argument("--strictPort", action="store_true", help="Compatibility argument; port binding is always strict")
    args = parser.parse_args()
    if not 0 <= args.port <= 65535:
        parser.error("port must be between 0 and 65535")
    with LabServer(args.port) as server:
        print(f"NDA Review Lab (full-stack local prototype): {server.origin}", flush=True)
        print("Archived outputs only; deterministic verification; no new model calls. Ctrl+C stops the server.", flush=True)
        try:
            server.serve_forever()
        except KeyboardInterrupt:
            pass


if __name__ == "__main__":
    main()
