"""Regression: chat continuation does not create a new user mission revision."""
import ast
from pathlib import Path


def _continuation_predicate():
    source = Path("tools/navimind_main_workspace.py").read_text(encoding="utf-8")
    module = ast.parse(source)
    for node in ast.walk(module):
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)) and node.name == "_is_continue_current_mission_request":
            node.decorator_list = []
            ns = {}
            exec(compile(ast.Module(body=[node], type_ignores=[]), "<predicate>", "exec"), ns)
            return ns[node.name]
    raise AssertionError("continuation_classifier_missing")


def test_short_continuation_commands_are_recognized():
    predicate = _continuation_predicate()
    for text in ("kontynuuj", "Wznów pracę", "wykonaj następny krok", "dalej",
                 "okej zrób ofertę", "Dobrze, zrob te oferte.", "ok, dalej",
                 "gotowe", "klient wybrany", "potwierdzam klienta",
                 "bez montażu, demontażu i wykończenia"):
        assert predicate(text)


def test_unsafe_mutations_never_count_as_status_only_continuation():
    predicate = _continuation_predicate()
    for text in (
        "kontynuuj, wpisz rabat 20%",
        "wybierz istniejącego klienta Top Trans",
        "zapisz ofertę",
        "kontynuuj i kliknij Zapisz",
        "okej zrób ofertę dla innego klienta",
        "zrób nową ofertę",
    ):
        assert not predicate(text)


def test_send_handler_does_not_append_user_message_in_continuation_branch():
    source = Path("tools/navimind_main_workspace.py").read_text(encoding="utf-8")
    root = ast.parse(source)
    send = next(node for node in ast.walk(root) if isinstance(node, ast.FunctionDef) and node.name == "_send")
    branch = next(n for n in ast.walk(send) if isinstance(n, ast.If) and isinstance(n.test, ast.Call) and isinstance(n.test.func, ast.Attribute) and n.test.func.attr == "_is_continue_current_mission_request")
    assert not any(isinstance(n, ast.Attribute) and n.attr == "user_message" for n in ast.walk(ast.Module(body=branch.body, type_ignores=[])))
    assert any(isinstance(n, ast.Return) for n in ast.walk(branch))
