"""Accounts and sign-in for the control panel. Standard library only.

Passwords are never stored: only a salted PBKDF2-SHA256 hash. Sign-in sessions are random tokens kept in a
cookie; only a hash of each token is stored, so the files in workspace/accounts/ cannot be used to sign in.
"""

from __future__ import annotations

import hashlib
import hmac
import json
import re
import secrets
import threading
from datetime import datetime, timedelta
from pathlib import Path

from agent.text import AgentError

ITERATIONS = 200_000
SESSION_DAYS = 30
MIN_PASSWORD = 8


def _now() -> datetime:
    return datetime.now().replace(microsecond=0)


def _hash_password(password: str, salt: bytes) -> str:
    return hashlib.pbkdf2_hmac("sha256", password.encode("utf-8"), salt, ITERATIONS).hex()


def _token_key(token: str) -> str:
    return hashlib.sha256(token.encode("utf-8")).hexdigest()


def _clean(value: str | None, label: str, limit: int = 40) -> str:
    value = " ".join((value or "").split())
    if not value:
        raise AgentError(f"Fill in your {label}.")
    if len(value) > limit:
        raise AgentError(f"Use at most {limit} characters for your {label}.")
    return value


def _clean_login(login: str | None) -> str:
    login = (login or "").strip().lower()
    if not re.fullmatch(r"[a-z0-9._-]{3,30}", login):
        raise AgentError("Choose a login of 3-30 characters: letters, numbers, dots, dashes or underscores, no spaces.")
    return login


class Accounts:
    def __init__(self, root: Path):
        self.root = Path(root)
        self.root.mkdir(parents=True, exist_ok=True)
        self.users_file = self.root / "users.json"
        self.sessions_file = self.root / "sessions.json"
        self.lock = threading.Lock()

    # ---- storage
    def _read(self, path: Path) -> dict:
        return json.loads(path.read_text(encoding="utf-8")) if path.exists() else {}

    def _write(self, path: Path, data: dict) -> None:
        path.write_text(json.dumps(data, indent=2, ensure_ascii=False), encoding="utf-8")

    def _user(self, login: str) -> dict | None:
        return self._read(self.users_file).get(login)

    def has_accounts(self) -> bool:
        return bool(self._read(self.users_file))

    def display_name(self, login: str) -> str | None:
        """First and last name: the name shown in logs and on every decision."""
        u = self._user(login)
        return f"{u['first_name']} {u['last_name']}" if u else None

    # ---- accounts
    def create(self, first_name: str | None, last_name: str | None, login: str | None, password: str | None) -> str:
        """Create an account and sign it in. Returns the session token."""
        first, last = _clean(first_name, "first name"), _clean(last_name, "last name")
        login = _clean_login(login)
        if len(password or "") < MIN_PASSWORD:
            raise AgentError(f"Choose a password of at least {MIN_PASSWORD} characters.")
        with self.lock:
            users = self._read(self.users_file)
            if login in users:
                raise AgentError(f"The login {login} is already taken. Sign in instead, or choose another login.")
            full = f"{first} {last}".lower()
            if any(f"{u['first_name']} {u['last_name']}".lower() == full for u in users.values()):
                raise AgentError(f"There is already an account for {first} {last}. Sign in with that account "
                                 "(two accounts with the same name would make the logs ambiguous).")
            salt = secrets.token_bytes(16)
            users[login] = {"login": login, "first_name": first, "last_name": last, "salt": salt.hex(),
                            "hash": _hash_password(password, salt), "created": _now().isoformat()}
            self._write(self.users_file, users)
        return self._new_session(login)

    def _check(self, login: str, password: str | None) -> bool:
        u = self._user(login)
        return bool(u) and hmac.compare_digest(u["hash"], _hash_password(password or "", bytes.fromhex(u["salt"])))

    def sign_in(self, login: str | None, password: str | None) -> str:
        """Check login and password. Returns a session token."""
        login = (login or "").strip().lower()
        if not self._check(login, password):  # same message for an unknown login and a wrong password
            raise AgentError("That login and password do not match.")
        return self._new_session(login)

    def change_password(self, login: str, old: str | None, new: str | None) -> None:
        if len(new or "") < MIN_PASSWORD:
            raise AgentError(f"Choose a new password of at least {MIN_PASSWORD} characters.")
        if not self._check(login, old):
            raise AgentError("Your current password is not correct.")
        with self.lock:
            users = self._read(self.users_file)
            salt = secrets.token_bytes(16)
            users[login].update(salt=salt.hex(), hash=_hash_password(new, salt))
            self._write(self.users_file, users)

    # ---- sessions
    def _new_session(self, login: str) -> str:
        token = secrets.token_urlsafe(32)
        with self.lock:
            sessions = self._read(self.sessions_file)
            now = _now()
            sessions = {k: v for k, v in sessions.items() if datetime.fromisoformat(v["expires"]) > now}  # tidy up
            sessions[_token_key(token)] = {"login": login, "expires": (now + timedelta(days=SESSION_DAYS)).isoformat()}
            self._write(self.sessions_file, sessions)
        return token

    def user_for(self, token: str | None) -> dict | None:
        """The signed-in account of a valid session ({login, name}), else None."""
        if not token:
            return None
        s = self._read(self.sessions_file).get(_token_key(token))
        if not s or datetime.fromisoformat(s["expires"]) <= _now():
            return None
        u = self._user(s["login"])
        if not u:
            return None
        return {"login": u["login"], "name": f"{u['first_name']} {u['last_name']}", "first_name": u["first_name"],
                "created": u["created"]}

    def sign_out(self, token: str | None) -> None:
        if not token:
            return
        with self.lock:
            sessions = self._read(self.sessions_file)
            if sessions.pop(_token_key(token), None) is not None:
                self._write(self.sessions_file, sessions)
