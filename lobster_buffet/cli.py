from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

from . import core


def emit(result: dict[str, Any]) -> None:
    print(json.dumps(result, indent=2, sort_keys=True))


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="lobster-buffet")
    subparsers = parser.add_subparsers(dest="group", required=True)

    command = subparsers.add_parser("command")
    command_subparsers = command.add_subparsers(dest="action", required=True)

    command_list = command_subparsers.add_parser("list")
    command_list.add_argument("--detail", choices=["summary", "full"], default="summary")
    command_list.add_argument("--include-deprecated", action="store_true")

    command_describe = command_subparsers.add_parser("describe")
    command_describe.add_argument("--name", required=True)

    operation = subparsers.add_parser("operation")
    operation_subparsers = operation.add_subparsers(dest="action", required=True)

    operation_plan = operation_subparsers.add_parser("plan")
    operation_plan.add_argument("--name", required=True)
    operation_plan.add_argument("--actor-ref", default="local-actor-ref")
    operation_plan.add_argument(
        "--surface",
        choices=["discord", "tui", "api", "cron", "unknown"],
        default="unknown",
    )

    project = subparsers.add_parser("project")
    project_subparsers = project.add_subparsers(dest="action", required=True)

    project_inspect = project_subparsers.add_parser("inspect")
    project_inspect.add_argument(
        "--adapter-fixture",
        default=None,
        help="Adapter fixture path. Overrides adapter config.",
    )
    project_inspect.add_argument(
        "--adapter-config",
        default=None,
        help=f"Adapter config path. Defaults to ${core.ADAPTER_CONFIG_ENV} when set.",
    )

    git = subparsers.add_parser("git")
    git_subparsers = git.add_subparsers(dest="action", required=True)

    git_workflow_guard = git_subparsers.add_parser("workflow-guard")
    git_workflow_guard.add_argument("--requested-action", choices=core.GIT_WORKFLOW_ACTIONS, default="lifecycle_apply")
    git_workflow_guard.add_argument("--detail", choices=["summary", "full"], default="summary")
    git_workflow_guard.add_argument(
        "--adapter-fixture",
        default=None,
        help="Adapter fixture path. Overrides adapter config.",
    )
    git_workflow_guard.add_argument(
        "--adapter-config",
        default=None,
        help=f"Adapter config path. Defaults to ${core.ADAPTER_CONFIG_ENV} when set.",
    )

    for action in core.LIFECYCLE_ACTIONS:
        lifecycle = project_subparsers.add_parser(action)
        lifecycle.add_argument("--project-name", required=True)
        lifecycle.add_argument("--mode", choices=["plan", "apply"], default="plan")
        lifecycle.add_argument("--reason", default=None)
        lifecycle.add_argument(
            "--adapter-fixture",
            default=None,
            help="Adapter fixture path. Overrides adapter config in apply mode.",
        )
        lifecycle.add_argument(
            "--adapter-config",
            default=None,
            help=f"Adapter config path. Defaults to ${core.ADAPTER_CONFIG_ENV} when set in apply mode.",
        )

    incident = subparsers.add_parser("incident")
    incident_subparsers = incident.add_subparsers(dest="action", required=True)

    incident_list = incident_subparsers.add_parser("list")
    incident_list.add_argument("--status", choices=["active", "stale", "closed", "all"], default="active")
    incident_list.add_argument("--detail", choices=["summary", "full"], default="summary")
    incident_list.add_argument(
        "--adapter-fixture",
        default=None,
        help="Adapter fixture path. Overrides adapter config.",
    )
    incident_list.add_argument(
        "--adapter-config",
        default=None,
        help=f"Adapter config path. Defaults to ${core.ADAPTER_CONFIG_ENV} when set.",
    )

    alignment = subparsers.add_parser("alignment")
    alignment_subparsers = alignment.add_subparsers(dest="action", required=True)

    alignment_scan = alignment_subparsers.add_parser("scan")
    alignment_scan.add_argument("--source", choices=["project", "channel", "explicit"], default="project")
    alignment_scan.add_argument("--project", default=None)
    alignment_scan.add_argument("--label", default=None)
    alignment_scan.add_argument("--current-plan-summary", default=None)
    alignment_scan.add_argument("--detail", choices=["summary", "full"], default="summary")
    alignment_scan.add_argument(
        "--adapter-fixture",
        default=None,
        help="Adapter fixture path. Overrides adapter config.",
    )
    alignment_scan.add_argument(
        "--adapter-config",
        default=None,
        help=f"Adapter config path. Defaults to ${core.ADAPTER_CONFIG_ENV} when set.",
    )

    review = subparsers.add_parser("review")
    review_subparsers = review.add_subparsers(dest="action", required=True)

    review_list = review_subparsers.add_parser("list")
    review_list.add_argument("--status", choices=["active", "blocked", "closed", "all"], default="active")
    review_list.add_argument("--detail", choices=["summary", "full"], default="summary")
    review_list.add_argument(
        "--adapter-fixture",
        default=None,
        help="Adapter fixture path. Overrides adapter config.",
    )
    review_list.add_argument(
        "--adapter-config",
        default=None,
        help=f"Adapter config path. Defaults to ${core.ADAPTER_CONFIG_ENV} when set.",
    )
    review_update = review_subparsers.add_parser("update")
    review_update.add_argument("--review-id", required=True)
    review_update.add_argument("--kind", choices=core.REVIEW_UPDATE_KINDS, required=True)
    review_update.add_argument("--summary", required=True)
    review_update.add_argument("--mode", choices=["plan", "apply"], default="plan")
    review_update.add_argument("--apply-gate", choices=core.REVIEW_APPLY_GATES, default=None)
    review_update.add_argument("--reason", default=None)
    review_update.add_argument(
        "--adapter-fixture",
        default=None,
        help="Adapter fixture path. Overrides adapter config.",
    )
    review_update.add_argument(
        "--adapter-config",
        default=None,
        help=f"Adapter config path. Defaults to ${core.ADAPTER_CONFIG_ENV} when set.",
    )

    heartbeat = subparsers.add_parser("heartbeat")
    heartbeat_subparsers = heartbeat.add_subparsers(dest="action", required=True)

    heartbeat_packet = heartbeat_subparsers.add_parser("packet")
    heartbeat_packet.add_argument("--detail", choices=["summary", "full"], default="summary")
    heartbeat_packet.add_argument(
        "--adapter-fixture",
        default=None,
        help="Adapter fixture path. Overrides adapter config.",
    )
    heartbeat_packet.add_argument(
        "--adapter-config",
        default=None,
        help=f"Adapter config path. Defaults to ${core.ADAPTER_CONFIG_ENV} when set.",
    )
    heartbeat_check = heartbeat_subparsers.add_parser("check")
    heartbeat_check.add_argument("--scope", choices=["project", "incident", "review", "all"], default="all")
    heartbeat_check.add_argument("--detail", choices=["summary", "full"], default="summary")
    heartbeat_check.add_argument(
        "--adapter-fixture",
        default=None,
        help="Adapter fixture path. Overrides adapter config.",
    )
    heartbeat_check.add_argument(
        "--adapter-config",
        default=None,
        help=f"Adapter config path. Defaults to ${core.ADAPTER_CONFIG_ENV} when set.",
    )

    return parser


def run(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)

    try:
        if args.group == "command" and args.action == "list":
            emit(core.command_list(include_deprecated=args.include_deprecated))
            return 0

        if args.group == "command" and args.action == "describe":
            emit(core.command_describe(args.name))
            return 0

        if args.group == "operation" and args.action == "plan":
            emit(core.operation_plan(args.name, actor_ref=args.actor_ref, surface=args.surface))
            return 0

        if args.group == "project" and args.action == "inspect":
            emit(
                core.project_inspect(
                    adapter_fixture_path=Path(args.adapter_fixture) if args.adapter_fixture else None,
                    adapter_config_path=Path(args.adapter_config) if args.adapter_config else None,
                )
            )
            return 0

        if args.group == "project" and args.action in core.LIFECYCLE_ACTIONS:
            emit(
                core.project_lifecycle(
                    f"project.{args.action}",
                    args.project_name,
                    mode=args.mode,
                    reason=args.reason,
                    adapter_fixture_path=Path(args.adapter_fixture) if args.adapter_fixture else None,
                    adapter_config_path=Path(args.adapter_config) if args.adapter_config else None,
                )
            )
            return 0

        if args.group == "git" and args.action == "workflow-guard":
            emit(
                core.git_workflow_guard(
                    requested_action=args.requested_action,
                    detail=args.detail,
                    adapter_fixture_path=Path(args.adapter_fixture) if args.adapter_fixture else None,
                    adapter_config_path=Path(args.adapter_config) if args.adapter_config else None,
                )
            )
            return 0

        if args.group == "incident" and args.action == "list":
            emit(
                core.incident_list(
                    status=args.status,
                    detail=args.detail,
                    adapter_fixture_path=Path(args.adapter_fixture) if args.adapter_fixture else None,
                    adapter_config_path=Path(args.adapter_config) if args.adapter_config else None,
                )
            )
            return 0

        if args.group == "alignment" and args.action == "scan":
            emit(
                core.alignment_scan(
                    source=args.source,
                    project=args.project,
                    label=args.label,
                    current_plan_summary=args.current_plan_summary,
                    detail=args.detail,
                    adapter_fixture_path=Path(args.adapter_fixture) if args.adapter_fixture else None,
                    adapter_config_path=Path(args.adapter_config) if args.adapter_config else None,
                )
            )
            return 0

        if args.group == "review" and args.action == "list":
            emit(
                core.review_list(
                    status=args.status,
                    detail=args.detail,
                    adapter_fixture_path=Path(args.adapter_fixture) if args.adapter_fixture else None,
                    adapter_config_path=Path(args.adapter_config) if args.adapter_config else None,
                )
            )
            return 0

        if args.group == "review" and args.action == "update":
            emit(
                core.review_update_preview(
                    review_id=args.review_id,
                    kind=args.kind,
                    summary=args.summary,
                    mode=args.mode,
                    apply_gate=args.apply_gate,
                    reason=args.reason,
                    adapter_fixture_path=Path(args.adapter_fixture) if args.adapter_fixture else None,
                    adapter_config_path=Path(args.adapter_config) if args.adapter_config else None,
                )
            )
            return 0

        if args.group == "heartbeat" and args.action == "packet":
            emit(
                core.heartbeat_packet(
                    detail=args.detail,
                    adapter_fixture_path=Path(args.adapter_fixture) if args.adapter_fixture else None,
                    adapter_config_path=Path(args.adapter_config) if args.adapter_config else None,
                )
            )
            return 0

        if args.group == "heartbeat" and args.action == "check":
            emit(
                core.heartbeat_check(
                    scope=args.scope,
                    detail=args.detail,
                    adapter_fixture_path=Path(args.adapter_fixture) if args.adapter_fixture else None,
                    adapter_config_path=Path(args.adapter_config) if args.adapter_config else None,
                )
            )
            return 0

    except core.OperationError as error:
        emit(error.to_result())
        return 1

    parser.error("unsupported command")
    return 2


def main() -> None:
    raise SystemExit(run())


if __name__ == "__main__":
    main()
