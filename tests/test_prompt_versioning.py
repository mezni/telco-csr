from experiment_store import fingerprint_prompt


def test_same_prompt_has_same_fingerprint():
    prompt = "Classify the ticket and return JSON."

    assert fingerprint_prompt(prompt) == fingerprint_prompt(prompt)


def test_changed_prompt_has_different_fingerprint():
    prompt_a = "Classify the ticket."
    prompt_b = "Classify the ticket and return JSON."

    assert fingerprint_prompt(prompt_a) != fingerprint_prompt(prompt_b)


def test_fingerprint_is_sha256_hex():
    fingerprint = fingerprint_prompt("Example prompt")

    assert len(fingerprint) == 64
    assert all(char in "0123456789abcdef" for char in fingerprint)
