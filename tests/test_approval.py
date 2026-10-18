import pytest

from approval import decide_approval

PENDING_RESULT = {
    "status": "pending_approval",
    "ticket": "My order #4821 has not arrived.",
    "classification": {
        "category": "order_status",
        "order_id": 4821,
        "needs_order_lookup": True,
    },
    "decision": "awaiting_human_approval",
    "error": None,
    "attempt_count": 1,
}


def test_approval_records_human_decision():
    result = decide_approval(
        PENDING_RESULT,
        decision="approve",
        reviewer="reviewer-1",
    )

    assert result["status"] == "approved"
    assert result["decision"] == "approve"
    assert result["reviewer"] == "reviewer-1"
    assert result["classification"] == PENDING_RESULT["classification"]


def test_rejection_records_human_decision():
    result = decide_approval(
        PENDING_RESULT,
        decision="reject",
        reviewer="reviewer-1",
    )

    assert result["status"] == "rejected"
    assert result["decision"] == "reject"


def test_original_recommendation_is_not_mutated():
    original = dict(PENDING_RESULT)

    decide_approval(
        PENDING_RESULT,
        decision="approve",
        reviewer="reviewer-1",
    )

    assert PENDING_RESULT == original
    assert PENDING_RESULT["status"] == "pending_approval"


def test_invalid_decision_is_rejected():
    with pytest.raises(ValueError, match="Decision must be one of"):
        decide_approval(
            PENDING_RESULT,
            decision="maybe",
            reviewer="reviewer-1",
        )


def test_empty_reviewer_is_rejected():
    with pytest.raises(ValueError, match="Reviewer"):
        decide_approval(
            PENDING_RESULT,
            decision="approve",
            reviewer=" ",
        )


def test_failed_classification_cannot_be_approved():
    failed_result = {
        "status": "needs_review",
        "classification": None,
    }

    with pytest.raises(
        ValueError,
        match="Only recommendations pending approval",
    ):
        decide_approval(
            failed_result,
            decision="approve",
            reviewer="reviewer-1",
        )


def test_missing_classification_is_rejected():
    invalid_result = {
        "status": "pending_approval",
        "classification": None,
    }

    with pytest.raises(
        ValueError,
        match="valid classification is required",
    ):
        decide_approval(
            invalid_result,
            decision="approve",
            reviewer="reviewer-1",
        )
