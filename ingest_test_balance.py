from datetime import date

from db import init_db, upsert_daily_balance


def main() -> None:
    today = date.today().isoformat()
    test_balance = 1234.56

    init_db()
    upsert_daily_balance(today, test_balance)

    print(f"Inserted test balance for {today}: {test_balance:.2f}")


if __name__ == "__main__":
    main()
