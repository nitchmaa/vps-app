from __future__ import annotations

import email
import imaplib
import os
import re
from datetime import datetime
from email.message import Message

from db_transactions import init_transactions_table, upsert_transaction


# =========================
# Environment configuration
# =========================

EMAIL_FROM = os.getenv("EMAIL_FROM", "").strip()
EMAIL_SUBJECT_KEYWORD = os.getenv("TRANSACTION_SUBJECT_KEYWORD", "").strip()

# =========================
# Regex patterns (USAA)
# =========================

AMOUNT_REGEX = re.compile(r"\$([\d]+\.\d{2})")
DATE_REGEX = re.compile(r"Date:\s*(\d{2}/\d{2}/\d{2})")

# Capture everything between "To:" and "Date:", including newlines
MERCHANT_REGEX = re.compile(
    r"To:\s*([\s\S]+?)\s*Date:",
    re.IGNORECASE,
)

ACCOUNT_LAST4_REGEX = re.compile(
    r"ending in\s*(\d{4})",
    re.IGNORECASE,
)


# =========================
# Helpers
# =========================

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


def find_latest_matching_message(client, sender, subject_keyword) -> bytes:
    status, data = client.search(
        None,
        "FROM",
        f'"{sender}"',
        "SUBJECT",
        f'"{subject_keyword}"',
    )
    if status != "OK" or not data or not data[0]:
        raise RuntimeError("No matching transaction emails found")
    return data[0].split()[-1]


def parse_transaction(body: str):
    # Date
    date_match = DATE_REGEX.search(body)
    if not date_match:
        raise RuntimeError("Could not parse transaction date")

    transaction_date = datetime.strptime(
        date_match.group(1),
        "%m/%d/%y",
    ).date().isoformat()

    # Amount
    amt_match = AMOUNT_REGEX.search(body)
    if not amt_match:
        raise RuntimeError("Could not parse transaction amount")

    amount = float(amt_match.group(1))

    # Merchant (multiline-safe)
    merch_match = MERCHANT_REGEX.search(body)
    if not merch_match:
        raise RuntimeError("Could not parse merchant")

    merchant = " ".join(merch_match.group(1).split())

    # Account last 4 (optional)
    acct_match = ACCOUNT_LAST4_REGEX.search(body)
    account_last4 = acct_match.group(1) if acct_match else None

    direction = "debit"

    return transaction_date, amount, direction, merchant, account_last4


# =========================
# Main
# =========================

def main() -> None:
    if not EMAIL_FROM or not EMAIL_SUBJECT_KEYWORD:
        raise RuntimeError(
            "EMAIL_FROM and TRANSACTION_SUBJECT_KEYWORD must be set"
        )

    host, port, username, password, mailbox = get_imap_config()

    with imaplib.IMAP4_SSL(host, port) as client:
        client.login(username, password)
        client.select(mailbox, readonly=True)

        msg_id = find_latest_matching_message(
            client,
            EMAIL_FROM,
            EMAIL_SUBJECT_KEYWORD,
        )

        status, data = client.fetch(msg_id, "(RFC822)")
        if status != "OK" or not data or data[0] is None:
            raise RuntimeError("Failed to fetch transaction email")

        raw_email = data[0][1]
        msg = email.message_from_bytes(raw_email)
        body = extract_text_from_message(msg)

        (
            transaction_date,
            amount,
            direction,
            merchant,
            account_last4,
        ) = parse_transaction(body)

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
        f"Stored transaction: {transaction_date} | "
        f"{direction} | {amount} | {merchant}"
    )


if __name__ == "__main__":
    main()
