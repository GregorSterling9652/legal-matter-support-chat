from src.support_chat import MatterMessage, classify_message


def test_deadline_follow_up_is_prioritised_for_near_due_matter() -> None:
    message = MatterMessage("acct", "m-1", "Any update on my case?", deadline_days=2)
    assert classify_message(message) == "deadline_follow_up"


def test_signed_document_has_delivery_event() -> None:
    message = MatterMessage("acct", "m-2", "The signed document is ready")
    assert classify_message(message) == "signed_document_delivery"
