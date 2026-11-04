from types import SimpleNamespace

from tools.live_windowhub_position_mission import parse_args, verified_action


def test_mission_cli():
    args = parse_args(['--quantity', '2', '--width', '1200', '--height', '1400', '--execute-live'])
    assert args.quantity == 2
    assert args.width == 1200
    assert args.height == 1400
    assert args.execute_live is True


def test_unverified_action_fails_closed():
    assert verified_action(SimpleNamespace(success=False, last_execution_result=None)) is False
    assert verified_action(SimpleNamespace(success=True, last_execution_result=None)) is False
