"""Appraisal feedback (prompt-level learning), automatic Claude API mode, and the Stage 7 style rewrite.
Run: python -m unittest discover tests"""

import json
import shutil
import sys
import tempfile
import types
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(Path(__file__).parent))

from agent import claude_api as C  # noqa: E402
from agent import workflow as W  # noqa: E402
from agent.text import AgentError  # noqa: E402
from test_rules import FORM, SCORES, TEXT, appraisal_answer  # noqa: E402

GOOD_KEY = "sk-ant-api03-" + "x" * 40


class Base(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.ctx = W.load_context()

    def setUp(self):
        self.tmp = Path(tempfile.mkdtemp())
        self.ws = W.Workspace(self.tmp)

    def tearDown(self):
        shutil.rmtree(self.tmp, ignore_errors=True)

    def appraised(self, scores=SCORES, note=None, title="Test survey"):
        run = W.start(self.ws, dict(FORM, title=title), text=TEXT)
        W.submit_answer(self.ws, self.ctx, run, appraisal_answer())
        W.decide_appraisal(self.ws, self.ctx, run, "Anna", scores, "accepted", note)
        return run

    def drafted(self, text="42 percent of surveyed agencies have a person check AI drafts."):
        run = self.appraised()
        W.submit_answer(self.ws, self.ctx, run, json.dumps({"evidence": [
            {"claim": "42 percent of surveyed agencies say a person checks every AI draft.",
             "quote": "42 percent of agencies said a person checks every AI draft", "paragraph": "P2"}]}))
        W.decide_evidence(self.ws, run, "Anna", ["E1"])
        W.submit_answer(self.ws, self.ctx, run, json.dumps(self.draft(text)))
        return run

    @staticmethod
    def draft(text, questions=("Who checks our drafts?",)):
        return {"title": "Checking AI drafts", "sections": [{"purpose": p, "heading": p, "blocks": [
            {"kind": "evidence", "text": text, "evidence": ["E1"]}]} for p in W.REQUIRED_SECTIONS],
            "decision_questions": list(questions)}


class Feedback(Base):
    def test_every_appraisal_decision_is_logged_next_to_the_ai_suggestion(self):
        run = self.appraised(dict(SCORES, authority=1), "author is a vendor")
        entries = W.appraisal_feedback(self.ws)
        self.assertEqual(len(entries), 1)
        e = entries[0]
        self.assertEqual((e["run"], e["by"], e["changed"], e["note"]), (run["id"], "Anna", ["authority"], "author is a vendor"))
        self.assertEqual((e["ai"]["scores"]["authority"], e["human"]["scores"]["authority"]), (2, 1))
        self.assertEqual(e["ai"]["reasons"]["authority"], "because")

    def test_later_stage4_prompts_carry_the_corrections_but_keep_the_rubric(self):
        first = self.appraised(dict(SCORES, authority=1), "author is a vendor")
        nxt = W.start(self.ws, FORM, text=TEXT)
        p = W.prompt(nxt, self.ctx, self.ws)
        self.assertIn("Calibration from earlier researcher decisions", p)
        self.assertIn(f"{first['id']} \"Test survey\"", p)
        self.assertIn("Authority AI 2 -> researcher 1", p)
        self.assertIn("author is a vendor", p)
        self.assertIn("Authority: changed in 1 of 1 (lowered 1, raised 0)", p)
        self.assertIn("Official rubric: week 2 search strategy.md, Section 1.1, version 1.0", p, "the rubric is unchanged")
        self.assertIn("not a second rubric", p)

    def test_a_run_never_calibrates_itself_and_reopening_keeps_only_the_latest_decision(self):
        run = self.appraised(dict(SCORES, authority=1), "vendor")
        W.reopen(self.ws, run, "Anna", 4)
        self.assertIn(W.NO_CALIBRATION, W.calibration_text(self.ws, self.ctx, exclude=run["id"]))
        W.decide_appraisal(self.ws, self.ctx, run, "Anna", SCORES, "accepted", None)
        entries = W.appraisal_feedback(self.ws)
        self.assertEqual(len(entries), 1)
        self.assertEqual(entries[0]["changed"], [])

    def test_deleted_runs_stop_counting(self):
        run = W.start(self.ws, FORM, text=TEXT, started_by="Anna Jansen", started_login="anna.j")
        W.submit_answer(self.ws, self.ctx, run, appraisal_answer())
        W.decide_appraisal(self.ws, self.ctx, run, "Anna Jansen", SCORES, "accepted", None)
        self.assertEqual(len(W.appraisal_feedback(self.ws)), 1)
        W.delete_run(self.ws, run["id"], {"login": "anna.j", "name": "Anna Jansen", "first_name": "Anna"})
        self.assertEqual(W.appraisal_feedback(self.ws), [])

    def test_the_stage5_prompt_says_the_stage4_decision_was_logged(self):
        run = self.appraised(dict(SCORES, authority=1), "vendor")
        p = W.prompt(run, self.ctx, self.ws)
        self.assertIn("Stage 5", p)
        self.assertIn("Stage 4 feedback logged: the AI suggested 8/10 (Tier A); the researcher decided 7/10", p)
        self.assertIn("changed authority", p)


class StyleRewrite(Base):
    def test_the_draft_prompt_has_style_rules(self):
        run = self.appraised()
        W.submit_answer(self.ws, self.ctx, run, json.dumps({"evidence": [
            {"claim": "A person checks drafts.", "quote": "a person checks every AI draft", "paragraph": "P2"}]}))
        W.decide_evidence(self.ws, run, "Anna", ["E1"])
        p = W.prompt(run, self.ctx, self.ws)
        self.assertIn("must not read as AI-written", p)
        self.assertIn("No em-dashes", p)

    def test_the_check_warns_about_ai_sounding_wording(self):
        run = self.drafted("42 percent of agencies check drafts — a game-changer, moreover.")
        style = [i["text"] for i in run["check"]["items"] if i["group"] == "Wording & style"]
        self.assertTrue(any("dash" in t for t in style))
        self.assertTrue(any("game-changer" in t for t in style))
        self.assertEqual(run["check"]["errors"], 0, "style is a warning, never an error")

    def test_a_rewrite_that_keeps_claims_figures_and_citations_replaces_the_wording(self):
        run = self.drafted("Moreover, 42 percent of agencies check drafts — a game-changer.")
        W.request_polish(self.ws, run, "Anna", "shorter please")
        self.assertEqual(W.status(run)["task"], "polish")
        p = W.prompt(run, self.ctx, self.ws)
        self.assertIn("Stage 7b", p)
        self.assertIn("shorter please", p)
        W.submit_answer(self.ws, self.ctx, run, json.dumps(self.draft("42 percent of agencies have someone check every draft.")))
        self.assertEqual(run["draft"]["sections"][0]["blocks"][0]["text"], "42 percent of agencies have someone check every draft.")
        self.assertEqual(run["draft"]["style_rewrite"]["by"], "Anna")
        self.assertEqual([i for i in run["check"]["items"] if i["group"] == "Wording & style"], [])
        self.assertIn("style_rewrite", run["history"][-1], "the earlier wording is kept")
        self.assertEqual(W.status(run)["stage"], 9)

    def test_a_rewrite_that_changes_a_figure_or_citation_is_refused(self):
        run = self.drafted()
        W.request_polish(self.ws, run, "Anna")
        with self.assertRaisesRegex(AgentError, "figures changed"):
            W.submit_answer(self.ws, self.ctx, run, json.dumps(self.draft("Almost half (45 percent) of agencies check drafts.")))
        bad = self.draft("42 percent of agencies check drafts.")
        bad["sections"][0]["blocks"][0]["evidence"] = []
        with self.assertRaisesRegex(AgentError, "citations changed"):
            W.submit_answer(self.ws, self.ctx, run, json.dumps(bad))
        bad = self.draft("42 percent of agencies check drafts.")
        bad["sections"][0]["blocks"][0]["kind"] = "interpretation"
        with self.assertRaisesRegex(AgentError, "label changed"):
            W.submit_answer(self.ws, self.ctx, run, json.dumps(bad))
        with self.assertRaisesRegex(AgentError, "decision questions"):
            W.submit_answer(self.ws, self.ctx, run, json.dumps(self.draft("42 percent of agencies check drafts.", questions=())))
        self.assertEqual(W.status(run)["task"], "polish", "still waiting for an acceptable rewrite")
        W.cancel_polish(self.ws, run, "Anna")
        self.assertEqual(W.status(run)["stage"], 9)


class FakeStream:
    def __init__(self, message):
        self.message = message

    def __enter__(self):
        return self

    def __exit__(self, *a):
        return False

    def get_final_message(self):
        return self.message


def fake_anthropic(reply, stop_reason="end_turn", calls=None):
    """A stand-in for the anthropic package, so the tests never call the real API."""
    mod = types.ModuleType("anthropic")
    for name in ("AuthenticationError", "PermissionDeniedError", "NotFoundError", "RateLimitError", "BadRequestError",
                 "APIStatusError", "APIConnectionError"):
        setattr(mod, name, type(name, (Exception,), {}))

    class Client:
        def __init__(self, api_key, max_retries):
            calls.append({"api_key": api_key})
            self.beta = types.SimpleNamespace(messages=types.SimpleNamespace(stream=self.stream))

        def stream(self, **params):
            calls.append(params)
            block = types.SimpleNamespace(type="text", text=reply)
            return FakeStream(types.SimpleNamespace(stop_reason=stop_reason, content=[block]))
    mod.Anthropic = Client
    return mod


class ClaudeApi(Base):
    def setUp(self):
        super().setUp()
        self.saved = sys.modules.get("anthropic")

    def tearDown(self):
        if self.saved is None:
            sys.modules.pop("anthropic", None)
        else:
            sys.modules["anthropic"] = self.saved
        super().tearDown()

    def test_settings_default_to_manual_and_never_return_the_key(self):
        s = C.Settings(self.tmp / "local_settings")
        self.assertEqual(s.public("anna")["mode"], "manual")
        out = s.update("anna", mode="api", model="claude-sonnet-5-5", api_key=GOOD_KEY)
        self.assertNotIn(GOOD_KEY, json.dumps(out))
        self.assertEqual((out["mode"], out["model"], out["key_hint"]), ("api", "claude-sonnet-5-5", "…" + GOOD_KEY[-4:]))
        self.assertEqual(s.public("ben")["mode"], "manual", "settings are per account")
        self.assertTrue((self.tmp / "local_settings" / ".gitignore").exists())
        with self.assertRaises(AgentError):
            s.update("anna", api_key="not a key")
        self.assertFalse(s.update("anna", clear_key=True)["key_hint"])

    def test_automatic_mode_sends_the_same_prompt_and_its_answer_goes_through_the_same_checks(self):
        calls = []
        sys.modules["anthropic"] = fake_anthropic(appraisal_answer(), calls=calls)
        run = W.start(self.ws, FORM, text=TEXT)
        prompt = W.prompt(run, self.ctx, self.ws)
        answer = C.run_prompt(prompt, "appraise", "claude-opus-5-5", GOOD_KEY)
        W.submit_answer(self.ws, self.ctx, run, answer, via="ai (Claude API, claude-opus-5-5, started by Anna)", expected_task="appraise")
        params = calls[1]
        self.assertEqual(params["messages"][0]["content"], prompt)
        self.assertEqual((params["model"], params["output_config"]["effort"], params["fallbacks"]), ("claude-opus-5-5", "high", "default"))
        self.assertEqual(W.status(run)["who"], "human", "the researcher still decides the appraisal")
        self.assertTrue(W.is_automatic(run["log"][-1]["who"]))
        self.assertNotIn(GOOD_KEY, json.dumps(run))

    def test_a_bad_api_answer_is_refused_like_a_pasted_one(self):
        sys.modules["anthropic"] = fake_anthropic('{"scores": {}}', calls=[])
        run = W.start(self.ws, FORM, text=TEXT)
        answer = C.run_prompt(W.prompt(run, self.ctx, self.ws), "appraise", "claude-haiku-5-5", GOOD_KEY)
        with self.assertRaisesRegex(AgentError, "needs a score"):
            W.submit_answer(self.ws, self.ctx, run, answer, expected_task="appraise")

    def test_refusals_and_cut_off_answers_are_reported(self):
        sys.modules["anthropic"] = fake_anthropic("", stop_reason="refusal", calls=[])
        with self.assertRaisesRegex(AgentError, "declined"):
            C.run_prompt("x", "draft", "claude-opus-5-5", GOOD_KEY)
        sys.modules["anthropic"] = fake_anthropic("{", stop_reason="max_tokens", calls=[])
        with self.assertRaisesRegex(AgentError, "cut off"):
            C.run_prompt("x", "draft", "claude-opus-5-5", GOOD_KEY)

    def test_an_answer_for_a_step_that_moved_on_is_refused(self):
        run = W.start(self.ws, FORM, text=TEXT)
        with self.assertRaisesRegex(AgentError, "changed while Claude was working"):
            W.submit_answer(self.ws, self.ctx, run, appraisal_answer(), expected_task="extract")


if __name__ == "__main__":
    unittest.main()
