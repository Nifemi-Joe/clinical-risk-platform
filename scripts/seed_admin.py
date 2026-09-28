"""
Creates the first admin account. Admin accounts are deliberately not
self-registrable via the API (see api/main.py /auth/register) - this script
is the real, intended way to provision one, run directly against the DB.

Usage:
    python -m scripts.seed_admin --email admin@example.com --name "Admin User"
    (will prompt for a password, hidden input, not passed on the command
    line where it could end up in shell history)

Idempotent: running it again with the same email updates nothing and exits
cleanly if that email already exists, rather than erroring or duplicating.
"""
from __future__ import annotations

import argparse
import getpass
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from api.auth import hash_password  # noqa: E402
from api.db import Role, SessionLocal, User, init_db  # noqa: E402


def seed_admin(email: str, full_name: str, password: str) -> None:
    init_db()
    db = SessionLocal()
    try:
        existing = db.query(User).filter(User.email == email).first()
        if existing:
            print(f"User {email} already exists (role={existing.role.value}) - nothing to do.")
            return
        admin = User(
            email=email,
            hashed_password=hash_password(password),
            full_name=full_name,
            role=Role.admin,
        )
        db.add(admin)
        db.commit()
        print(f"Created admin account: {email}")
    finally:
        db.close()


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Seed the first admin account")
    parser.add_argument("--email", required=True)
    parser.add_argument("--name", required=True, dest="full_name")
    parser.add_argument(
        "--password",
        default=None,
        help="If omitted, you'll be prompted (hidden input) - safer than a shell arg.",
    )
    args = parser.parse_args()

    password = args.password or getpass.getpass("Admin password: ")
    if len(password) < 8:
        print("Password must be at least 8 characters.", file=sys.stderr)
        sys.exit(1)

    seed_admin(args.email, args.full_name, password)
