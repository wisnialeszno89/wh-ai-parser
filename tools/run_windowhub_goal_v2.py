"""NaviMind V2 goal runner: inspect / think / verified live actions."""
import argparse
from datetime import datetime, timezone
import os
from pathlib import Path
import sys
from uuid import uuid4
from urllib.parse import urlsplit

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from app.agent.intake.task_document import read_task_document
from app.agent.learning.windowhub_demonstration import stage_of
from app.agent.learning.windowhub_training_context import (read_demonstration_experience, read_demonstration_report, windowhub_skill_knowledge)
from app.agent.perception.windowhub_semantic_world import enrich_windowhub_scene
from app.agent.reasoning.navimind_task_reasoner_v2 import (NaviMindTaskReasonerV2, NaviMindTaskReasonerV2Config)
from app.agent.runtime.computer_use_v2_action_session import ComputerUseV2ActionSession
from app.agent.runtime.windowhub_goal_v2_coordinator import execute_v2_step, enforce_v2_live_policy
from app.agent.runtime.windowhub_window_activation import activate_windowhub_workflow_window
from app.agent.runtime.windowhub_discovery_diagnostics import print_discovery_diagnostics


def parse_args(argv=None):
    parser = argparse.ArgumentParser(description="Goal-driven WindowHub with NaviMind V2")
    parser.add_argument("--goal", help="Free-form Polish or German instruction")
    parser.add_argument("--task-file", type=Path, help="Client request (.txt/.md/.pdf)")
    parser.add_argument("--mode", choices=("inspect", "think", "execute"), default="inspect")
    parser.add_argument("--reasoner", choices=("navimind", "local-ollama"), default="navimind",
                        help="Choose existing NaviMind endpoint or local Ollama without Vercel")
    parser.add_argument("--require-stage", choices=("start", "offer_document", "order_document", "position", "dimensions", "basic_parameters", "glazing", "hardware"), help="Fail closed when observed WindowHub stage is not the required stage")
    parser.add_argument("--probe-mdi", action="store_true",
                        help="Read-only native UIA ancestry of duplicate per-offer toolbar controls")
    parser.add_argument("--reuse-shared-navimind-endpoint", action="store_true", help="Use existing V1 connection for V2 only AFTER NaviMind PR #26 is deployed")
    parser.add_argument("--demo", type=Path)
    parser.add_argument("--max-actions", type=int, default=6)
    parser.add_argument("--show-window-title", action="store_true", help="Print current native title locally for unknown stages; may contain business details")
    parser.add_argument("--execute-live", action="store_true")
    parser.add_argument("--allow-local-offer-add-once", action="store_true",
                        help="One locally verified Dodaj on exact test OFR; requires --expected-offer")
    parser.add_argument("--expected-offer", help="Exact selected test OFR caption, e.g. OFR/4488-4300 <>")
    parser.add_argument("--activate-window", action="store_true",
                        help="Require authorized WindowHub focus; with both desktop flags, discovery is automatic even without this option")
    parser.add_argument("--approve-persistent", action="store_true")
    parser.add_argument("--customer-name", help="Existing client name to find by progressive native/OCR lookup")
    parser.add_argument("--customer-lookup-skill", action="store_true",
                        help="Allow one locally verified customer lookup before model decisions (execute mode only)")
    parser.add_argument("--interactive-handoff", action="store_true",
                        help="Ask salesperson for guidance with a bounded timeout, then observe and resume")
    parser.add_argument("--handoff-timeout", type=int, default=60,
                        help="Seconds for an answer, 1-300 (default 60)")
    return parser.parse_args(argv)


def audit_start_action_read_only(prepared, scene):
    """Prove that a model's Start1 action can be resolved locally; never click."""
    entities = {
        item["ref"]: item for item in prepared.request_payload["world"]["entities"]
    }
    choices = [
        item for item in prepared.request_payload["capabilities"]["actions"]
        if item["name"].startswith("click_ent_")
        and entities.get(item["target_ref"], {}).get("label") == "NOWA OFERTA"
    ]
    if len(choices) != 1:
        print("START_NEW_OFFER_GUARD=NOT_UNIQUELY_EXPOSED")
        return
    action = choices[0]
    synthetic = {
        "version": "2",
        "task_id": prepared.request_payload["task_id"],
        "decision": "act",
        "rationale": "Local read-only validation of the observed New Offer capability.",
        "confidence": 0.99,
        "observation_request": None,
        "action": {
            "name": action["name"],
            "target_ref": action["target_ref"],
            "value": None,
            "expected_postcondition": {"kind": "scene_changed"},
            "requires_confirmation": action["requires_confirmation"],
        },
        "completion": None,
        "requires_manual_review": False,
    }
    try:
        resolved = prepared.resolve_action_decision(synthetic)
        enforce_v2_live_policy(scene, resolved)
    except (ValueError, KeyError) as exc:
        print("START_NEW_OFFER_GUARD=BLOCKED")
        print("START_NEW_OFFER_REASON=" + str(exc))
        return
    print("START_NEW_OFFER_GUARD=PASS")
    print("START_NEW_OFFER_CHECK=V2 protocol and local UIA identity only; no click, no model request")




def request_human_resume(loop, *, timeout_seconds=60):
    """Ask once, time out, then resume only after fresh WindowHub observation."""
    from app.agent.runtime.goal_task_supervisor import timed_salesperson_prompt
    response = timed_salesperson_prompt(
        "Agent potrzebuje wskazowki. Pokaz lub popraw cos w WindowHub, "
        "nastepnie wpisz 'tak', aby kontynuowal.",
        timeout_seconds=timeout_seconds,
    )
    if response is None:
        from app.agent.runtime.goal_task_supervisor import (
            TaskItem, TaskLedger, append_unresolved_issues,
        )
        # No business subtask graph exists yet, so fail closed rather than
        # assume the current user request may be safely skipped.
        ledger = TaskLedger({"active_goal": TaskItem("active_goal", required=True)})
        ledger.unresolved("active_goal", reason="operator_timeout_dependency_unresolved")
        try:
            print("HANDOFF_AUDIT_RECORDS=" + str(append_unresolved_issues(ledger)))
        except OSError:
            print("HANDOFF_AUDIT_RECORDS=unavailable")
        print("HANDOFF_RESULT=timeout")
        print("HANDOFF_UNRESOLVED=requires_goal_dependency_review")
        return False
    if response.strip().casefold() not in {"tak", "t"}:
        print("HANDOFF_RESULT=declined")
        return False
    focused, info = activate_windowhub_workflow_window()
    print("HANDOFF_REFOCUS=" + info)
    if not focused:
        print("HANDOFF_RESULT=environment_unavailable")
        return False
    new_scene = loop.observe_scene()
    if stage_of(new_scene) is None:
        print("HANDOFF_RESULT=no_verified_windowhub_scene")
        return False
    print("HANDOFF_RESULT=accepted_reobserved")
    return True

def run_goal(loop, *, goal, reasoner, mode, max_actions, experience=(),
             approved_persistent=False, show_window_title=False,
             customer_lookup_name=None, interactive_handoff=False,
             handoff_timeout=60, require_stage=None,
             local_offer_add_once=False, expected_offer=None):
    session = ComputerUseV2ActionSession()
    from app.agent.runtime.goal_progress_memory import ProgressMemory
    progress = ProgressMemory()
    task_id = "wh-" + uuid4().hex[:16]
    feedback = list(experience)
    customer_lookup_attempted = False
    for revision in range(max_actions if mode == "execute" else 1):
        from app.agent.runtime.windowhub_mdi_native_probe import enrich_native_mdi_document_scope
        scene = enrich_windowhub_scene(
            enrich_native_mdi_document_scope(loop.observe_scene())
        )
        stage = stage_of(scene)
        if stage is None:
            print("STOP: WindowHub must be the foreground application.")
            return 4
        if stage == "order_document" and mode != "inspect":
            print("STOP: ZLC document recognized, but its action semantics are not verified.")
            print("AI_REQUEST_SENT=False")
            print("INPUT_EXECUTED=False")
            return 4
        if require_stage is not None and stage != require_stage:
            print("STOP: required stage " + require_stage + ", actual stage " + str(stage))
            print("AI_REQUEST_SENT=False")
            return 4
        from app.agent.runtime.active_panel_context import (
            safe_panel_diagnostics, panel_model_context,
        )
        panel_state = safe_panel_diagnostics(scene)
        feedback.append(panel_model_context(scene))
        print("PANEL_CONTEXT=" + str(panel_state["context_status"]))
        print("PANEL_SELECTED_TABS=" + str(panel_state["selected_tab_count"]))
        print("PANEL_FOCUSED_CONTROLS=" + str(panel_state["focused_control_count"]))
        print("PANEL_NAMED_CONTAINERS=" + str(panel_state["named_container_count"]))
        print("PANEL_SCOPED_CONTROLS=" + str(panel_state["controls_with_ancestry"]))
        if stage == "offer_document":
            from app.agent.runtime.active_document_scope import (
                duplicate_document_action_status,
            )
            add_scope = duplicate_document_action_status(scene, label="Dodaj")
            print("MDI_DOCUMENT_TAB_STATUS=" + add_scope["selected_document_status"])
            print("MDI_DODAJ_BUTTONS=" + str(add_scope["observed"]))
            print("MDI_DODAJ_ACTIVE_SCOPED=" + str(add_scope["active_scope_proven"]))
            print("MDI_DODAJ_UNRESOLVED=" + str(add_scope["unresolved_scope"]))
            print("MDI_DODAJ_SAFE_TARGET=" + str(add_scope["safe_unique_active_target"]))
        world_state = progress.observe(scene, stage=stage)
        print("WORLD_STAGE=" + str(world_state["stage"]))
        print("WORLD_CHANGED=" + str(world_state["world_changed_since_last"]))
        print("WORLD_VISIBLE_CONTROLS=" + str(world_state["visible_semantic_controls"]))
        feedback.append({
            "source": "local_world_state",
            "observed_stage": stage,
            "world_changed": world_state["world_changed_since_last"],
            "visible_semantic_controls": world_state["visible_semantic_controls"],
        })
        if (mode == "execute" and customer_lookup_name
                and stage == "document_properties"
                and not customer_lookup_attempted):
            # Native DevExpress lookup is not represented by a generic model
            # edit affordance. Execute one specifically approved local skill,
            # then hand the verified result + fresh scene to NaviMind V2.
            customer_lookup_attempted = True
            from tools.run_windowhub_top_trans_single_window_mission import (
                customer_selected, progressive_customer_selection,
            )
            if customer_selected(scene, customer_lookup_name):
                verified, outcome = True, "CUSTOMER_ALREADY_SELECTED"
            else:
                verified, outcome = progressive_customer_selection(
                    loop, scene, customer_lookup_name,
                )
            print("CUSTOMER_SKILL_STATUS=" + outcome)
            feedback.append({
                "source": "windowhub_local_customer_skill",
                "action_type": "select_existing_customer",
                "from_stage": "document_properties",
                "to_stage": stage_of(enrich_windowhub_scene(loop.observe_scene())) or "unknown",
                "verified": verified,
                "result": outcome,
            })
            if not verified:
                print("STOP: customer selection requires additional visual/native verification.")
                return 6
            if revision + 1 >= max_actions:
                print("STOP: customer skill verified but model action budget exhausted.")
                return 4
            continue
        if show_window_title and stage == "windowhub_unmapped":
            print("UNMAPPED_FOREGROUND_TITLE=" + repr(scene.observation.state.active_window_title))
            print("TITLE_NOTE=local diagnostic only; review for business identifiers before sharing")
        prepared = session.prepare_cycle(
            scene, task_id=task_id, session_id=task_id, goal=goal,
            world_revision=revision + 1, cycle=revision,
            max_cycles=max_actions, knowledge=windowhub_skill_knowledge(),
            experience=feedback[-12:],
            observed_at=datetime.now(timezone.utc).isoformat(),
        )
        actions = prepared.request_payload["capabilities"]["actions"]
        # Authoritative stage from locally observed Okna.exe foreground.
        # V2 world title may be redacted or normalized for privacy, and is
        # never a reliable substitute for the local stage classifier.
        if reasoner is not None:
            prepared.request_payload["metadata"]["verified_windowhub_stage"] = stage
        if stage == "offer_document" and reasoner is not None:
            from app.agent.runtime.active_document_scope import unique_active_document_control
            scoped_add = unique_active_document_control(scene, label="Dodaj")
            eligible = []
            if scoped_add is not None:
                for item in actions:
                    try:
                        matched = prepared.snapshot.reference_map.resolve(
                            item["target_ref"], task_id=task_id,
                            world_revision=revision + 1,
                        )
                    except (ValueError, KeyError, TypeError):
                        continue
                    if matched is scoped_add and item["name"].startswith("click_ent_"):
                        eligible.append(item["target_ref"])
            prepared.request_payload["metadata"]["verified_active_offer_add_refs"] = eligible[:1]
            print("OFFER_ADD_MODEL_ELIGIBLE=" + str(len(eligible) == 1))
        print(f"CYCLE={revision+1} STAGE={stage} ACTION_CAPABILITIES={len(actions)}")
        if mode == "inspect":
            from app.agent.runtime.goal_affordance_ranking import affordance_relevance
            from app.agent.runtime.active_panel_context import observe_panel_context
            ranked_hits = []
            for item in actions:
                if item.get("target_ref") is None:
                    continue
                # The capability's target ref is deliberately opaque. Inspect
                # diagnostic relevance against the *same local* reference map.
                target = item["target_ref"]
                try:
                    element = prepared.snapshot.reference_map.resolve(
                        target, task_id=task_id, world_revision=revision + 1
                    )
                except (ValueError, KeyError):
                    continue
                if (element.metadata or {}).get("source") == "windows_desktop_window":
                    # Other top-level windows are navigation context, not
                    # a business-control goal match.
                    continue
                ranking = affordance_relevance(
                    {
                        "entity_ref": target,
                        "description": item.get("description", ""),
                    },
                    goal=goal,
                    reference_map=prepared.snapshot.reference_map,
                    task_id=task_id,
                    world_revision=revision + 1,
                    panel_context=observe_panel_context(scene),
                )
                ranked_hits.append((item, ranking))
            positive = sum(rank["direct"] > 0 for _, rank in ranked_hits)
            print("GOAL_RELEVANT_ACTIONS=" + str(positive))
            print("GOAL_CONTEXTUAL_ACTIONS=" + str(sum(
                rank["context"] > 0 for _, rank in ranked_hits
            )))
            for entry, rank in sorted(
                ranked_hits, key=lambda pair: -pair[1]["score"]
            )[:5]:
                print(
                    "GOAL_CANDIDATE="
                    + str(rank["label"])[:80]
                    + " DIRECT=" + str(rank["direct"])
                    + " PANEL=" + str(rank["context"])
                    + " TOTAL=" + str(rank["score"])
                )
            if positive == 0:
                print("GOAL_CONTEXT=NO_DIRECT_SEMANTIC_MATCH_INSPECT_NAVIGATION_BEFORE_ACTION")
            else:
                print("GOAL_CONTEXT=RELATED_CONTROLS_PRESENT_BUT_ACTION_UNVERIFIED")
            # Show the agent's *actual* current knowledge of the two critical
            # size fields, never generic customer or document text.
            if stage == "dimensions":
                from app.agent.runtime.windowhub_dimension_replace import current_dimension
                for field in ("width_1", "height_1"):
                    observed = current_dimension(scene, field)
                    print("CURRENT_DIMENSION_" + field.upper() + "=" + (
                        repr(observed) if observed is not None else "UNOBSERVABLE"
                    ))
            entities = {e["ref"]: e for e in prepared.request_payload["world"]["entities"]}
            for item in actions[:24]:
                target = entities.get(item["target_ref"]) if item["target_ref"] else None
                print(f"CAPABILITY={item['name']} LABEL={(target or {}).get('label')}")
            if stage == "start":
                audit_start_action_read_only(prepared, scene)
            print("INSPECT_ONLY: local capability inventory; no reasoning model was called and no UI action was performed.")
            return 0
        response = reasoner.reason(prepared.request_payload)
        if response is None:
            print("STOP: NAVIMIND_ERROR=" + str(reasoner.last_error))
            return 5
        print(f"REASONER_DECISION={response['decision']} CONFIDENCE={response['confidence']}")
        print(f"REASONER_REASON={str(response['rationale'])[:300]}")
        if response["decision"] == "done":
            # The editor stage alone is not proof that an arbitrary task is
            # finished. Never mark a document/customer/catalog operation done
            # solely because the native window is titled Modyfikator.
            print("MODEL_DONE_REQUESTED=True")
            print("TASK_COMPLETION_VERIFIED=False")
            print("STOP: goal-specific business postconditions require independent verification.")
            return 4
        if response["decision"] != "act" or response["confidence"] < .80:
            print("STOP: reasoner cannot yet choose a confident executable action.")
            if (mode == "execute" and interactive_handoff
                    and request_human_resume(loop, timeout_seconds=handoff_timeout)):
                feedback.append({
                    "source": "salesperson_guidance",
                    "result": "human_updated_screen_and_approved_resume",
                    "verified": False,
                })
                continue
            return 4
        try:
            action = prepared.resolve_action_decision(response)
        except (ValueError, KeyError) as exc:
            print("STOP: invalid proposed action: " + str(exc))
            return 5
        print("PROPOSED_ACTION=" + action.action.name + " TARGET=" + str(getattr(action.action.target, "label", None)))
        if mode == "think":
            # A model-selected capability is only a proposal. The same
            # deterministic local policy and postcondition contract used for
            # execution must accept it before we call it an eligible plan.
            from app.agent.runtime.windowhub_goal_v2_coordinator import (
                enforce_v2_live_policy, verified_v2_outcome,
            )
            try:
                enforce_v2_live_policy(
                    scene, action,
                    approved_persistent=approved_persistent,
                )
                expectation = verified_v2_outcome(
                    action, baseline_scene=scene,
                )
            except (ValueError, RuntimeError) as exc:
                print("THINK_LOCAL_POLICY=BLOCKED")
                print("THINK_BLOCK_REASON=" + type(exc).__name__ + ":" + str(exc)[:120])
                print("THINK_ONLY: nothing executed.")
                return 4
            print("THINK_LOCAL_POLICY=PASS")
            print("THINK_EXPECTED_WINDOW=" + str(expectation.expected_window_title))
            print("THINK_EXPECTED_SCENE_CHANGE=" + str(expectation.require_scene_change))
            print("THINK_ONLY: nothing executed.")
            return 0
        if local_offer_add_once:
            # Explicit one-step permission never extends to any other GUI action.
            from app.agent.runtime.active_document_scope import unique_active_document_control
            selected_control = unique_active_document_control(scene, label="Dodaj")
            actual_offer = (scene.observation.state.active_window_title or "").strip()
            if not (
                stage == "offer_document"
                and actual_offer == "Okna - " + expected_offer
                and action.action.name == "click_screen_element"
                and getattr(action.action.target, "label", "").strip().casefold() == "dodaj"
                and selected_control is not None
                and (selected_control.metadata or {}).get("uia_runtime_id")
                    == getattr(action.action.target, "uia_runtime_id", None)
            ):
                print("STOP: LOCAL_OFFER_ADD_GUARD=BLOCKED")
                return 4
            print("LOCAL_OFFER_ADD_GUARD=PASS")
        allowed, progress_reason = progress.allow_action(action.action, scene, stage=stage)
        print("PROGRESS_ACTION_POLICY=" + progress_reason)
        if not allowed:
            print("RECOVERY=blocked_identical_action_on_unchanged_world")
            feedback.append({
                "source": "local_recovery",
                "verified": False,
                "blocked_action": action.action.name,
                "reason": "same_action_same_world_choose_different_method",
                "stage": stage,
            })
            # Ask the model for a different, currently available capability.
            # This still consumes the finite action budget and performs no UI
            # input in the blocked cycle.
            continue
        try:
            execute_v2_step(loop, scene, action, approved_persistent=approved_persistent)
        except (ValueError, RuntimeError) as exc:
            print("ACTION_OUTCOME=blocked_or_unverified")
            feedback.append({
                "source": "local_recovery",
                "verified": False,
                "failed_action": action.action.name,
                "reason": type(exc).__name__,
                "stage": stage,
                "next_step": "reobserve_and_choose_an_evidence_based_alternative",
            })
            # One failed UI operation is not yet enough to assume nothing
            # changed: the following cycle will re-observe the desktop.
            # Never send the identical action twice on unchanged evidence.
            if (mode == "execute" and interactive_handoff
                    and request_human_resume(loop, timeout_seconds=handoff_timeout)):
                feedback.append({
                    "source": "salesperson_guidance",
                    "result": "human_updated_screen_and_approved_resume",
                    "verified": False,
                })
            continue
        print("ACTION_VERIFIED=" + action.action.name)
        after = loop.observe_scene()
        feedback.append({
            "source": "local_verified_action",
            "from_stage": stage,
            "to_stage": stage_of(after) or "unknown",
            "action_type": action.action.name,
            "verified": True,
            "world_change_detected": progress.feedback(after, stage=stage_of(after))["observable_change"],
        })
    print("STOP: action budget exhausted; goal completion not assumed.")
    return 4


def shared_endpoint_v2_config() -> NaviMindTaskReasonerV2Config:
    """Use existing V1 URL explicitly after the shared V2 route is deployed."""
    from dotenv import load_dotenv
    load_dotenv()
    url = os.getenv("NAVIMIND_AGENT_URL", "").strip()
    parts = urlsplit(url)
    if not url:
        raise ValueError(
            "NAVIMIND_AGENT_URL is not configured. Run python tools/diagnose_navimind_setup.py."
        )
    if (
        parts.path.rstrip("/") != "/api/agent/task"
        or not parts.hostname
        or parts.username is not None
        or parts.password is not None
        or parts.query or parts.fragment
        or not (
            parts.scheme == "https"
            or parts.scheme == "http" and parts.hostname in {"localhost", "127.0.0.1"}
        )
    ):
        raise ValueError("NAVIMIND_AGENT_URL must be a secure shared /api/agent/task endpoint.")
    secret = os.getenv("NAVIMIND_AGENT_SECRET", "").strip()
    if not secret:
        raise ValueError("NAVIMIND_AGENT_SECRET is required for the shared V2 connection.")
    return NaviMindTaskReasonerV2Config(
        url=url, secret=secret, timeout_seconds=20,
    )


def main(argv=None):
    args = parse_args(argv)
    if os.name != "nt" or not 1 <= args.max_actions <= 20 or not 1 <= args.handoff_timeout <= 300:
        return 2
    try:
        file_text = read_task_document(args.task_file) if args.task_file else ""
    except (ValueError, RuntimeError, OSError) as exc:
        print("STOP: document intake: " + str(exc))
        return 2
    goal = "\n".join(
        part for part in (args.goal or "", "Client request: " + file_text if file_text else "")
        if part.strip()
    )
    if not goal.strip() or len(goal) > 16000:
        print("STOP: --goal or --task-file required; empty or oversized request.")
        return 2
    if args.probe_mdi and args.mode != "inspect":
        print("STOP: --probe-mdi is read-only and requires --mode inspect.")
        return 2
    if args.customer_lookup_skill and (
        args.mode != "execute" or not isinstance(args.customer_name, str)
        or not args.customer_name.strip() or len(args.customer_name.strip()) > 100
    ):
        print("STOP: customer lookup skill requires execute mode and a valid --customer-name.")
        return 2
    desktop_authorized = all(
        os.getenv(k) == "1" for k in ("WH_REAL_WINDOWHUB", "COMPUTER_USE_LIVE")
    )
    if args.activate_window and not desktop_authorized:
        print("STOP: --activate-window needs both explicit desktop authorization flags.")
        return 2
    if args.mode != "execute" and desktop_authorized:
        # With desktop access already authorized, the agent locates and focuses
        # the existing WindowHub window even when PowerShell is foreground.
        # Focus transfer is the only desktop mutation in inspect mode.
        focused, info = activate_windowhub_workflow_window()
        print("WINDOWHUB_AUTO_DISCOVERY=" + info)
        if not focused:
            print_discovery_diagnostics()
            # Inspection may still continue if the *actual current foreground*
            # belongs to Okna.exe. Do not activate an unknown title, and do
            # not extend this fallback to model thinking or live execution.
            from app.agent.runtime.windowhub_foreground_inspection import (
                inspect_current_windowhub_foreground,
                activate_unique_windowhub_for_inspection,
            )
            if args.mode != "inspect":
                return 3
            if not inspect_current_windowhub_foreground():
                recovered, diagnostic = activate_unique_windowhub_for_inspection()
                print("WINDOWHUB_INSPECT_RECOVERY=" + diagnostic)
                if not recovered:
                    return 3
            print("WINDOWHUB_UNMAPPED_FOREGROUND=READ_ONLY_OBSERVATION")

    if args.mode == "execute":
        if not args.execute_live or any(
            os.getenv(k) != "1" for k in ("WH_REAL_WINDOWHUB", "COMPUTER_USE_LIVE")
        ):
            print("STOP: --execute-live and both explicit desktop flags required.")
            return 2
        ok, info = activate_windowhub_workflow_window()
        print("WINDOWHUB_ACTIVATION=" + info)
        if not ok:
            print_discovery_diagnostics()
            return 3
    try:
        experience = read_demonstration_experience(args.demo) if args.demo else ()
        if args.mode == "inspect":
            reasoner = None
        elif args.reasoner == "local-ollama":
            from app.agent.reasoning.local_ollama_task_reasoner_v2 import LocalOllamaTaskReasonerV2
            reasoner = LocalOllamaTaskReasonerV2()
        else:
            reasoner = (
                NaviMindTaskReasonerV2(
                    config=shared_endpoint_v2_config(),
                ) if args.reuse_shared_navimind_endpoint
                else NaviMindTaskReasonerV2()
            )
    except (RuntimeError, ValueError, OSError) as exc:
        print("STOP: NaviMind V2 configuration or demo error: " + str(exc))
        if args.mode != "inspect":
            from tools.diagnose_navimind_setup import evaluate_navimind_setup
            from dotenv import load_dotenv
            load_dotenv()
            report = evaluate_navimind_setup({
                k: os.getenv(k, "") for k in (
                    "NAVIMIND_AGENT_URL", "NAVIMIND_AGENT_SECRET",
                    "NAVIMIND_AGENT_V2_URL", "NAVIMIND_AGENT_V2_SECRET",
                )
            })
            print("SAFE_CONNECTION_DIAGNOSTIC=" + ",".join(
                k + ":" + report[k] for k in (
                    "V1_URL", "V1_SECRET", "V2_URL", "V2_SECRET", "NEXT_ACTION",
                )
            ))
        if "NAVIMIND_AGENT_V2_URL" in str(exc):
            from dotenv import load_dotenv
            load_dotenv()
            print("V1_NAVIMIND_URL_CONFIGURED=" + str(bool(os.getenv("NAVIMIND_AGENT_URL", "").strip())))
            print("V2_NAVIMIND_URL_CONFIGURED=False")
            print("NAVI_V2_DEPLOYMENT_STATUS=check_server_separately")
            print("NAVI_V2_ROUTE=/api/agent/task (shared URL, protocol version is in JSON body)")
            print("ACTION=Configure NAVIMIND_AGENT_V2_URL and matching NAVIMIND_AGENT_V2_SECRET locally; never commit secrets.")
            print("SECURITY=Do not paste secrets or production customer payloads into logs.")
        return 5
    if args.reasoner == "local-ollama" and args.reuse_shared_navimind_endpoint:
        print("STOP: cannot combine local Ollama with shared NaviMind endpoint.")
        return 2
    if args.allow_local_offer_add_once and not (
        args.reasoner == "local-ollama" and args.mode == "execute"
        and args.execute_live and args.max_actions == 1
        and args.require_stage == "offer_document"
        and not args.approve_persistent and not args.interactive_handoff
        and not args.customer_lookup_skill and not args.task_file
        and isinstance(args.expected_offer, str)
        and args.expected_offer == "OFR/4488-4300 <>"
    ):
        print("STOP: single-action Ollama offer test requires exact scoped flags and offer caption.")
        return 2
    if args.reasoner == "local-ollama" and args.mode == "execute" and not args.allow_local_offer_add_once:
        print("STOP: local Ollama provider is THINK-only except explicit one-step test offer Add.")
        return 2
    if args.reuse_shared_navimind_endpoint and args.mode != "inspect":
        print("NAVIMIND_ENDPOINT=shared /api/agent/task (V2 payload)")
        print("REQUIREMENT=Target server must support protocol version 2; check server deployment independently.")
    if args.demo:
        report = read_demonstration_report(args.demo)
        print("DEMO_RECORDED_EVENTS=" + str(report["record_count"]))
        print("DEMO_STAGE_SEQUENCE=" + " -> ".join(report["stage_sequence"]))
        print("DEMO_FORM_STATE_EVENTS=" + str(report["within_stage_changes"]))
        print("DEMO_UNMAPPED_TRANSITIONS=" + str(report["unmapped_transitions"]))
        print("DEMO_EXPERIENCE_ITEMS=" + str(len(experience)))
        print("DEMO_MODIFIER_VERIFIED=" + str(report["modifier_observed"]))
    if args.mode != "inspect":
        if args.reasoner == "local-ollama":
            print("REASONER=LOCAL_OLLAMA_LOOPBACK")
            print("NOTICE: semantic goal and scene are sent only to localhost Ollama; no Vercel.")
            if args.mode == "think":
                print("THINK_ONLY: no local AI decisions will be executed.")
            else:
                print("LOCAL_EXECUTE_LIMIT=one verified Add on exact test offer")
        else:
            print("NOTICE: goal and semantic scene are transmitted to configured NaviMind.")
    if args.probe_mdi:
        from app.agent.runtime.windows_desktop_agent_control_loop import (
            create_windows_desktop_agent_control_loop,
        )
        from app.agent.runtime.windowhub_mdi_native_probe import inspect_native_mdi_button_ancestry
        scene = enrich_windowhub_scene(
            create_windows_desktop_agent_control_loop().observe_scene()
        )
        if stage_of(scene) != "offer_document":
            print("MDI_PROBE=not_offer_document")
            return 4
        report = inspect_native_mdi_button_ancestry(scene)
        print("MDI_PROBE_STATUS=" + report.get("status", "unknown"))
        print("MDI_PROBE_SELECTED=" + report.get("selected_tab_status", "unknown"))
        print("MDI_PROBE_BUTTONS=" + str(report.get("observed_dodaj", 0)))
        print("MDI_PROBE_UIA_UNIQUE=" + str(report.get("uia_matched_uniquely", 0)))
        print("MDI_PROBE_NATIVE_EXACT_MATCH=" + str(report.get("with_exact_mdi_ancestor", 0)))
        print("MDI_PROBE_NO_NATIVE_MATCH=" + str(report.get("with_no_mdi_ancestor", 0)))
        print("MDI_PROBE_NATIVE_AMBIGUOUS=" + str(report.get("with_ambiguous_mdi_ancestor", 0)))
        for index, item in enumerate(report.get("buttons", ())):
            print("MDI_PROBE_BUTTON_" + str(index) + "_UIA_MATCH=" + str(item["uia_match_count"]))
            print("MDI_PROBE_BUTTON_" + str(index) + "_NATIVE_PARENTS=" + str(item["native_ancestor_windows"]))
            print("MDI_PROBE_BUTTON_" + str(index) + "_MDI_CAPTION_MATCH=" + str(item["mdi_title_match_count"]))
            print("MDI_PROBE_BUTTON_" + str(index) + "_MDI_CHILD_CATEGORY=" + str(item["mdi_child_classification"]))
            print("MDI_PROBE_BUTTON_" + str(index) + "_STRUCTURE=" + repr(item["structural_chain"][:8]))
        print("MDI_PROBE_ACTIONS_EXECUTED=False")
        return 0
    try:
        from app.agent.runtime.windows_desktop_agent_control_loop import create_windows_desktop_agent_control_loop
        return run_goal(
            create_windows_desktop_agent_control_loop(),
            goal=goal, reasoner=reasoner, mode=args.mode,
            max_actions=args.max_actions, experience=experience,
            approved_persistent=args.approve_persistent,
            show_window_title=args.show_window_title,
            customer_lookup_name=(args.customer_name.strip()
                                  if args.customer_lookup_skill else None),
            interactive_handoff=args.interactive_handoff,
            handoff_timeout=args.handoff_timeout,
            require_stage=args.require_stage,
        )
    except Exception as exc:
        print("STOP: " + type(exc).__name__ + ": " + str(exc)[:200])
        return 7


if __name__ == "__main__":
    raise SystemExit(main())
