"""Automatic mode: send an AI-step prompt to Claude through the Anthropic API.

Manual mode (copy the prompt, paste Claude's answer) stays the default. In automatic mode the
agent sends the very same prompt and passes the reply through the very same checks as a pasted
answer, so nothing about the research rules changes.

API keys are stored per account in local_settings/claude_api.json on this computer only. That
folder is ignored by git, the key is never sent back to the browser (only a masked hint), and it is
never written to a run, the activity log or an error message.
Needs the official SDK once:  py -m pip install anthropic
"""

from __future__ import annotations

import json
import os
import threading
from pathlib import Path

from agent.text import AgentError

MODELS = {  # shown in the settings; the first is the default
    "claude-opus-5-5": "Claude Opus 5.5 (most careful, default)",
    "claude-sonnet-5-5": "Claude Sonnet 5.5 (faster, cheaper)",
    "claude-haiku-5-5": "Claude Haiku 5.5 (fastest, cheapest; weakest at appraisal)",
}
DEFAULT_MODEL = "claude-opus-5-5"
MODES = ("manual", "api")
# How hard Claude thinks per step. Opus 5.5 defaults to "medium", so it is set explicitly.
EFFORT = {"translate": "medium", "appraise": "high", "extract": "high", "draft": "high", "polish": "medium"}
SYSTEM = ("You are the AEL Research Agent v0, a research assistant for a team writing an evidence-based handbook on "
          "AI in small marketing agencies. Follow the user's prompt exactly. It is complete. Reply with only the "
          "JSON object it asks for: no text, headings or code fences before or after it.")


class Settings:
    """Per-account mode, model and API key, in one JSON file next to the app (never in the workspace or a run)."""

    def __init__(self, folder: Path):
        self.folder = Path(folder)
        self.file = self.folder / "claude_api.json"
        self.lock = threading.Lock()

    def _all(self) -> dict:
        try:
            return json.loads(self.file.read_text(encoding="utf-8"))
        except (OSError, ValueError):
            return {}

    def _save(self, data: dict) -> None:
        self.folder.mkdir(parents=True, exist_ok=True)
        ignore = self.folder / ".gitignore"
        if not ignore.exists():  # keeps the keys out of any git repository this folder ends up in
            ignore.write_text("# Local API keys: never commit.\n*\n", encoding="utf-8")
        tmp = self.file.with_suffix(".tmp")
        tmp.write_text(json.dumps(data, indent=2), encoding="utf-8")
        try:
            os.chmod(tmp, 0o600)
        except OSError:
            pass
        tmp.replace(self.file)

    def raw(self, login: str) -> dict:
        s = self._all().get(login) or {}
        return {"mode": s.get("mode") if s.get("mode") in MODES else "manual",
                "model": s.get("model") if s.get("model") in MODELS else DEFAULT_MODEL,
                "api_key": s.get("api_key") or ""}

    def public(self, login: str) -> dict:
        """What the browser may see: never the key itself."""
        s = self.raw(login)
        key = s.pop("api_key")
        env = bool(os.environ.get("ANTHROPIC_API_KEY"))
        s.update(has_key=bool(key) or env, key_hint=(f"…{key[-4:]}" if key else "from ANTHROPIC_API_KEY" if env else ""),
                 models=MODELS, sdk_installed=sdk_installed())
        return s

    def update(self, login: str, mode: str | None = None, model: str | None = None, api_key: str | None = None,
               clear_key: bool = False) -> dict:
        with self.lock:
            data = self._all()
            s = data.setdefault(login, {})
            if mode is not None:
                if mode not in MODES:
                    raise AgentError("Unknown mode.")
                s["mode"] = mode
            if model is not None:
                if model not in MODELS:
                    raise AgentError("Unknown model.")
                s["model"] = model
            if clear_key:
                s.pop("api_key", None)
            elif api_key:
                key = api_key.strip()
                if not key.startswith("sk-ant-") or len(key) < 30 or any(c.isspace() for c in key):
                    raise AgentError("That does not look like a Claude API key (it starts with sk-ant-).")
                s["api_key"] = key
            self._save(data)
        return self.public(login)


def sdk_installed() -> bool:
    try:
        import anthropic  # noqa: F401
        return True
    except ImportError:
        return False


def run_prompt(prompt: str, task: str, model: str, api_key: str | None) -> str:
    """Send one AI-step prompt and return Claude's text reply. Errors never contain the key."""
    try:
        import anthropic
    except ImportError:
        raise AgentError("Automatic mode needs the Anthropic Python package. Close the black window, run "
                         "'py -m pip install anthropic' in a command prompt, then start start.bat again. "
                         "Until then, switch to manual mode.") from None
    key = api_key or os.environ.get("ANTHROPIC_API_KEY")
    if not key:
        raise AgentError("No Claude API key saved. Add one under your name (top right) > AI settings, or switch to manual mode.")
    client = anthropic.Anthropic(api_key=key, max_retries=3)
    params = dict(model=model, max_tokens=64000, system=SYSTEM, messages=[{"role": "user", "content": prompt}],
                  output_config={"effort": EFFORT.get(task, "high")})
    if model in ("claude-opus-5-5", "claude-sonnet-5-5"):
        # if a safety classifier declines, the API retries on Anthropic's recommended fallback model
        params.update(betas=["server-side-fallback-2026-07-01"], fallbacks="default")
    try:
        with client.beta.messages.stream(**params) as stream:  # streamed: long translations and drafts
            message = stream.get_final_message()
    except anthropic.AuthenticationError:
        raise AgentError("Claude rejected the API key. Check it under your name > AI settings.") from None
    except anthropic.PermissionDeniedError:
        raise AgentError("This API key may not use that model. Choose another model under AI settings.") from None
    except anthropic.NotFoundError:
        raise AgentError(f"The model {model} was not found for this API key. Choose another model under AI settings.") from None
    except anthropic.RateLimitError:
        raise AgentError("Claude's rate limit was reached. Wait a minute and try again, or use manual mode.") from None
    except anthropic.BadRequestError as exc:
        raise AgentError(f"Claude refused the request: {_safe(exc)}") from None
    except anthropic.APIStatusError as exc:
        raise AgentError(f"Claude's service returned an error ({exc.status_code}). Try again later, or use manual mode.") from None
    except anthropic.APIConnectionError:
        raise AgentError("Could not reach Claude. Check the internet connection, or use manual mode.") from None
    if message.stop_reason == "refusal":
        raise AgentError("Claude declined this request. Try manual mode in the Claude project, and tell a teammate.")
    if message.stop_reason == "max_tokens":
        raise AgentError("Claude's answer was cut off because it was too long. Try manual mode for this source.")
    text = "".join(b.text for b in message.content if b.type == "text").strip()
    if not text:
        raise AgentError("Claude sent an empty answer. Try again, or use manual mode.")
    return text


def _safe(exc) -> str:
    """The API's own error message, without anything that could echo a credential."""
    msg = str(getattr(exc, "message", "") or exc)
    return msg if "sk-ant-" not in msg else "request rejected"
