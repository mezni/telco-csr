# cli.py
import argparse
import json
from typing import Any

from agent import process_ticket
from approval import decide_approval
from audit_log import list_events


def print_json(data: dict[str, Any] | list[dict[str, Any]]) -> None:
    """Print structured data in a readable format."""
    print(json.dumps(data, indent=2, ensure_ascii=False))


def handle_triage(args: argparse.Namespace) -> int:
    recommendation = process_ticket(
        ticket=args.ticket,
        model=args.model,
        ticket_id=args.ticket_id,
    )

    print("\n=== Classification recommendation ===")
    print_json(recommendation)

    if recommendation["status"] != "pending_approval":
        print("\nManual review is required. No approval was recorded.")
        return 1

    answer = input("\nApprove this recommendation? [y/n]: ").strip().lower()

    if answer not in {"y", "yes", "n", "no"}:
        print("Invalid choice. No approval was recorded.")
        return 2

    decision = "approve" if answer in {"y", "yes"} else "reject"
    reviewer = input("Reviewer identifier: ").strip()

    if not reviewer:
        print("Reviewer identifier is required. No decision was recorded.")
        return 2

    final_result = decide_approval(
        recommendation,
        decision=decision,
        reviewer=reviewer,
    )

    print("\n=== Final decision ===")
    print_json(final_result)
    return 0


def handle_history(args: argparse.Namespace) -> int:
    events = list_events(
        ticket_id=args.ticket_id,
        limit=args.limit,
    )

    print("\n=== Audit history ===")
    print_json(events)
    return 0


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="ticket-triage",
        description="Classify support tickets and review recommendations.",
    )

    subparsers = parser.add_subparsers(
        dest="command",
        required=True,
    )

    triage_parser = subparsers.add_parser(
        "triage",
        help="Classify a ticket and request human approval.",
    )
    triage_parser.add_argument(
        "--ticket",
        required=True,
        help="Customer support ticket text.",
    )
    triage_parser.add_argument(
        "--model",
        required=True,
        help="Model identifier configured for your inference service.",
    )
    triage_parser.add_argument(
        "--ticket-id",
        default=None,
        help="Existing ticket ID; generated if omitted.",
    )
    triage_parser.set_defaults(handler=handle_triage)

    history_parser = subparsers.add_parser(
        "history",
        help="View persisted audit events.",
    )
    history_parser.add_argument(
        "--ticket-id",
        default=None,
        help="Filter events by ticket ID.",
    )
    history_parser.add_argument(
        "--limit",
        type=int,
        default=20,
        help="Maximum number of events to display.",
    )
    history_parser.set_defaults(handler=handle_history)

    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)

    if hasattr(args, "limit") and args.limit < 1:
        parser.error("--limit must be at least 1")

    return args.handler(args)


if __name__ == "__main__":
    raise SystemExit(main())
