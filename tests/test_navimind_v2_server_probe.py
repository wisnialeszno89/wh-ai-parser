from app.agent.bridge.agent_task_contract_v2 import validate_agent_task_v2_payload
from tools.probe_navimind_v2_server import make_probe_payload, main


def test_remote_probe_only_constructs_synthetic_v2_world():
    request = make_probe_payload()
    validate_agent_task_v2_payload(request)
    assert request["version"] == "2"
    assert request["world"]["application"] == "Okna.exe"
    assert request["world"]["window_title"] == "Okna - Start1"
    assert any(
        entity["label"] == "NOWA OFERTA"
        for entity in request["world"]["entities"]
    )
    assert "customer" not in str(request).lower()
    assert "XYZ TEST AGENT" not in str(request)
    assert any(
        action["name"].startswith("click_ent_")
        for action in request["capabilities"]["actions"]
    )


def test_remote_probe_fails_closed_without_explicit_billed_request(capsys):
    assert main([]) == 2
    captured = capsys.readouterr().out
    assert "STOP" in captured
    assert "may incur a charge" in captured
