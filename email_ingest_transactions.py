from __future__ import annotations

import email
import imaplib
import os
import re
from datetime import datetime
from email.message import Message

from db_transactions import init_transactions_table, upsert_transaction

# ===== Configuration (env vars) =====
EMAIL_FROM = os.getenv("EMAIL_FROM", "").strip()
EMAIL_SUBJECT_KEYWORD = os.getenv("TRANSACTION_SUBJECT_KEYWORD", "").strip()

# Regex patterns
AMOUNT_REGEX = re.compile(r"\$([\d]+\.\d{2})")
DATE_REGEX = re.compile(r"Date:\s*(\d{2}/\d{2}/\d{2})")
MERCHANT_REGEX = re.compile(r"To:\s*([A-Z0-9 \-]+)")
ACCOUNT_LAST4_REGEX = re.compile(r"ending in\s*(\d{4})", re.IGNORECASE)


def require_env(name: str) -> str:
    val = os.getenv(name, "").strip()
    if not val:
        raise RuntimeError(f"Missing required environment variable: {name}")
    return val


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
    client: imaplib.IMAP4_SSL,
    sender: str,
    subject_keyword: str,
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
    ids = data[0].split()
    if not ids:
        raise RuntimeError("No matching transaction emails found")
    return ids[-1]


def parse_transaction(email_body: str) -> tuple[str, float, str, str | None]:
    # Date
    date_match = DATE_REGEX.search(email_body)
    if not date_match:
        raise RuntimeError("Could not find transaction date")
    dt_str = date_match.group(1)
    dt = datetime.strptime(dt_str, "%m/%d/%y").date().isoformat()

    # Amount
    amt_match = AMOUNT_REGEX.search(email_body)
    if not amt_match:
        raise RuntimeError("Could not find amount")
    amount = float(amt_match.group(1))

    # Merchant
    merch_match = MERCHANT_REGEX.search(email_body)
    if not merch_match:
        raise RuntimeError("Could not find merchant")
    merchant = merch_match.group(1).strip()

    # Account last 4
    acct_match = ACCOUNT_LAST4_REGEX.search(email_body)
    last4 = acct_match.group(1) if acct_match else None

    # Direction is always debit for now
    direction = "debit"

    return dt, amount, direction, merchant, last4


def main() -> None:
    # Validate config
    if not EMAIL_FROM or not EMAIL_SUBJECT_KEYWORD:
        raise RuntimeError(
            "Please set EMAIL_FROM and TRANSACTION_SUBJECT_KEYWORD environment variables"
        )

    host, port, username, password, mailbox = get_imap_config()

    with imaplib.IMAP4_SSL(host, port) as client:
        client.login(username, password)
        status, _ = client.select(mailbox, readonly=True)
        if status != "OK":
            raise RuntimeError(f"Unable to open mailbox: {mailbox}")

        msg_id = find_latest_matching_message(
            client, EMAIL_FROM, EMAIL_SUBJECT_KEYWORD
        )
        status, data = client.fetch(msg_id, "(RFC822)")
        if status != "OK" or not data or data[0] is None:
            raise RuntimeError("Failed to fetch transaction email")

        raw_email = data[0][1]
        msg = email.message_from_bytes(raw_email)
        body_text = extract_text_from_message(msg)

        (
            transaction_date,
            amount,
            direction,
            merchant,
            account_last4,
        ) = parse_transaction(body_text)

    # Insert
    init_transactions_table()
    upsert_transaction(
        transaction_date,
        amount,
        direction,
        merchant,
        account_last4,
        EMAIL_FROM,
    )
    print(
        f"Stored transaction: {transaction_date} | {direction} | "
        f"{amount} | {merchant}"
    )


if __name__ == "__main__":
    main()
