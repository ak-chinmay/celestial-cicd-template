#!/usr/bin/env python3
"""Minimal Telegram validation and notification client with bounded errors."""

from __future__ import annotations

import argparse
import json
import os
import re
import urllib.error
import urllib.parse
import urllib.request


TOKEN_RE = re.compile(r"^[0-9]{6,12}:[A-Za-z0-9_-]{20,}$")
CHAT_RE = re.compile(r"^-?[0-9]{1,20}$")


class NotificationError(RuntimeError):
    pass


def _credentials() -> tuple[str, str]:
    token = os.environ.get("TELEGRAM_BOT_TOKEN", "")
    chat_id = os.environ.get("TELEGRAM_CHAT_ID", "")
    if not TOKEN_RE.fullmatch(token) or not CHAT_RE.fullmatch(chat_id):
        raise NotificationError("notification-credentials-invalid")
    return token, chat_id


def _request(method: str, values: dict[str, str] | None = None) -> dict[str, object]:
    token, _ = _credentials()
    data = None if values is None else urllib.parse.urlencode(values).encode("utf-8")
    request = urllib.request.Request(
        f"https://api.telegram.org/bot{token}/{method}", data=data, method="POST"
    )
    try:
        with urllib.request.urlopen(request, timeout=10) as response:
            payload = json.load(response)
    except (OSError, urllib.error.URLError, json.JSONDecodeError) as exc:
        raise NotificationError("notification-provider-unavailable") from exc
    if not isinstance(payload, dict) or payload.get("ok") is not True:
        raise NotificationError("notification-provider-rejected")
    return payload


def check() -> None:
    _, chat_id = _credentials()
    _request("getMe")
    _request("getChat", {"chat_id": chat_id})


def notify(message: str) -> None:
    if not 1 <= len(message) <= 1000 or "\x00" in message:
        raise NotificationError("notification-message-invalid")
    _, chat_id = _credentials()
    _request("sendMessage", {"chat_id": chat_id, "text": message})


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument("--check", action="store_true")
    group.add_argument("--message")
    args = parser.parse_args()
    try:
        if args.check:
            check()
        else:
            notify(args.message)
    except NotificationError as exc:
        print(str(exc))
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
