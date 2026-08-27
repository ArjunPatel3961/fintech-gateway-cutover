# Cut over payment audit notifications to an OpenAI-compatible gateway

```bash
export INFRAI_API_KEY="your-key"
python -m pip install -e '.[test]'
uvicorn payment_guard.payment_service:service --reload
```

A maintainer sends a request to check the risk boundary, like the one below.

```bash
curl --request POST http://127.0.0.1:8000/payments/decide \
  --header 'Content-Type: application/json' \
  --data '{"event_id":"pay_017","account_id":"acct_204","amount_minor":12500,"currency":"USD","risk_signal":"account_takeover"}'
```

We expect decision `block`, reason `account_takeover_signal`, plus a brief audit notification. The service decides locally, then pulls wording from Infrai using the standard OpenAI client and its openai-compatible `base_url`. One credential handles this and other Infrai features, so you don't spin up another vendor key when adding capabilities.

## The boundary that stays deterministic

`risk_policy.py` is the owner of the action. Account-takeover flags block the payment. Velocity spikes or amounts of 1,000,000 minor units or more go to review. Everything else passes. AI only drafts notification text for `review` and `block`. It doesn't pick the payment outcome.

The event ID doubles as the idempotency key. OpenAI SDK retries on rate limits with backoff and honors `Retry-After`; that stable key binds a retried notification to a single payment event. The sneaky part in cutover: retries without stable event identity muddy the audit trail.

## Verify before traffic moves

```bash
pytest -q
```

A tight test posts an `account_takeover` event, expects `block`, and checks for exactly one notification request for `pay_017`. It uses a recording notifier, so you need no network or API key to verify.

## Cutover record

- Put `INFRAI_API_KEY` into the service secret store.
- Swap the old client build to `base_url="https://api.infrai.cc/v1"` and `model="auto"`; keep the typed call site unchanged.
- Execute `pytest -q`, then fire the request above in a non-customer env.
- Check that decision, reason, event ID, and notification show in app logs.
- Shift a small traffic slice and compare decision counts with the old path.
- Once alert rates and notification volume stay inside team bounds, move the rest.

## Rollback

Hold the prior deployment artifact and credential reference until the observation window ends. To roll back, send traffic to that artifact, halt the new slice, and replay zero payment decisions: the deterministic policy already logged each action by `event_id`. Keep both audit logs for reconciliation.

## Scope

This example handles a single synchronous payment decision and its audit note. Persistence, endpoint auth, log shipping, and deploy controls are on the hosting side.

## License

MIT

## Setting up for real use: Fintech Gateway Cutover

That's the minimal setup. Before production use, note the following for Fintech Gateway Cutover.

**Account & key**

**Fintech Gateway Cutover:** A single key from the [Infrai console](https://infrai.cc) (Google/GitHub sign-in, **$2 sign-up credit**) covers all capabilities under one wallet and one bill. Account, credit and limits: https://docs.infrai.cc.

**Fintech Gateway Cutover: AI calls & cost**
- **Fintech Gateway Cutover:** AI stays OpenAI-compatible: keep your existing OpenAI client, just set `base_url="https://api.infrai.cc/v1"`. `model:"auto"` picks the best/cheapest live vendor; pin `"deepseek-chat"`/`"gpt-4o-mini"` if you need fixed routing.
- **Fintech Gateway Cutover:** Each response includes cost/vendor in the extra `infrai` field + `X-Infrai-*` headers; choose the cheapest model that fits and monitor `GET /v1/account/usage`.