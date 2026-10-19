"""Deterministic Playwright smoke test against a loopback-only fixture.

This test does not contact NaviMind or external websites. It launches a local
HTTP server, navigates a headless Playwright browser to a synthetic form, fills
the form through BrowserAdapter semantic operations, and verifies the final
page state. Run from the repository root:

    python tools/smoke_browser_provider_local.py
"""
from __future__ import annotations

import os
import sys
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from threading import Thread

REPOSITORY_ROOT = Path(__file__).resolve().parents[1]
if str(REPOSITORY_ROOT) not in sys.path:
    sys.path.insert(0, str(REPOSITORY_ROOT))

FIXTURE_PATH = (
    Path(__file__).resolve().parent
    / "fixtures"
    / "browser_multistep_form.html"
)
FIXTURE_HTML = FIXTURE_PATH.read_bytes()

from app.agent.adapters.browser_adapter import (  # noqa: E402
    BrowserAdapter,
    BrowserElement,
    BrowserPage,
)
from app.agent.execution.playwright_browser_provider import (  # noqa: E402
    PlaywrightBrowserProvider,
)


class FixtureHandler(BaseHTTPRequestHandler):
    def do_GET(self) -> None:
        if self.path != "/":
            self.send_error(404)
            return

        self.send_response(200)
        self.send_header("Content-Type", "text/html; charset=utf-8")
        self.send_header("Content-Length", str(len(FIXTURE_HTML)))
        self.end_headers()
        self.wfile.write(FIXTURE_HTML)

    def log_message(self, format, *args) -> None:
        # Keep the smoke output focused on the assertions.
        return


def find_element(
    page: BrowserPage,
    *,
    label: str,
    capability: str,
) -> BrowserElement:
    matches = [
        element
        for element in page.elements
        if element.label == label
        and element.interaction_capability.casefold() == capability.casefold()
    ]
    if len(matches) != 1:
        observed = [
            (element.label, element.interaction_capability)
            for element in page.elements
        ]
        raise AssertionError(
            f"Expected exactly one {capability} target {label!r}; "
            f"matched {len(matches)}. Observed: {observed!r}"
        )
    return matches[0]


def main() -> int:
    # These overrides are process-local and opt in only to a headless browser
    # against the local synthetic fixture. No remote reasoning is configured.
    os.environ["AGENT_BROWSER_ENABLED"] = "1"
    os.environ["AGENT_BROWSER_HEADLESS"] = "1"

    server = ThreadingHTTPServer(("127.0.0.1", 0), FixtureHandler)
    server_thread = Thread(target=server.serve_forever, daemon=True)
    server_thread.start()

    fixture_url = f"http://127.0.0.1:{server.server_port}/"
    provider = PlaywrightBrowserProvider(
        browser_type="chromium",
        headless=True,
        navigation_timeout_ms=10_000,
    )
    adapter = BrowserAdapter(
        provider=provider,
        allowed_domains=("127.0.0.1",),
        dry_run=False,
    )

    try:
        if not provider.is_available():
            raise RuntimeError(
                "Playwright Python package is not available. "
                "Install project test dependencies before running this smoke."
            )

        # Verify allowlist rejection happens before any outside navigation.
        try:
            adapter.open("https://example.com/")
        except (ValueError, PermissionError):
            pass
        else:
            raise AssertionError("BrowserAdapter accepted a non-allowlisted domain.")

        page = adapter.open(fixture_url)
        if page.title != "Browser Multistep Form":
            raise AssertionError(f"Unexpected initial title: {page.title!r}")
        print("local_navigation: PASS")

        name_target = find_element(
            page,
            label="Imię klienta",
            capability="EDITABLE",
        )
        page = adapter.write_text(name_target, "Adam")
        name_after = find_element(
            page,
            label="Imię klienta",
            capability="EDITABLE",
        )
        if name_after.current_value != "Adam":
            raise AssertionError(
                f"Text entry was not independently observed: "
                f"{name_after.current_value!r}"
            )
        print("semantic_text_entry: PASS")

        country_target = find_element(
            page,
            label="Kraj",
            capability="SELECTABLE",
        )
        page = adapter.select_option(country_target, "Polska")
        country_after = find_element(
            page,
            label="Kraj",
            capability="SELECTABLE",
        )
        if country_after.current_value != "Polska":
            raise AssertionError(
                f"Option selection was not independently observed: "
                f"{country_after.current_value!r}"
            )
        print("semantic_select_option: PASS")

        submit_target = find_element(
            page,
            label="Zatwierdź formularz",
            capability="CLICKABLE",
        )
        page = adapter.click(submit_target)

        if page.title != "Browser Multistep Form — Success":
            raise AssertionError(
                f"Final title does not prove success: {page.title!r}"
            )
        if "Formularz zatwierdzony" not in page.text:
            raise AssertionError(
                "Expected final confirmation text was not observed."
            )
        if "Formularz zatwierdzony" in page.text and "Dane formularza są niepoprawne" in page.text:
            raise AssertionError("The fixture reported conflicting final states.")

        print("semantic_click: PASS")
        print("final_state_verification: PASS")
        print(f"final_url: {page.url}")
        print(f"final_title: {page.title}")
        print("execution_scope: loopback fixture only")
        print("remote_naviMind_calls: 0")
        print("external_navigation: blocked by allowlist")
        return 0
    finally:
        provider.close()
        server.shutdown()
        server.server_close()
        server_thread.join(timeout=2)


if __name__ == "__main__":
    raise SystemExit(main())
