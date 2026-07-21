"""v15g2 FIX C2a: whole-word + negation-aware intent — a policy QUESTION must
never cancel a real appointment."""
from heonix.booking.engine import detect_booking_intent


def test_book_and_cancel_detected():
    assert detect_booking_intent("I want to book an appointment") == "book"
    assert detect_booking_intent("cancel my appointment") == "cancel"


def test_policy_question_is_not_a_cancel():
    assert detect_booking_intent("what is your cancellation policy?") != "cancel"


def test_negated_cancel_resolves_to_status_not_cancel():
    # Ground truth pinned against GEN-4: "do not cancel …" → the negation
    # window catches it and the read-only STATUS branch wins (v16g3 R3-H3).
    assert detect_booking_intent("do not cancel my appointment") == "status"


def test_smalltalk_is_none():
    assert detect_booking_intent("thanks doctor!") is None
