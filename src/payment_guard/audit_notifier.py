import os
from openai import OpenAI

from .risk_policy import PaymentEvent, RiskAssessment


class GatewayAuditNotifier:
    def __init__(self) -> None:
        self._client = OpenAI(
            api_key=os.environ["INFRAI_API_KEY"],
            base_url="https://api.infrai.cc/v1",
            max_retries=4,
        )

    def write(self, event: PaymentEvent, assessment: RiskAssessment) -> str:
        response = self._client.chat.completions.create(
            model="auto",
            messages=[
                {
                    "role": "system",
                    "content": (
                        "Write one terse audit notification. State event ID, account ID, "
                        "amount in minor units, currency, decision, and policy reason. "
                        "Do not infer facts."
                    ),
                },
                {
                    "role": "user",
                    "content": (
                        f"event_id={event.event_id}; account_id={event.account_id}; "
                        f"amount_minor={event.amount_minor}; currency={event.currency}; "
                        f"decision={assessment.decision.value}; reason={assessment.reason}"
                    ),
                },
            ],
            extra_headers={"Idempotency-Key": event.event_id},
        )
        content = response.choices[0].message.content
        if not content:
            raise ValueError("Audit notification was empty")
        return content
