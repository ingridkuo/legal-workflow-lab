# Run a separate controlled API study

This add-on is prepared code, not a completed API experiment. No real API responses or API performance scores are included. The existing agent-batch study remains unchanged.

Python 3.10 or later and the standard library are sufficient. Run commands from this Lab folder. Access to the configured model and API usage credits are required only for `--execute`.

## 1. Inspect the offline plan

```sh
python scripts/api_study.py plan
python scripts/test_api_study.py
```

The configured snapshot is `gpt-5.4-mini-2026-03-17`, with `reasoning.effort=low` and a 4,096-token output allowance. Temperature and top_p are omitted and recorded as omitted. This avoids claiming a value that was never submitted. No tools, conversation or previous response is supplied. Each agreement starts a separate API request.

The request uses the frozen v2 prompt and supplied NDA policy. The API schema converts constants to typed singleton enums and omits pattern/minLength restrictions; the original schema remains the local validation standard. This adapter is recorded separately and does not alter the old evaluation schema.

## 2. Smoke-test one development agreement

```sh
python scripts/api_study.py smoke --study smoke-001
python scripts/api_study.py smoke --study smoke-001 --execute --prompt-key
python scripts/api_study.py score --study smoke-001
```

The first command is an offline preview. The second makes one billable API request for development document NDA-01. It asks for the key privately in the terminal; entered characters are not displayed or saved. Alternatively, set `OPENAI_API_KEY` privately and omit `--prompt-key`. Do not place a key in source code, screenshots, chat or GitHub.

Confirm that one response is complete, its returned model matches the requested snapshot, and its structured result can be scored. This smoke result does not count as one of the 45 held-out requests. A smoke check can establish that the pipeline works even if the legal result has errors; inspect the scored output rather than assuming a perfect result.

## 3. Run the 45-request study

```sh
python scripts/api_study.py run --study nda-api-001
python scripts/api_study.py run --study nda-api-001 --execute --max-calls 45 --prompt-key
python scripts/api_study.py score --study nda-api-001
```

Without `--execute`, no request is sent. An execution defaults to at most one new call unless `--max-calls` is explicitly supplied. The full protocol comprises 15 held-out documents in each of three replicates: 45 separate requests. The request-count and output-token caps are not a dollar spending limit. Confirm model access, current pricing and available credits before execution.

The program freezes the exact request payloads and source identities before the first call. Reference labels are retained for offline scoring but never sent in a request. Successful saved responses are reused on resume only when the frozen configuration and source bytes still match.

There are no automatic network retries. Refusals, incomplete responses, model mismatches and malformed outputs are preserved and stop execution. A timeout may have been processed by the provider; inspect the record and account usage before deciding on another study. Do not delete failed attempts to make the result appear complete.

## 4. Inspect the evidence

Each new study lives in `api_studies/<study-name>/`:

- `protocol.json`: snapshot, settings, endpoint, exact payloads and source hashes.
- `jobs/<job>/request.json`: the submitted body without an API key.
- `attempt.json`, `transport.json`, `response.json`: timestamps, selected provider headers and the preserved response body. An unexpected credential echo is redacted, explicitly marked and excluded from scoring.
- `result.json`: response ID, returned model, usage, parsed finding and byte bindings.
- `failure.json`: failure type without secret-bearing exception text, where applicable.
- `results_summary.json`, `per_run_metrics.csv`, `per_issue_consistency.csv` and `API_Results.md`: created only after the complete study can be scored.

Precision uses source-supported document/rule matches divided by returned findings; recall uses those matches divided by positive reference instances. Empty denominators remain undefined. Severity, routing and source-status differences remain separate from issue detection. Consistency can be consistently wrong.

This repeats the existing synthetic held-out partition. Even a perfect result would not establish performance on new client agreements, a population accuracy rate or a production deployment.

## Official references

- [OpenAI developer quickstart](https://developers.openai.com/api/docs/quickstart)
- [GPT-5.4 mini model and snapshots](https://developers.openai.com/api/docs/models/gpt-5.4-mini)
- [Responses API create reference](https://developers.openai.com/api/reference/python/resources/responses/methods/create)
- [Structured outputs](https://developers.openai.com/api/docs/guides/structured-outputs)

The account may not have access to every documented model. If a snapshot or parameter is unavailable, preserve the failed attempt and prepare a newly named protocol with supported settings; do not silently change a running study.
