#!/usr/bin/env python3
"""HTTP boundary tests plus one real check of the preserved local cohort."""
from __future__ import annotations

import http.client
import json
import socket
import subprocess
import sys
import tempfile
import threading
import unittest
from pathlib import Path
from unittest.mock import patch

import web_lab


def fake_check():
    return 0, {"status": "PASS", "checks": ["test check"], "repeatability": None}


class HTTPBoundaryTests(unittest.TestCase):
    def setUp(self):
        self.calls = 0

        def runner():
            self.calls += 1
            return fake_check()

        self.server = web_lab.LabServer(port=0, runner=runner)
        self.thread = threading.Thread(target=self.server.serve_forever, daemon=True)
        self.thread.start()
        self.origin = self.server.origin

    def tearDown(self):
        self.server.shutdown()
        self.server.server_close()
        self.thread.join(timeout=5)

    def request(self, method, path, body=None, headers=None):
        connection = http.client.HTTPConnection("127.0.0.1", self.server.server_port, timeout=5)
        connection.request(method, path, body=body, headers=headers or {})
        response = connection.getresponse()
        status, response_headers, raw = response.status, dict(response.getheaders()), response.read()
        connection.close()
        return status, response_headers, raw

    def post(self, body="{}", **headers):
        defaults = {"Content-Type": "application/json", "Origin": self.origin}
        defaults.update(headers)
        status, response_headers, raw = self.request("POST", "/api/check", body, defaults)
        self.assertEqual(response_headers["Content-Type"], "application/json; charset=utf-8")
        return status, json.loads(raw)

    def test_loopback_bind_and_valid_post_preserve_session_status(self):
        self.assertEqual(self.server.server_address[0], "127.0.0.1")
        status, data = self.post()
        self.assertEqual(status, 200)
        self.assertTrue(data["ok"])
        self.assertEqual(data["status"], "PASS")
        self.assertEqual(data["new_model_calls"], 0)
        self.assertEqual(self.calls, 1)
        status, _, raw = self.request("GET", "/api/status")
        self.assertEqual(status, 200)
        saved = json.loads(raw)
        self.assertEqual(saved["last_check"]["checked_at"], data["checked_at"])

    def test_malformed_json_and_arbitrary_args_never_run(self):
        for body, expected in [("{", "invalid_json"), ('{"args":["--root","/"]}', "empty_object_required"), ("[]", "empty_object_required"), ("null", "empty_object_required")]:
            with self.subTest(body=body):
                status, data = self.post(body)
                self.assertEqual(status, 400)
                self.assertEqual(data["error"], expected)
        self.assertEqual(self.calls, 0)

    def test_cross_origin_including_null_and_different_port_are_rejected(self):
        for origin in ["null", "https://example.invalid", "http://127.0.0.1:1", "http://localhost:" + str(self.server.server_port)]:
            with self.subTest(origin=origin):
                status, data = self.post(Origin=origin)
                self.assertEqual(status, 403)
                self.assertEqual(data["error"], "cross_origin_request_rejected")
        self.assertEqual(self.calls, 0)

    def test_command_line_request_without_origin_is_allowed(self):
        status, _, raw = self.request("POST", "/api/check", "{}", {"Content-Type": "application/json"})
        self.assertEqual(status, 200)
        self.assertTrue(json.loads(raw)["ok"])
        self.assertEqual(self.calls, 1)

    def test_content_type_body_size_and_transfer_encoding(self):
        status, data = self.post(**{"Content-Type": "text/plain"})
        self.assertEqual((status, data["error"]), (415, "json_required"))
        status, data = self.post(" " * (web_lab.MAX_BODY + 1))
        self.assertEqual((status, data["error"]), (413, "request_too_large"))
        status, data = self.post(**{"Transfer-Encoding": "chunked"})
        self.assertEqual((status, data["error"]), (400, "unsupported_transfer_encoding"))
        self.assertEqual(self.calls, 0)

    def test_unknown_routes_queries_and_traversal_are_not_served(self):
        for path in ["/missing", "/scripts/web_lab.py", "/repeatability/", "/../README.md", "/%2e%2e/README.md", "/api/status?file=README.md"]:
            with self.subTest(path=path):
                status, _, raw = self.request("GET", path)
                self.assertEqual(status, 404)
                self.assertEqual(json.loads(raw)["error"], "unknown_route")
        status, _, raw = self.request("POST", "/missing", "{}", {"Content-Type": "application/json", "Origin": self.origin})
        self.assertEqual(status, 404)
        self.assertEqual(self.calls, 0)

    def test_bad_host_and_duplicate_origin_are_rejected(self):
        status, _, raw = self.request("GET", "/api/status", headers={"Host": "evil.invalid"})
        self.assertEqual((status, json.loads(raw)["error"]), (400, "invalid_host"))
        conn = http.client.HTTPConnection("127.0.0.1", self.server.server_port, timeout=5)
        conn.putrequest("POST", "/api/check")
        conn.putheader("Content-Type", "application/json")
        conn.putheader("Content-Length", "2")
        conn.putheader("Origin", self.origin)
        conn.putheader("Origin", self.origin)
        conn.endheaders(b"{}")
        response = conn.getresponse()
        self.assertEqual(response.status, 403)
        response.read()
        conn.close()
        self.assertEqual(self.calls, 0)

    def test_duplicate_content_length_and_unsupported_methods(self):
        conn = http.client.HTTPConnection("127.0.0.1", self.server.server_port, timeout=5)
        conn.putrequest("POST", "/api/check")
        conn.putheader("Content-Type", "application/json")
        conn.putheader("Content-Length", "2")
        conn.putheader("Content-Length", "2")
        conn.endheaders(b"{}")
        response = conn.getresponse()
        self.assertEqual(response.status, 400)
        self.assertEqual(json.loads(response.read())["error"], "invalid_content_length")
        conn.close()
        status, _, raw = self.request("PUT", "/api/check", "{}")
        self.assertEqual((status, json.loads(raw)["error"]), (405, "method_not_allowed"))

    def test_malformed_absolute_url_and_extreme_length_return_json(self):
        # http.client itself rejects this malformed target, so send the wire form.
        with socket.create_connection(("127.0.0.1", self.server.server_port), timeout=5) as connection:
            wire = f"GET http://[ HTTP/1.1\r\nHost: 127.0.0.1:{self.server.server_port}\r\nConnection: close\r\n\r\n"
            connection.sendall(wire.encode("ascii"))
            chunks = []
            while chunk := connection.recv(4096):
                chunks.append(chunk)
        headers, raw = b"".join(chunks).split(b"\r\n\r\n", 1)
        self.assertIn(b" 404 ", headers.split(b"\r\n")[0])
        self.assertEqual(json.loads(raw)["error"], "unknown_route")
        conn = http.client.HTTPConnection("127.0.0.1", self.server.server_port, timeout=5)
        conn.putrequest("POST", "/api/check")
        conn.putheader("Content-Type", "application/json")
        conn.putheader("Content-Length", "9" * 5000)
        conn.endheaders()
        response = conn.getresponse()
        self.assertEqual(response.status, 413)
        self.assertEqual(json.loads(response.read())["error"], "request_too_large")
        conn.close()
        self.assertEqual(self.calls, 0)

    def test_allowlisted_symlink_outside_source_is_not_served(self):
        with tempfile.TemporaryDirectory() as directory:
            temporary = Path(directory)
            root = temporary / "root"
            root.mkdir()
            secret = temporary / "outside.txt"
            secret.write_text("must not be served")
            (root / "web_lab.html").symlink_to(secret)
            with patch.object(web_lab, "ROOT", root):
                status, _, raw = self.request("GET", "/")
                self.assertEqual(status, 404)
                self.assertNotIn(b"must not be served", raw)

    def test_runner_failure_returns_safe_json(self):
        def fail():
            raise RuntimeError("sensitive local path and source contents")

        self.server.runner = fail
        status, data = self.post()
        self.assertEqual(status, 500)
        self.assertEqual(data["error"], "check_failed")
        self.assertNotIn("sensitive", json.dumps(data))

    def test_simultaneous_check_is_rejected(self):
        self.server.check_lock.acquire()
        try:
            status, data = self.post()
            self.assertEqual((status, data["error"]), (409, "check_already_running"))
            self.assertEqual(self.calls, 0)
        finally:
            self.server.check_lock.release()


class FixedRunnerTests(unittest.TestCase):
    def test_literal_subprocess_without_shell(self):
        completed = subprocess.CompletedProcess([], 0, '{"status":"PASS"}', "")
        with patch.object(web_lab.subprocess, "run", return_value=completed) as run:
            result = web_lab.run_fixed_check()
        self.assertEqual(result, (0, {"status": "PASS"}))
        self.assertEqual(run.call_args.args, ([sys.executable, str(web_lab.RUN_LAB), "check", "--require-repeats", "--json"],))
        self.assertIs(run.call_args.kwargs["shell"], False)
        self.assertEqual(run.call_args.kwargs["cwd"], web_lab.ROOT)

    def test_non_json_and_timeout_fail_safely(self):
        completed = subprocess.CompletedProcess([], 1, "", "private source error")
        with patch.object(web_lab.subprocess, "run", return_value=completed):
            with self.assertRaisesRegex(web_lab.CheckError, "^check_failed_without_json$"):
                web_lab.run_fixed_check()
        with patch.object(web_lab.subprocess, "run", side_effect=subprocess.TimeoutExpired([], 1)):
            with self.assertRaisesRegex(web_lab.CheckError, "^check_timeout$"):
                web_lab.run_fixed_check()

    def test_real_preserved_cohort_check_once(self):
        # The single real CLI execution checks saved evidence, not model inference.
        returncode, payload = web_lab.run_fixed_check()
        self.assertEqual(returncode, 0)
        self.assertEqual(payload["status"], "PASS")
        self.assertTrue(payload["repeatability_scored"])
        summary = payload["repeatability"]
        self.assertEqual(summary["independent_agent_batches"], 3)
        self.assertEqual(summary["documents_per_batch"], 15)
        self.assertEqual(len(summary["runs"]), 3)


if __name__ == "__main__":
    unittest.main(verbosity=2)
