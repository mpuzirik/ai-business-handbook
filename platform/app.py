"""AEL Research Agent v0 - control panel.

Start:  double-click start.bat   (or: python app.py)
Runs on this computer only (http://127.0.0.1:8765). No workflow rules live here:
every button calls a function in agent/workflow.py.
"""

from __future__ import annotations

import base64
import json
import re
import sys
import threading
import traceback
import webbrowser
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import urlparse

ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT))

from agent import workflow as W  # noqa: E402
from agent import text as T  # noqa: E402
from agent.text import AgentError  # noqa: E402
from agent.word import draft_to_docx  # noqa: E402
from agent.accounts import Accounts  # noqa: E402
from agent import claude_api as C  # noqa: E402
from agent import wiki as WK  # noqa: E402
from http.cookies import SimpleCookie  # noqa: E402

UI = ROOT / "ui"
COOKIE = "ael_session"


class SignInNeeded(Exception):
    pass


class App:
    def __init__(self, workspace: Path | None = None):
        self.ctx = W.load_context()
        self.ws = W.Workspace(workspace or ROOT / "workspace")
        self.accounts = Accounts(self.ws.root / "accounts")
        self.lock = threading.Lock()
        self.settings = C.Settings(ROOT / "local_settings")   # per-account AI mode, model and API key (never in workspace/)
        self.calling = set()                                  # runs with a Claude API call in progress
        self.wiki = WK.WikiSettings(ROOT / "local_settings")  # where the team's LLM wiki clone is on this computer

    def config(self, account=None):
        r = self.ctx["rubric"]
        return {"rubric": r, "material": W.MATERIAL, "restricted": sorted(W.RESTRICTED), "privacy": W.PRIVACY,
                "stages": W.STAGES, "default_question": W.DEFAULT_QUESTION,
                "runs": [self.summary(i, account) for i in reversed(self.ws.ids())],
                "deleted": W.deleted_for(self.ws, account) if account else [],
                "activity": self.activity()}

    def activity(self, limit=8):
        """The latest decisions made by people, across all runs (for the home page)."""
        items = []
        for run_id in self.ws.ids():
            run = self.ws.load(run_id)
            title = W.display_title(run)
            items += [{"time": e["time"], "who": e["who"], "what": e["what"], "id": run_id, "title": title}
                      for e in run["log"] if not W.is_automatic(e["who"])]
        return sorted(items, key=lambda x: x["time"], reverse=True)[:limit]

    def summary(self, run_id, account=None):
        run = self.ws.load(run_id)
        st = W.status(run)
        return {"id": run_id, "title": W.display_title(run), "stage": st["stage"], "who": st["who"],
                "step": W.STAGES[st["stage"] - 1], "owner": W.owner(run), "people": W.people(run),
                "created": run["created"], "updated": run["log"][-1]["time"] if run["log"] else run["created"],
                "mine": W.may_delete(run, account), "can_delete": W.may_delete(run, account)}

    def view(self, run_id):
        run = self.ws.load(run_id)
        return {"run": run, "status": W.status(run), "stages": W.stage_states(run), "prompt": W.prompt(run, self.ctx, self.ws),
                "calibration": len(W.appraisal_feedback(self.ws)), "calling": run_id in self.calling,
                "wiki": self.wiki.get()}

    def start(self, b):
        data = base64.b64decode(b["file_b64"]) if b.get("file_b64") else None
        run = W.start(self.ws, b.get("form") or {}, text=b.get("text"), url=b.get("url"),
                      filename=b.get("filename"), data=data, started_by=b.get("reviewer"),
                      started_login=(b.get("account") or {}).get("login"))
        return self.view(run["id"])

    def detect(self, b):
        """Preview what the source says about itself, to fill the form before starting. Nothing is stored."""
        if (b.get("material") or "") in W.RESTRICTED:
            raise AgentError("Restricted material is not read.")
        data = base64.b64decode(b["file_b64"]) if b.get("file_b64") else None
        got = T.read_source(url=(b.get("url") or "").strip() or None, filename=b.get("filename"), data=data,
                            text=b.get("text"))
        return {"details": got["details"], "kind": got["kind"], "paragraphs": len(T.paragraphs(got["text"]))}

    def act(self, run_id, action, b):
        run = self.ws.load(run_id)
        who = b.get("reviewer")
        if action == "delete":
            W.delete_run(self.ws, run_id, b["account"])
            return {"deleted": run_id}
        if action == "answer":
            W.submit_answer(self.ws, self.ctx, run, b.get("answer") or "")
        elif action == "privacy":
            W.decide_privacy(self.ws, run, who, bool(b.get("allow")), b.get("note"))
        elif action == "appraisal":
            W.decide_appraisal(self.ws, self.ctx, run, who, b.get("scores") or {}, b.get("decision"), b.get("note"))
        elif action == "evidence":
            W.decide_evidence(self.ws, run, who, b.get("approved") or [])
        elif action == "redraft":
            W.request_new_draft(self.ws, run, who, b.get("note"))
        elif action == "reopen":
            W.reopen(self.ws, run, who, int(b.get("stage") or 0))
        elif action == "keep":
            W.keep_as_was(self.ws, run, who)
        elif action == "details":
            W.update_details(self.ws, run, who, b.get("fields") or {})
        elif action == "review":
            W.review_page(self.ws, run, who, b.get("decision"), b.get("note"))
        elif action == "polish":
            W.request_polish(self.ws, run, who, b.get("note"))
        elif action == "cancel_polish":
            W.cancel_polish(self.ws, run, who)
        elif action == "wiki":
            self.send_to_wiki(run, who, b)
        else:
            raise AgentError("Unknown action.")
        return self.view(run_id)

    def send_to_wiki(self, run, who, b):
        """Bring the team's LLM wiki up to date with this run (agent/wiki.py), then record that in the run."""
        who = W.check_reviewer(who)
        s = self.wiki.set(folder=b.get("folder"), push=b.get("push"))
        done = WK.send(self.ws.root, run, who, s["folder"], push=s["push"])
        run["wiki"] = done
        pages = ", ".join(p for p in (done["run_page"], done["source_page"] if done["new_source"] else None, done["handbook_page"]) if p)
        W.log(run, who, f"sent to the LLM wiki: {pages} ({done['lint'].rstrip('.')}"
              + (f"; commit {done['commit']}" if done["commit"] else "") + ("; pushed" if done["pushed"] else "") + ")")
        self.ws.save(run)


def run_with_claude(app: App, run_id: str, account: dict):
    """Automatic mode: send the current AI-step prompt to Claude and submit the reply like a pasted answer.
    The (slow) API call runs outside the app lock, so other people can keep working meanwhile."""
    s = app.settings.raw(account["login"])
    with app.lock:
        if run_id in app.calling:
            raise AgentError("Claude is already working on this step.")
        run = app.ws.load(run_id)
        task = W.status(run)["task"]
        if not task:
            raise AgentError("This run is not waiting for an AI step.")
        prompt = W.prompt(run, app.ctx, app.ws)
        app.calling.add(run_id)
    try:
        answer = C.run_prompt(prompt, task, s["model"], s["api_key"])
    finally:
        with app.lock:
            app.calling.discard(run_id)
    with app.lock:
        run = app.ws.load(run_id)
        try:
            W.submit_answer(app.ws, app.ctx, run, answer, via=f"ai (Claude API, {s['model']}, started by {account['name']})",
                            expected_task=task)
        except AgentError as exc:  # keep Claude's reply so the researcher can see it, fix it and submit it by hand
            refused = AgentError(f"{exc}\n\nClaude's reply has been put in the answer box: you can correct it and submit it by hand.")
            refused.answer = answer
            raise refused from None
        return app.view(run_id)


def make_handler(app: App):
    class Handler(BaseHTTPRequestHandler):
        def log_message(self, *args):
            pass

        def send(self, code, body: bytes, ctype):
            self.send_response(code)
            self.send_header("Content-Type", ctype)
            self.send_header("Content-Length", str(len(body)))
            self.send_header("Cache-Control", "no-store")
            self.end_headers()
            self.wfile.write(body)

        def json(self, code, data, cookie: str | None = None):
            body = json.dumps(data, ensure_ascii=False).encode("utf-8")
            self.send_response(code)
            self.send_header("Content-Type", "application/json; charset=utf-8")
            self.send_header("Content-Length", str(len(body)))
            self.send_header("Cache-Control", "no-store")
            if cookie is not None:  # the sign-in cookie: not readable by scripts, never sent by other websites
                age = 30 * 24 * 3600 if cookie else 0
                self.send_header("Set-Cookie", f"{COOKIE}={cookie}; Path=/; HttpOnly; SameSite=Strict; Max-Age={age}")
            self.end_headers()
            self.wfile.write(body)

        def token(self):
            c = SimpleCookie(self.headers.get("Cookie") or "")
            return c[COOKIE].value if COOKIE in c else None

        def user(self):
            return app.accounts.user_for(self.token())

        def need_user(self):
            user = self.user()
            if not user:
                raise SignInNeeded()
            return user

        def do_GET(self):
            path = urlparse(self.path).path
            try:
                if path == "/api/me":
                    return self.json(200, {"user": self.user(), "has_accounts": app.accounts.has_accounts()})
                account = self.need_user() if path.startswith("/api/") else None
                if path == "/api/config":
                    return self.json(200, app.config(account))
                if path == "/api/stats":
                    return self.json(200, W.stats(app.ws, account))
                if path == "/api/settings":
                    return self.json(200, app.settings.public(account["login"]))
                m = re.fullmatch(r"/api/run/(RUN-\d+)", path)
                if m:
                    return self.json(200, app.view(m[1]))
                m = re.fullmatch(r"/api/run/(RUN-\d+)/word", path)
                if m:
                    run = app.ws.load(m[1])
                    if not run["draft"]:
                        raise AgentError("There is no draft yet.")
                    name = re.sub(r"[^A-Za-z0-9 _-]+", "", run["draft"]["title"])[:60].strip() or "draft"  # plain ASCII: safe in every browser
                    body = draft_to_docx(run)
                    self.send_response(200)
                    self.send_header("Content-Type", "application/vnd.openxmlformats-officedocument.wordprocessingml.document")
                    self.send_header("Content-Disposition", f'attachment; filename="{m[1]} - {name}.docx"')
                    self.send_header("Content-Length", str(len(body)))
                    self.end_headers()
                    self.wfile.write(body)
                    return
            except SignInNeeded:
                return self.json(401, {"error": "Please sign in.", "signin": True})
            except AgentError as exc:
                return self.json(400, {"error": str(exc)})
            except Exception as exc:  # show the problem instead of a broken download
                traceback.print_exc()
                return self.json(500, {"error": f"Unexpected problem: {exc}"})
            name = "index.html" if path in ("/", "") else path.lstrip("/")
            file = (UI / name).resolve()
            if file.parent == UI.resolve() and file.exists():
                types = {".html": "text/html", ".js": "text/javascript", ".css": "text/css"}
                return self.send(200, file.read_bytes(), types.get(file.suffix, "text/plain") + "; charset=utf-8")
            self.send(404, b"Not found", "text/plain")

        def do_POST(self):
            # only this page may send actions (blocks other websites from driving the agent)
            if self.headers.get("Origin") not in (None, f"http://{self.headers.get('Host')}"):
                return self.json(403, {"error": "Requests from other websites are not allowed."})
            try:
                body = json.loads(self.rfile.read(int(self.headers.get("Content-Length") or 0)) or b"{}")
                path = urlparse(self.path).path
                # ---- signing in and out
                if path == "/api/signup":
                    token = app.accounts.create(body.get("first_name"), body.get("last_name"), body.get("login"), body.get("password"))
                    return self.json(200, {"user": app.accounts.user_for(token)}, cookie=token)
                if path == "/api/signin":
                    token = app.accounts.sign_in(body.get("login"), body.get("password"))
                    return self.json(200, {"user": app.accounts.user_for(token)}, cookie=token)
                if path == "/api/signout":
                    app.accounts.sign_out(self.token())
                    return self.json(200, {"user": None}, cookie="")
                # ---- everything else needs a signed-in account; decisions are recorded under that account's name
                account = self.need_user()
                user = body["reviewer"] = account["name"]   # first and last name
                body["account"] = account
                if path == "/api/password":
                    app.accounts.change_password(account["login"], body.get("old"), body.get("new"))
                    return self.json(200, {"ok": True})
                if path == "/api/settings":
                    return self.json(200, app.settings.update(account["login"], mode=body.get("mode"), model=body.get("model"),
                                                              api_key=body.get("api_key"), clear_key=bool(body.get("clear_key"))))
                c = re.fullmatch(r"/api/run/(RUN-\d+)/claude", path)
                if c:  # automatic mode (manages the lock itself)
                    return self.json(200, run_with_claude(app, c[1], account))
                m = re.fullmatch(r"/api/run/(RUN-\d+)/(\w+)", path)
                d = re.fullmatch(r"/api/deleted/(RUN-\d+(?:_\d+)?)/(restore|purge)", path)
                if path == "/api/detect":  # read-only preview (no lock: it stores nothing)
                    return self.json(200, app.detect(body))
                with app.lock:
                    if path == "/api/start":
                        return self.json(200, app.start(body))
                    if d:
                        run_id = (W.restore_run if d[2] == "restore" else W.purge_run)(app.ws, d[1], account)
                        return self.json(200, {"id": run_id})
                    if m:
                        return self.json(200, app.act(m[1], m[2], body))
                self.json(404, {"error": "Unknown request."})
            except SignInNeeded:
                self.json(401, {"error": "Please sign in.", "signin": True})
            except AgentError as exc:
                self.json(400, {"error": str(exc), "answer": getattr(exc, "answer", None)})
            except Exception as exc:  # show the problem instead of failing silently
                traceback.print_exc()
                self.json(500, {"error": f"Unexpected problem: {exc}"})

    return Handler


def create_server(app: App, port: int = 8765) -> ThreadingHTTPServer:
    for p in range(port, port + 20):
        try:
            return ThreadingHTTPServer(("127.0.0.1", p), make_handler(app))
        except OSError:
            continue
    raise AgentError("No free port found.")


def main():
    try:
        app = App()
    except AgentError as exc:
        print(f"Cannot start: {exc}")
        return
    server = create_server(app, int(sys.argv[1]) if len(sys.argv) > 1 and sys.argv[1].isdigit() else 8765)
    url = f"http://127.0.0.1:{server.server_address[1]}/"
    print(f"AEL Research Agent - control panel\n  Open: {url}\n  Keep this window open while you work.")
    if "--no-browser" not in sys.argv:
        threading.Timer(0.8, lambda: webbrowser.open(url)).start()
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        pass


if __name__ == "__main__":
    main()
