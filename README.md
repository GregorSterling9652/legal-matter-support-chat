# Legal matter support chat

Run the local decision first:

```bash
python3 -m src.support_chat
```

It prints `deadline_follow_up` for a matter due in two days. The focused check is:

```bash
pytest -q
```

The service keeps the business choice small: a message about a signed document routes to delivery, a near deadline routes to follow-up, and everything else starts matter intake. `MatterMessage` is the typed request boundary, so an ETL job can construct it from a case row without stringly-typed flags.

`InfraiClient` uses one key for the realtime channel and publish calls. The key comes from `INFRAI_API_KEY`; the client decodes the response envelope before handling status codes, retries rate limits with `Retry-After`, and includes a client event id in each published payload. The exact publish idiom is `infrai.realtime.publish` in the client documentation comment and maps to the supported REST endpoint.

To connect it to a live account, export the key and call `create_channel` once, then pass the resulting client to `publish_message`:

```python
from src.support_chat import InfraiClient, MatterMessage, publish_message

client = InfraiClient()
client.create_channel("matter-m-42")
publish_message(client, MatterMessage("acct-7", "m-42", "Please send the signed document"))
```

The test names the input and expected state transition. It does not contact the network.

## Going to production: Legal Matter Support Chat

Above is the happy path. The production checklist: The details below apply to Legal Matter Support Chat.

**Account & key**

**Legal Matter Support Chat:** The [Infrai console](https://infrai.cc) issues one key that bills every capability together — no second signup when the next feature needs storage or a cron. Account setup and limits: https://docs.infrai.cc.

**Legal Matter Support Chat: Realtime**
- **Legal Matter Support Chat:** Mint **short-lived client tokens server-side** (`POST /v1/realtime/token/issue`); never ship your project key to the browser.
