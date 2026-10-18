
from datetime import UTC, datetime

from cost_analysis import analyze_experiment
from error_analysis import analyze_errors
from evaluation_gates import evaluate_gates


def build_evaluation_report(
    experiment: dict,
    input_price_per_million: float,
    output_price_per_million: float,
    min_overall_accuracy: float = 0.85,
    min_category_accuracy: float = 0.90,
    max_latency_ms: float = 2000.0,
    max_invalid_json: int = 0,
) -> str:
    """Build a Markdown evaluation report from a saved experiment."""

    details = experiment.get("details", [])

    # Gate checks use the saved experiment's summary metrics.
    gate_result = evaluate_gates(
        experiment={
            **experiment,
            "details": details,
        },
        min_overall_accuracy=min_overall_accuracy,
        min_category_accuracy=min_category_accuracy,
        max_latency_ms=max_latency_ms,
        max_invalid_json=max_invalid_json,
    )

    performance = analyze_experiment(
        experiment=experiment,
        input_price_per_million=input_price_per_million,
        output_price_per_million=output_price_per_million,
    )

    error_result = analyze_errors(details)
    manifest = experiment.get("manifest", {})

    lines = [
        "# Ticket-Triage Evaluation Report",
        "",
        f"- Generated at: {datetime.now(UTC).isoformat()}",
        f"- Experiment ID: {experiment.get('id', 'unknown')}",
        f"- Prompt: {experiment.get('prompt_name', 'unnamed')}",
        f"- Prompt version: {experiment.get('prompt_version', 'v1')}",
        f"- Model: {experiment.get('model', 'unknown')}",
        f"- Tickets evaluated: {experiment.get('ticket_count', 0)}",
        "",
        "## 1. Evaluation Results",
        "",
        "| Metric | Result |",
        "|---|---:|",
        f"| Category accuracy | {experiment.get('category_accuracy', 0):.1%} |",
        f"| Order ID accuracy | {experiment.get('order_id_accuracy', 0):.1%} |",
        f"| Lookup accuracy | {experiment.get('lookup_accuracy', 0):.1%} |",
        f"| Overall field accuracy | {experiment.get('overall_field_accuracy', 0):.1%} |",
        "",
        "## 2. Cost and Performance",
        "",
        "| Metric | Result |",
        "|---|---:|",
        f"| Input tokens | {experiment.get('total_input_tokens', 0):,} |",
        f"| Output tokens | {experiment.get('total_output_tokens', 0):,} |",
        f"| Total tokens | {performance['total_tokens']:,} |",
        f"| Estimated input cost | ${performance['input_cost_usd']:.6f} USD |",
        f"| Estimated output cost | ${performance['output_cost_usd']:.6f} USD |",
        f"| Estimated total cost | ${performance['total_cost_usd']:.6f} USD |",
        f"| Estimated cost per ticket | ${performance['cost_per_ticket_usd']:.6f} USD |",
        f"| Average latency | {performance['average_latency_ms']:.2f} ms |",
        f"| Median latency | {performance['median_latency_ms']:.2f} ms |",
        f"| P95 latency | {performance['p95_latency_ms']:.2f} ms |",
        "",
        ("> Cost is an estimate based on the configured token rates. "
        "It excludes other possible provider, hosting, and tool charges."),
        "",
        "## 3. Evaluation Gates",
        "",
        f"**Gate status: {'PASS' if gate_result['approved'] else 'FAIL'}**",
        "",
        "| Gate | Actual | Threshold | Result |",
        "|---|---:|---:|---|",
    ]

    for name, check in gate_result["checks"].items():
        lines.append(
            f"| {name} | {check['actual']} | {check['threshold']} | "
            f"{'PASS' if check['passed'] else 'FAIL'} |"
        )

    if gate_result["failures"]:
        lines.extend(
            [
                "",
                "Failed gates: " + ", ".join(gate_result["failures"]),
            ]
        )
    else:
        lines.extend(["", "All configured evaluation gates passed."])

    lines.extend(
        [
            "",
            "## 4. Error Analysis",
            "",
            (f"- Tickets with at least one incorrect field: "
            f"{error_result['error_count']} / {error_result['ticket_count']}"),
            "",
            "### Results by expected category",
            "",
            ("| Category | Tickets | Category accuracy | Order ID accuracy | "
            "Lookup accuracy | Overall field accuracy |"),
            "|---|---:|---:|---:|---:|---:|",
        ]
    )

    for category, stats in sorted(
        error_result["category_summary"].items()
    ):
        lines.append(
            f"| {category} | {stats['ticket_count']} | "
            f"{stats['category_accuracy']:.1%} | "
            f"{stats['order_id_accuracy']:.1%} | "
            f"{stats['lookup_accuracy']:.1%} | "
            f"{stats['overall_field_accuracy']:.1%} |"
        )

    lines.extend(["", "### Incorrect predictions", ""])

    if error_result["errors"]:
        lines.extend(
            [
                ("| Ticket ID | Expected category | Predicted category | "
                "Parse error |"),
                "|---|---|---|---|",
            ]
        )

        for item in error_result["errors"]:
            expected_category = item.get("expected", {}).get(
                "category", "unknown"
            )
            predicted_category = item.get("predicted", {}).get(
                "category", "missing"
            )
            parse_error = item.get("parse_error") or "None"

            lines.append(
                f"| {item.get('id', '')} | {expected_category} | "
                f"{predicted_category} | {parse_error} |"
            )
    else:
        lines.append("No incorrect predictions were recorded.")

    lines.extend(
        [
            "",
            "## 5. Reproducibility",
            "",
        ]
    )

    if manifest:
        lines.extend(
            [
                f"- Manifest version: {manifest.get('manifest_version', 'unknown')}",
                f"- Prompt SHA-256: {manifest.get('prompt_hash', 'not recorded')}",
                f"- Dataset SHA-256: {manifest.get('dataset_hash', 'not recorded')}",
                f"- Evaluator version: {manifest.get('evaluator_version', 'unknown')}",
                f"- Manifest model: {manifest.get('model', 'unknown')}",
            ]
        )
    else:
        lines.append(
            "No reproducibility manifest was saved for this experiment."
        )

    lines.extend(
        [
            "",
            "## 6. Readiness Assessment",
            "",
            (f"- Configured evaluation gates: "
            f"{'passed' if gate_result['approved'] else 'not all passed'}."),
            "- Review incorrect predictions before changing prompts or thresholds.",
            "- Confirm the dataset represents real ticket categories and edge cases.",
            "- Validate category definitions and order-lookup business rules with stakeholders.",
            ("- Test security, privacy, monitoring, failure handling, and human approval "
            "before production use."),
            "- Treat this report as evaluation evidence, not as automatic deployment approval.",
            "",
            "## 7. Evaluation Configuration",
            "",
            f"- Minimum overall accuracy: {min_overall_accuracy:.1%}",
            f"- Minimum category accuracy: {min_category_accuracy:.1%}",
            f"- Maximum average latency: {max_latency_ms:.2f} ms",
            f"- Maximum invalid JSON responses: {max_invalid_json}",
            "",
        ]
    )

    return "\n".join(lines)

