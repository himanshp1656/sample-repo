from __future__ import annotations
import time
from typing import List, Optional, Callable
from errors import ValidationError, NotFoundError
from validators import validate_email

CHANNELS = {"email", "sms", "push", "slack"}

# Module-level queues
_queue: list[dict] = []
_sent: list[dict] = []
_failed: list[dict] = []

# Registered handlers per channel
_handlers: dict[str, Callable] = {}


def register_handler(channel: str, handler: Callable) -> None:
    if channel not in CHANNELS:
        raise ValidationError("channel", f"must be one of {CHANNELS}")
    _handlers[channel] = handler


def build_notification(
    recipient: str,
    subject: str,
    body: str,
    channel: str = "email",
    priority: int = 5,
    metadata: dict | None = None,
) -> dict:
    if channel not in CHANNELS:
        raise ValidationError("channel", f"'{channel}' is not a valid channel")
    if not (1 <= priority <= 10):
        raise ValidationError("priority", "must be 1-10")
    if channel == "email":
        validate_email(recipient)
    return {
        "id": f"notif-{int(time.time() * 1000)}",
        "recipient": recipient,
        "subject": subject,
        "body": body,
        "channel": channel,
        "priority": priority,
        "metadata": metadata or {},
        "created_at": time.time(),
        "status": "queued",
    }


def enqueue(notification: dict) -> str:
    _queue.append(notification)
    return notification["id"]


def send_notification(notification: dict) -> bool:
    handler = _handlers.get(notification["channel"])
    if not handler:
        notification["status"] = "failed"
        notification["error"] = f"No handler for channel '{notification['channel']}'"
        _failed.append(notification)
        return False
    try:
        handler(notification)
        notification["status"] = "sent"
        notification["sent_at"] = time.time()
        _sent.append(notification)
        return True
    except Exception as e:
        notification["status"] = "failed"
        notification["error"] = str(e)
        _failed.append(notification)
        return False


def flush_queue(max_batch: int = 50) -> dict:
    batch = _queue[:max_batch]
    del _queue[:max_batch]
    success = 0
    failure = 0
    for notif in sorted(batch, key=lambda n: -n.get("priority", 5)):
        if send_notification(notif):
            success += 1
        else:
            failure += 1
    return {"processed": len(batch), "success": success, "failure": failure}


def notify_user(
    user_id: int,
    subject: str,
    body: str,
    email: str,
    channel: str = "email",
) -> str:
    notif = build_notification(
        recipient=email,
        subject=subject,
        body=body,
        channel=channel,
        metadata={"user_id": user_id},
    )
    return enqueue(notif)


def get_stats() -> dict:
    return {
        "queued": len(_queue),
        "sent": len(_sent),
        "failed": len(_failed),
        "channels": {ch: sum(1 for n in _sent if n["channel"] == ch) for ch in CHANNELS},
    }
