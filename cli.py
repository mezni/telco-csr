import argparse
import json
import logging
from typing import Sequence

from agent import process_ticket
from approval import decide_approval
from audit_log import list_events
from metrics import build_metrics_report


def build_parser() -> argparse.ArgumentParser:
    """Build the command-line interface."""
    parser = argparse.ArgumentParser(
        description="AI-assisted support ticket triage.",
    )

    subparsers = parser.add_subparsers(
        dest="command",
        required=True,
    )

    # Triage a ticket and request human approval.
    triage_parser = subparsers.add_parser(
        "triage",
        help="Classify a ticket and request human approval.",
    )
    triage_parser.add_argument(
        "--ticket",
        required=True,
        help="Support ticket text.",
    )
    triage_parser.add_argument(
        "--model",
        required=True,
        help="Model identifier to use for classification.",
    )
    triage_parser.add_argument(
        "--ticket-id",
        help="Optional ticket identifier.",
    )

    # View the audit history.
    history_parser = subparsers.add_parser(
        "history",
        help="Display audit events.",
    )
    history_parser.add_argument(
        "--ticket-id",
        help="Filter events by ticket identifier.",
    )
    history_parser.add_argument(
        "--limit",
        type=int,
        default=20,
        help="Maximum number of events to display (default: 20).",
    )

    # View operational metrics.
    subparsers.add_parser(
        "metrics",
        help="Display operational metrics.",
    )

    return parser


def run_triage(args: argparse.Namespace) -> int:
    """Classify a ticket and collect the human decision."""
    result = process_ticket(
        ticket=args.ticket,
        model=args.model,
        ticket_id=args.ticket_id,
    )

    print(json.dumps(result, indent=2))

    # Do not request approval when classification failed.
    if result["status"] != "pending_approval":
        return 1

    while True:
        decision = input("Approve this recommendation? [y/n]: ").strip().lower()

        if decision in {"y", "yes"}:
            decision = "approve"
            break

        if decision in {"n", "no"}:
            decision = "reject"
            break

        print("Invalid choice. Enter y or n.")

    reviewer = input("Reviewer identifier: ").strip()

    if not reviewer:
        print("Error: reviewer identifier cannot be empty.")
        return 2

    final_result = decide_approval(
        agent_result=result,
        decision=decision,
        reviewer=reviewer,
    )

    print("\nFinal decision:")
    print(json.dumps(final_result, indent=2))

    return 0


def run_history(args: argparse.Namespace) -> int:
    """Display recent audit events."""
    if args.limit < 1:
        print("Error: --limit must be at least 1.")
        return 2

    events = list_events(
        ticket_id=args.ticket_id,
        limit=args.limit,
    )

    print(json.dumps(events, indent=2))
    return 0


def run_metrics() -> int:
    """Display the operational metrics report."""
    report = build_metrics_report()
    print(json.dumps(report, indent=2))
    return 0


def main(argv: Sequence[str] | None = None) -> int:
    """CLI entry point."""
    logging.basicConfig(
        level=logging.INFO,
        format="%(message)s",
    )

    parser = build_parser()
    args = parser.parse_args(argv)

    if args.command == "triage":
        return run_triage(args)

    if args.command == "history":
        return run_history(args)

    if args.command == "metrics":
        return run_metrics()

    parser.error(f"Unknown command: {args.command}")
    return 2


if __name__ == "__main__":
    raise SystemExit(main())
