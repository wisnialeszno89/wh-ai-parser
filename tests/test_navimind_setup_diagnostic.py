from tools.diagnose_navimind_setup import evaluate_navimind_setup


def test_diagnostic_missing_config_returns_action_without_exposing_values():
    result = evaluate_navimind_setup({}, env_file_present=False)
    assert result["V1_URL"] == "missing"
    assert result["V2_URL"] == "missing"
    assert result["NEXT_ACTION"] == "configure_navimind_deployment_origin_and_auth_in_local_env"
    assert result["V2_SERVER_DEPLOYED"] == "not_verified"


def test_valid_shared_endpoint_recognized_without_echoing_secrets():
    url = "https://navimind.example/api/agent/task"
    secret = "private-test-value-should-never-print"
    result = evaluate_navimind_setup({
        "NAVIMIND_AGENT_URL": url,
        "NAVIMIND_AGENT_SECRET": secret,
    }, env_file_present=True)
    assert result["V1_URL"] == "format_valid"
    assert result["V1_SECRET"] == "set"
    assert result["NEXT_ACTION"] == "deploy_navimind_v2_then_use_existing_shared_endpoint"
    assert url not in repr(result)
    assert secret not in repr(result)


def test_rejects_wrong_path_and_query_secrets():
    wrong = evaluate_navimind_setup({
        "NAVIMIND_AGENT_URL": "https://navimind.example/api/agent/task/v2",
        "NAVIMIND_AGENT_SECRET": "synthetic-secret",
    })
    assert wrong["V1_URL"] == "wrong_endpoint_path"
    assert wrong["NEXT_ACTION"] == "use_exact_path_api_agent_task_on_existing_deployment"

    query = evaluate_navimind_setup({
        "NAVIMIND_AGENT_URL": "https://navimind.example/api/agent/task?token=secret",
    })
    assert query["V1_URL"] == "invalid_query_or_fragment"


def test_http_localhost_accepted_but_remote_http_blocked():
    local = evaluate_navimind_setup({
        "NAVIMIND_AGENT_URL": "http://localhost:3000/api/agent/task",
    })
    assert local["V1_URL"] == "format_valid_local_only"
    remote = evaluate_navimind_setup({
        "NAVIMIND_AGENT_URL": "http://navimind.example/api/agent/task",
    })
    assert remote["V1_URL"] == "not_secure_https"
