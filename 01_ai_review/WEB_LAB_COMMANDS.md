# Run the local NDA Review Lab

Requires Python 3.10 or later. No third-party packages, API keys or model connection are needed. From this `01_ai_review` folder:

```sh
python3 scripts/web_lab.py
```

Open the printed `http://127.0.0.1:8765` URL. Click **Run checks** to call the local backend and recompute metrics from the archived outputs. Stop with `Ctrl+C`. If that port is occupied, choose another loopback port:

```sh
python3 scripts/web_lab.py --port 8766
```

The equivalent CLI and HTTP test commands are:

```sh
python3 scripts/run_lab.py check --require-repeats --json
python3 scripts/test_web_lab.py
```

The server also accepts an absolute script path from another working directory. Opening `web_lab.html` directly does not start the backend.

This is a **full-stack local prototype**: browser → loopback HTTP → fixed Python CLI → archived evidence. It does not perform new model inference, process a newly uploaded contract or implement production approval controls. The displayed study consists of three preserved independent agent batches, each covering the same 15 synthetic documents. A new button click is a new deterministic check, not a new reviewer batch.

The server binds only `127.0.0.1`. Its only content routes are `/`, `/api/status`, `/api/check`, `/evidence/repeatability.json` and the optional `/evidence/one-pager.pdf`. The PDF link appears when `repeatability/Repeatability_Results.pdf` is present. There is no directory listing or upload endpoint. The check accepts an empty JSON object only and runs the literal argument vector `[sys.executable, run_lab.py, 'check', '--require-repeats', '--json']` with no shell. Cross-origin POST requests, including `Origin: null`, are rejected. Request bodies are capped at 1,024 bytes; allowlisted files resolving outside this folder are not served.

The `PORT` environment variable supplies the default port when set; an explicit `--port` overrides it. Open the printed IPv4 loopback address so its Host and Origin match the server's local origin.

For development-preview command compatibility, `--host 127.0.0.1` and `--strictPort` are accepted. No other host is permitted, and an occupied explicit port always fails rather than switching silently.

The check writes derived score reports through the existing CLI and preserves the three saved reviewer outputs. The UI distinguishes saved metrics from a check completed in the current server session. Inspect the downloadable JSON and CLI output when reviewing a result; human legal review remains required.
