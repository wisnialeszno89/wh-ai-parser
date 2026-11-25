"""Model-selected *read-only* local tools, verified against host-owned registry.

This is deliberately separate from AgentControlLoop native action execution.
A string/JSON from a remote model can request only exact tool IDs supplied
by the trusted local host. It cannot grant permissions or select arbitrary
Python functions, shell commands, file paths or desktop action targets.
"""
from __future__ import annotations

from dataclasses import dataclass
import json
from typing import Callable, Mapping


@dataclass(frozen=True)
class ReadOnlyTool:
    name: str
    description: str
    run: Callable[[], str]
    requires_document_consent: bool = False
    synthesize_result: bool = False


@dataclass(frozen=True)
class ModelToolDecision:
    kind: str
    tool: str = ""
    answer: str = ""


def tool_catalog_instructions(tools: Mapping[str, ReadOnlyTool]) -> str:
    entries = "\n".join(
        "- " + tool.name + ": " + tool.description
        for tool in tools.values()
    )
    return (
        "\n\nDECYZJA AI: DOSTĘPNE LOKALNE NARZĘDZIA TYLKO DO ODCZYTU.\n"
        + entries + "\n"
        "Dla każdej odpowiedzi zwróć JEDEN obiekt JSON i nic poza nim. "
        "Gdy potrzebujesz rzeczywistej obserwacji komputera, użyj "
        "{\"kind\":\"tool\",\"tool\":\"NAZWA_NARZEDZIA\"}. "
        "W przeciwnym razie odpowiedz naturalnie po polsku: "
        "{\"kind\":\"answer\",\"answer\":\"Twoja odpowiedź\"}. "
        "Nie możesz zakładać, że narzędzie wykonało akcję, dopóki host "
        "nie zwróci wyniku. Nie ma narzędzia do klikania, wpisywania, "
        "uruchamiania aplikacji, zapisu ofert, PowerShell ani napraw Windows. "
        "Nigdy nie umieszczaj własnych komend lub parametrów wykonania. "
        "Jeżeli użytkownik prosi o zmianę danych lub uruchomienie programu, "
        "wyjaśnij ograniczenie, nie udawaj działania."
    )


def parse_model_tool_decision(raw: str, allowed: Mapping[str, ReadOnlyTool]) -> ModelToolDecision:
    if not isinstance(raw, str) or len(raw) > 3500:
        raise ValueError("tool_decision_invalid")
    text = raw.strip()
    # Some chat models surround otherwise valid JSON in a Markdown fence.
    # Strip only an exact single fence; never search arbitrary prose for
    # executable-looking JSON snippets.
    if text.startswith("```json\n") and text.endswith("\n```"):
        text = text[len("```json\n"):-len("\n```")].strip()
    elif text.startswith("```\n") and text.endswith("\n```"):
        text = text[len("```\n"):-len("\n```")].strip()
    try:
        value = json.loads(text)
    except (TypeError, ValueError):
        raise ValueError("tool_decision_invalid_json") from None
    if not isinstance(value, dict):
        raise ValueError("tool_decision_invalid_shape")
    if value.get("kind") == "tool":
        if set(value) != {"kind", "tool"}:
            raise ValueError("tool_decision_invalid_fields")
        tool = value.get("tool")
        if not isinstance(tool, str) or tool not in allowed:
            raise ValueError("tool_decision_not_allowlisted")
        return ModelToolDecision(kind="tool", tool=tool)
    if value.get("kind") == "answer":
        if set(value) != {"kind", "answer"}:
            raise ValueError("tool_decision_invalid_fields")
        answer = value.get("answer")
        if not isinstance(answer, str) or not answer.strip() or len(answer) > 3000:
            raise ValueError("tool_decision_invalid_answer")
        return ModelToolDecision(kind="answer", answer=answer.strip())
    raise ValueError("tool_decision_unsupported")


def invoke_read_only_tool(name: str, tools: Mapping[str, ReadOnlyTool]) -> str:
    """No dynamic imports, eval, shell, model-generated arguments or UI writes."""
    tool = tools.get(name)
    if not isinstance(tool, ReadOnlyTool) or tool.name != name:
        return "Nie mam podłączonego takiego narzędzia. Nie wykonałem działania."
    try:
        result = tool.run()
    except Exception:
        return "Nie udało się bezpiecznie wykonać odczytu. Niczego nie zmieniłem."
    if not isinstance(result, str) or not result.strip() or len(result) > 3000:
        return "Narzędzie nie zwróciło prawidłowego wyniku. Niczego nie zmieniłem."
    return result.strip()
