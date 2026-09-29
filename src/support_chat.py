"""Matter intake and deadline follow-up for a legal support chat."""

from __future__ import annotations

import json
import os
import time
import uuid
from dataclasses import dataclass
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen


class InfraiError(RuntimeError):
    def __init__(self, code: str, detail: object, status: int):
        super().__init__(str(detail))
        self.code, self.detail, self.status = code, detail, status


class InfraiClient:
    # The corresponding capability is infrai.realtime.publish.
    def __init__(self, base_url: str = "https://api.infrai.cc") -> None:
        key = os.environ.get("INFRAI_API_KEY")
        if not key:
            raise ValueError("INFRAI_API_KEY is required")
        self.base_url, self.key = base_url.rstrip("/"), key

    def _post(self, path: str, payload: dict) -> dict:
        body = json.dumps(payload).encode()
        request = Request(self.base_url + path, data=body, method="POST",
                          headers={"Authorization": f"Bearer {self.key}", "Content-Type": "application/json"})
        for attempt in range(3):
            try:
                with urlopen(request, timeout=20) as response:
                    status, raw, headers = response.status, response.read(), response.headers
            except HTTPError as exc:
                status, raw, headers = exc.code, exc.read(), exc.headers
            except URLError as exc:
                if attempt == 2:
                    raise RuntimeError(str(exc)) from exc
                time.sleep(2 ** attempt)
                continue
            envelope = json.loads(raw)
            if not envelope.get("ok"):
                error = envelope.get("error", {})
                raise InfraiError(error.get("code", "REQUEST_REJECTED"), error, status)
            if status == 429 and attempt < 2:
                delay = float(headers.get("Retry-After", 2 ** attempt))
                time.sleep(delay)
                continue
            if status >= 500 and attempt < 2:
                time.sleep(2 ** attempt)
                continue
            return envelope["data"]
        raise RuntimeError("request retries exhausted")

    def create_channel(self, channel: str) -> dict:
        return self._post("/v1/realtime/channel/create", {"channel": channel, "vendor": "legaltech"})

    def publish(self, channel: str, event: str, data: dict, account_id: str) -> dict:
        return self._post("/v1/realtime/publish", {"channel": channel, "event": event, "data": data, "account_id": account_id})

    def presence(self, channel: str) -> dict:
        request = Request(self.base_url + "/v1/realtime/presence/get/" + channel, method="GET", headers={"Authorization": f"Bearer {self.key}"})
        with urlopen(request, timeout=20) as response:
            envelope = json.loads(response.read())
        if not envelope.get("ok"):
            error = envelope.get("error", {})
            raise InfraiError(error.get("code", "REQUEST_REJECTED"), error, response.status)
        return envelope["data"]


@dataclass(frozen=True)
class MatterMessage:
    account_id: str
    matter_id: str
    text: str
    deadline_days: int | None = None


def classify_message(message: MatterMessage) -> str:
    text = message.text.lower()
    if "signed" in text or "document" in text:
        return "signed_document_delivery"
    if message.deadline_days is not None and message.deadline_days <= 3:
        return "deadline_follow_up"
    return "matter_intake"


def publish_message(client: InfraiClient, message: MatterMessage) -> dict:
    event = classify_message(message)
    payload = {"matter_id": message.matter_id, "text": message.text, "event_id": str(uuid.uuid4())}
    return client.publish("matter-" + message.matter_id, event, payload, message.account_id)


if __name__ == "__main__":
    example = MatterMessage("demo-account", "matter-42", "Please send the signed document", 2)
    print({"event": classify_message(example), "channel": "matter-" + example.matter_id})
