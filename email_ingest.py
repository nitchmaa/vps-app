from __future__ import annotations

import email
import imaplib
import os
import re
from datetime import date
from email.message import Message

from db import init_db, upsert_daily_balance


# ===== Configuration (via environment variables) =====
EMAIL_FROM = os.getenv("EMAIL_FROM", "alerts@example.com")
EMAIL_SUBJECT_KEYWORD = os.getenv("EMAIL_SUBJECT_KEYWORD", "Daily Balance")

BALANCE_REGEX = re.compile(
    r"\$\s*(\d{1,3}(?:,\d{3})*(?:\.\d{2})|\d+(?:\.\d{2})?)"
)


def require_env(name: str) -> str:
    value = os.getenv(name, "").strip()
    if not value:
        raise RuntimeError(f"Missing required environment variable: {name}")
    return value


def get_imap_config() -> tuple[str, int, str, str, str]:
    host = require_env("EMAIL_HOST")
    port_raw = os.getenv("EMAIL_PORT", "993").strip()
    username = require_env("EMAIL_USER")
    password = require_env("EMAIL_PASSWORD")
    mailbox = os.getenv("EMAIL_MAILBOX", "INBOX").strip() or "INBOX"
    return host, int(port_raw), username, password, mailbox


def decode_payload(part: Message) -> str:
    payload = part.get_payload(decode=True)
    if payload is None:
        return ""
    charset = part.get_content_charset() or "utf-8"
    return payload.decode(charset, errors="replace")


def extract_text_from_message(msg: Message) -> str:
    if msg.is_multipart():
        chunks: list[str] = []
        for part in msg.walk():
            if part.get_content_type() in {"text/plain", "text/html"}:
                chunks.append(decode_payload(part))
        return "\n".join(chunks)
    return decode_payload(msg)


def find_latest_matching_message(
    client: imaplib.IMAP4_SSL, sender: str, subject_keyword: str
) -> bytes:
    status, data = client.search(
        None,
        "FROM",
        f'"{sender}"',
        "SUBJECT",
        f'"{subject_keyword}"',
    )
    if status != "OK":
        raise RuntimeError("Failed to search mailbox")

    message_ids = data[0].split()
    if not message_ids:
        raise RuntimeError("No matching emails found")

    return message_ids[-1]


def extract_balance(email_body: str) -> float:
    match = BALANCE_REGEX.search(email_body)
    if not match:
        raise RuntimeError("Could not find a dollar balance in the email body")
    return float(match.group(1).replace(",", ""))


def main() -> None:
    if EMAIL_FROM == "alerts@example.com":
        raise RuntimeError(
            "Set EMAIL_FROM to your real bank sender address before running."
        )

    host, port, username, password, mailbox = get_imap_config()

    with imaplib.IMAP4_SSL(host, port) as client:
        client.login(username, password)
        status, _ = client.select(mailbox, readonly=True)
        if status != "OK":
            raise RuntimeError(f"Unable to open mailbox: {mailbox}")

        message_id = find_latest_matching_message(
            client, EMAIL_FROM, EMAIL_SUBJECT_KEYWORD
        )
        status, data = client.fetch(message_id, "(RFC822)")
        if status != "OK" or not data or data[0] is None:
            raise RuntimeError("Failed to fetch matched email")

        raw_email = data[0][1]
        if not isinstance(raw_email, (bytes, bytearray)):
            raise RuntimeError("Unexpected email payload from IMAP server")

        msg = email.message_from_bytes(raw_email)
        email_body = extract_text_from_message(msg)
        balance = extract_balance(email_body)

    today = date.today().isoformat()
    init_db()
    upsert_daily_balance(today, balance)

    print(f"Stored balance for {today}: ${balance:,.2f}")


if __name__ == "__main__":
    main()
