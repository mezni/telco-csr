import hashlib
import json

EVALUATOR_VERSION = "1.0.0"


def fingerprint_text(value: str) -> str:
    """Return the SHA-256 fingerprint of text."""
    return hashlib.sha256(value.encode("utf-8")).hexdigest()


def fingerprint_dataset(dataset: list[dict]) -> str:
    """Fingerprint dataset content independently of JSON formatting."""
    canonical_json = json.dumps(
        dataset,
        sort_keys=True,
        separators=(",", ":"),
        ensure_ascii=False,
    )
    return fingerprint_text(canonical_json)


def build_manifest(
    prompt: str,
    model: str,
    dataset: list[dict],
) -> dict:
    """Build metadata identifying the inputs to an evaluation."""
    return {
        "manifest_version": "1.0",
        "prompt_hash": fingerprint_text(prompt),
        "dataset_hash": fingerprint_dataset(dataset),
        "model": model,
        "evaluator_version": EVALUATOR_VERSION,
        "ticket_count": len(dataset),
    }
