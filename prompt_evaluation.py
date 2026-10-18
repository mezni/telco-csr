import json
from pathlib import Path

from dataset_validation import validate_dataset
from evaluator import score_prediction, summarize_scores
from llm_service import run_inference

DATASET_PATH = (
    Path(__file__).resolve().parent
    / "data"
    / "eval_tickets.json"
)


def load_dataset() -> list[dict]:
    dataset = json.loads(DATASET_PATH.read_text(encoding="utf-8"))

    errors = validate_dataset(dataset)
    if errors:
        raise ValueError(
            "Evaluation dataset is invalid:\n- " + "\n- ".join(errors)
        )

    return dataset

def run_prompt_evaluation(
    prompt: str,
    model: str,
    tickets: list[dict] | None = None,
) -> dict:
    dataset = tickets if tickets is not None else load_dataset()

    errors = validate_dataset(dataset)
    if errors:
        raise ValueError(
            "Evaluation dataset is invalid:\n- " + "\n- ".join(errors)
        )


    dataset = tickets if tickets is not None else load_dataset()
    scores = []
    latencies = []
    input_tokens = 0
    output_tokens = 0
    details = []

    for item in dataset:
        run = run_inference(
            ticket=item["ticket"],
            system_prompt=prompt,
            model=model,
        )

        latencies.append(run["latency_ms"])
        input_tokens += run["input_tokens"] or 0
        output_tokens += run["output_tokens"] or 0

        try:
            predicted = json.loads(run["response"])
            field_scores = score_prediction(
                item["expected"],
                predicted,
            )
            parse_error = None
        except (json.JSONDecodeError, TypeError):
            predicted = {}
            field_scores = {
                "category_correct": False,
                "order_id_correct": False,
                "lookup_correct": False,
            }
            parse_error = "Invalid JSON response"

        scores.append(field_scores)
        details.append({
            "id": item["id"],
            "ticket": item["ticket"],
            "expected": item["expected"],
            "predicted": predicted,
            "scores": field_scores,
            "latency_ms": run["latency_ms"],
            "total_tokens": run["total_tokens"],
            "parse_error": parse_error,
        })

    return {
        "model": model,
        "ticket_count": len(dataset),
        "summary": summarize_scores(scores),
        "average_latency_ms": (
            sum(latencies) / len(latencies) if latencies else 0.0
        ),
        "total_input_tokens": input_tokens,
        "total_output_tokens": output_tokens,
        "details": details,
    }

