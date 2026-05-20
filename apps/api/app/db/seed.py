from datetime import UTC, datetime

DEMO_USERS = [
    "admin@prompteer.dev",
    "paid@prompteer.dev",
    "free@prompteer.dev",
]


def main() -> None:
    now = datetime.now(tz=UTC).isoformat()
    print(f"Seed placeholder ran at {now}; demo users: {', '.join(DEMO_USERS)}")


if __name__ == "__main__":
    main()
