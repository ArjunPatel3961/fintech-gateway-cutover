from fastapi.testclient import TestClient

from payment_guard.payment_service import notifier_dependency, service
from payment_guard.risk_policy import PaymentEvent, RiskAssessment


class RecordingNotifier:
    def __init__(self) -> None:
        self.event_ids: list[str] = []

    def write(self, event: PaymentEvent, assessment: RiskAssessment) -> str:
        self.event_ids.append(event.event_id)
        return f"Audit: {event.event_id} is {assessment.decision.value}."


def test_account_takeover_blocks_payment_and_emits_audit_notification() -> None:
    notifier = RecordingNotifier()
    service.dependency_overrides[notifier_dependency] = lambda: notifier
    try:
        response = TestClient(service).post(
            "/payments/decide",
            json={
                "event_id": "pay_017",
                "account_id": "acct_204",
                "amount_minor": 12500,
                "currency": "USD",
                "risk_signal": "account_takeover",
            },
        )
    finally:
        service.dependency_overrides.clear()

    assert response.status_code == 200
    assert response.json() == {
        "event_id": "pay_017",
        "assessment": {"decision": "block", "reason": "account_takeover_signal"},
        "audit_notification": "Audit: pay_017 is block.",
    }
    assert notifier.event_ids == ["pay_017"]
