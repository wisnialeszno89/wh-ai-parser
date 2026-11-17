"""Diagnose Ollama localhost separately from WindowHub.

No screenshots, UI controls, customer data, or input actions. Only a tiny
synthetic chat request is sent to 127.0.0.1.
"""
from __future__ import annotations
import argparse
import json
import time
from urllib.request import Request, urlopen
from urllib.error import URLError, HTTPError

BASE = "http://127.0.0.1:11434"

def check(model: str, timeout: int) -> int:
    try:
        start = time.monotonic()
        with urlopen(BASE + "/api/version", timeout=5) as response:
            version = json.load(response)
        print("OLLAMA_API=READY")
        print("OLLAMA_VERSION=" + str(version.get("version", "unknown")))
        with urlopen(BASE + "/api/tags", timeout=5) as response:
            tags = json.load(response)
        models = [str(item.get("name")) for item in tags.get("models", [])]
        print("OLLAMA_MODELS=" + ",".join(models) if models else "OLLAMA_MODELS=NONE")
        if model not in models:
            print("STOP=MODEL_NOT_INSTALLED")
            return 4
        body = json.dumps({
            "model": model,
            "stream": False,
            "format": "json",
            "options": {"temperature": 0, "num_predict": 80, "num_ctx": 2048},
            "messages": [
                {"role": "system", "content": "Reply with one JSON object and nothing else."},
                {"role": "user", "content": 'Return exactly {"status":"ok"}. No explanation.'},
            ],
        }).encode()
        request = Request(
            BASE + "/api/chat", data=body,
            headers={"Content-Type": "application/json"}, method="POST",
        )
        print("OLLAMA_TEST=STARTED_NO_WINDOWHUB_DATA", flush=True)
        with urlopen(request, timeout=timeout) as response:
            result = json.load(response)
        seconds = time.monotonic() - start
        print("OLLAMA_TEST_SECONDS=" + str(round(seconds, 2)))
        print("OLLAMA_LOAD_SECONDS=" + str(round(result.get("load_duration", 0) / 1e9, 2)))
        print("OLLAMA_EVAL_TOKENS=" + str(result.get("eval_count", "unknown")))
        content = result.get("message", {}).get("content", "")
        obj = json.loads(content)
        print("OLLAMA_JSON=" + ("PASS" if isinstance(obj, dict) and obj.get("status") == "ok" else "UNEXPECTED"))
        return 0 if isinstance(obj, dict) and obj.get("status") == "ok" else 5
    except (TimeoutError, URLError) as exc:
        print("OLLAMA_TEST=TIMEOUT_OR_UNAVAILABLE_" + type(exc).__name__)
        return 5
    except HTTPError as exc:
        print("OLLAMA_TEST=HTTP_" + str(exc.code))
        return 5
    except (ValueError, KeyError, TypeError) as exc:
        print("OLLAMA_TEST=INVALID_RESPONSE_" + type(exc).__name__)
        return 5

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--model", default="qwen2.5:7b")
    parser.add_argument("--timeout", type=int, default=90)
    a = parser.parse_args()
    raise SystemExit(check(a.model, max(5, min(a.timeout, 300))))
