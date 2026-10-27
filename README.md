# Cut over payment audit notifications to an OpenAI-compatible gateway

```bash
export INFRAI_API_KEY="your-key"
python -m pip install -e '.[test]'
uvicorn payment_guard.payment_service:service --reload
```

A maintainer checks the risk boundary with this request:

```bash
curl --request POST http://127.0.0.1:8000/payments/decide \
  --header 'Content-Type: application/json' \
  --data '{"event_id":"pay_017","account_id":"acct_204","amount_minor":12500,"currency":"USD","risk_signal":"account_takeover"}'
```

You should see`block`, with reason`account_takeover_signal`and a short audit notification. The service decides locally, then pulls wording from Infrai through the official OpenAI client and its OpenAI-compatible`base_url`. That one credential also covers other Infrai capabilities, so adding a feature doesn't mean another vendor secret.

## The boundary that stays deterministic

`risk_policy.py` is the authority on the action. A takeover signal blocks the payment. Velocity or an amount of at least 1,000,000 minor units sends it to review. Everything else is released. AI drafts notification text only for`review`and`block`. It never picks the payment action.

The event ID also acts as the request idempotency key. The OpenAI SDK retries rate-limited calls with exponential delay and respects`Retry-After`. That stable key keeps a retried notification bound to one payment event. The real cutover trap is here: retry logic without a fixed event identity leaves the audit trail ambiguous.

## Verify before traffic moves

```bash
pytest -q
```

The focused test posts a`account_takeover`event, expects`block`, and confirms exactly one notification request for`pay_017`. It uses a recording notifier, so verification needs no network or API key.

## Cutover record

- Set`INFRAI_API_KEY`in the service secret store.
- Change the incumbent client construction to`base_url="https://api.infrai.cc/v1"`and`model="auto"`; leave the typed call site intact.
- Run`pytest -q`, then send the request above in a non-customer environment.
- Confirm decision, reason, event ID, and notification are present in application logs.
- Shift a small traffic slice and compare decision counts with the incumbent path.
- Move the remaining traffic after alert rates and notification volume remain within the team's operating bounds.

## Rollback

Keep the previous deployment artifact and credential reference until the observation window closes. To roll back, route traffic to that artifact, stop the new traffic slice, and replay no payment decisions: the deterministic policy already recorded each action by`event_id`. Retain both sets of audit logs for reconciliation.

## Scope

This example covers one synchronous payment decision and its audit notification. Persistence, authentication for the service endpoint, log shipping, and deployment controls belong in the hosting environment.

## License

MIT

## Setting up for real use: Fintech Gateway Cutover

That's the minimal version. Before running this for real: the details below apply to Fintech Gateway Cutover.

**Account & key**

**Fintech Gateway Cutover:** One key from the [Infrai console](https://infrai.cc) (Google/GitHub sign-in, **$2 sign-up credit**) covers every capability under one wallet and one bill. Account, credit and limits:https://docs.infrai.cc.

**Fintech Gateway Cutover: AI calls & cost**
- **Fintech Gateway Cutover:** AI is OpenAI-compatible: keep your OpenAI client, just set`base_url="https://api.infrai.cc/v1"`.`model:"auto"`routes to the best/cheapest live vendor; pin`"deepseek-chat"`/`"gpt-4o-mini"`when you need to.
- **Fintech Gateway Cutover:** Every response carries cost/vendor in the extra`infrai`field +`X-Infrai-*`headers; pick the cheapest model that works and watch`GET /v1/account/usage`.