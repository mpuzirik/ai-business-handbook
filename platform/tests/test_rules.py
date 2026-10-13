"""Proof that the key research rules hold. Run: python -m unittest discover tests"""

import json
import shutil
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from agent import workflow as W  # noqa: E402
from agent.text import AgentError  # noqa: E402

TEXT = ("Most small agencies use AI for first drafts.\n\n"
        "In the survey, 42 percent of agencies said a person checks every AI draft.\n\n"
        "The survey covered 300 agencies in the Netherlands in 2025.")
FORM = {"title": "Test survey", "organisation": "Test institute", "date": "2025-10-01", "language": "en",
        "material": "published", "privacy": "public"}
ANNA = {"login": "anna.j", "name": "Anna Jansen", "first_name": "Anna"}
BEN = {"login": "ben", "name": "Ben de Vries", "first_name": "Ben"}
SCORES = {"authority": 2, "evidence": 2, "recency": 2, "relevance": 1, "independence_bias": 1}


def appraisal_answer(scores=SCORES):
    return json.dumps({"scores": {k: {"score": v, "reason": "because", "paragraphs": ["P2"]} for k, v in scores.items()}})


def make_pdf(pages):
    """A small real PDF with a text layer: pages = list of lists of text lines."""
    objs = ["<< /Type /Catalog /Pages 2 0 R >>", None, "<< /Type /Font /Subtype /Type1 /BaseFont /Helvetica >>"]
    kids = []
    for lines in pages:
        ops = "BT /F1 11 Tf 14 TL 50 790 Td " + " ".join(
            "(%s) Tj T*" % line.replace("(", "\\(").replace(")", "\\)") for line in lines) + " ET"
        objs.append("<< /Length %d >>\nstream\n%s\nendstream" % (len(ops), ops))
        objs.append("<< /Type /Page /Parent 2 0 R /MediaBox [0 0 595 842] /Resources << /Font << /F1 3 0 R >> >> "
                    "/Contents %d 0 R >>" % len(objs))
        kids.append("%d 0 R" % len(objs))
    objs[1] = "<< /Type /Pages /Kids [%s] /Count %d >>" % (" ".join(kids), len(kids))
    out, offsets = "%PDF-1.4\n", []
    for i, body in enumerate(objs, start=1):
        offsets.append(len(out))
        out += "%d 0 obj\n%s\nendobj\n" % (i, body)
    xref = len(out)
    out += "xref\n0 %d\n0000000000 65535 f \n" % (len(objs) + 1) + "".join("%010d 00000 n \n" % o for o in offsets)
    out += "trailer\n<< /Size %d /Root 1 0 R >>\nstartxref\n%d\n%%%%EOF\n" % (len(objs) + 1, xref)
    return out.encode("latin-1")


PDF_PAGES = [["AI in small agencies",
              "Most small agencies now use generative AI for first drafts of copy, social posts and",
              "campaign ideas, according to the 2025 survey.",
              "In the survey, 42 percent of agencies said a person checks every AI draft.",
              "Human review"],
             ["Owners mention accuracy and client confidentiality as the main reasons to keep a person",
              "in the loop before any AI-assisted work reaches a client."]]


class Rules(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.ctx = W.load_context()

    def setUp(self):
        self.tmp = Path(tempfile.mkdtemp())
        self.ws = W.Workspace(self.tmp)

    def tearDown(self):
        shutil.rmtree(self.tmp, ignore_errors=True)

    def to_evidence_review(self):
        run = W.start(self.ws, FORM, text=TEXT)
        W.submit_answer(self.ws, self.ctx, run, appraisal_answer())
        W.decide_appraisal(self.ws, self.ctx, run, "Anna", SCORES, "accepted", None)
        W.submit_answer(self.ws, self.ctx, run, json.dumps({"evidence": [
            {"claim": "42 percent of surveyed agencies say a person checks every AI draft.",
             "quote": "42 percent of agencies said a person checks every AI draft", "paragraph": "P2"},
            {"claim": "Half of agencies use AI.", "quote": "Half of all agencies use AI", "paragraph": "P1"},
            {"claim": "80% of agencies use AI for drafts.", "quote": "Most small agencies use AI for first drafts", "paragraph": "P1"}]}))
        return run

    def test_pdf_upload_is_read_with_pages_and_paragraphs(self):
        run = W.start(self.ws, dict(FORM, title=""), filename="survey.pdf", data=make_pdf(PDF_PAGES))
        texts = [p["text"] for p in run["paragraphs"]]
        self.assertEqual(texts[0], "[Page 1]")
        self.assertIn("[Page 2]", texts)
        self.assertIn("AI in small agencies", texts, "a heading stays its own paragraph")
        self.assertTrue(any(t.startswith("Most small agencies") and t.endswith("2025 survey.") for t in texts),
                        "wrapped lines are joined into one paragraph")
        self.assertIn("Human review", texts, "a heading after a sentence starts a new paragraph")
        self.assertIn("PDF", run["source"]["capture"])
        from agent.text import quote_in
        self.assertTrue(any(quote_in("42 percent of agencies said a person checks every AI draft", t) for t in texts))

    def test_scanned_pdf_is_refused_with_a_manual_fallback(self):
        blank = make_pdf([[]])
        with self.assertRaisesRegex(AgentError, "paste"):
            W.start(self.ws, FORM, filename="scan.pdf", data=blank)

    def to_draft(self):
        run = self.to_evidence_review()
        W.decide_evidence(self.ws, run, "Anna", ["E1"])
        draft = {"title": "T", "sections": [{"purpose": p, "heading": p, "blocks": [
            {"kind": "evidence", "text": "42 percent of surveyed agencies have a person check AI drafts.", "evidence": ["E1"]}]}
            for p in W.REQUIRED_SECTIONS], "decision_questions": ["Who checks our drafts?"]}
        W.submit_answer(self.ws, self.ctx, run, json.dumps(draft))
        return run

    def test_going_back_without_a_real_change_keeps_later_steps(self):
        run = self.to_draft()
        W.reopen(self.ws, run, "Anna", 4)
        self.assertEqual((W.status(run)["stage"], W.status(run)["who"]), (4, "human"))
        W.decide_appraisal(self.ws, self.ctx, run, "Anna", dict(SCORES, relevance=2), "accepted", "same tier")  # 9/10, still A
        self.assertIsNotNone(run["draft"], "same decision and tier: the draft is kept")
        self.assertEqual(W.status(run)["stage"], 9)
        W.reopen(self.ws, run, "Anna", 5)
        W.decide_evidence(self.ws, run, "Anna", ["E1"])
        self.assertIsNotNone(run["draft"], "same evidence selection: the draft is kept")

    def test_a_real_change_redoes_the_steps_that_depend_on_it(self):
        run = self.to_draft()
        W.reopen(self.ws, run, "Anna", 4)
        W.decide_appraisal(self.ws, self.ctx, run, "Anna", dict(SCORES, evidence=0, recency=1), "accepted", "weaker")  # 5/10, Tier B
        self.assertIsNone(run["evidence"], "a different tier: evidence and draft must be redone")
        self.assertIsNone(run["draft"])
        self.assertEqual(W.status(run)["task"], "extract")
        self.assertEqual(run["history"][-1]["cleared"], ["evidence", "draft"])
        self.assertIsNotNone(run["history"][-1]["data"]["draft"], "the old work is kept in the history")

    def test_keep_as_it_was_restores_everything(self):
        run = self.to_draft()
        W.reopen(self.ws, run, "Anna", 5)
        self.assertEqual(W.status(run)["stage"], 5)
        W.keep_as_was(self.ws, run, "Anna")
        self.assertEqual(W.status(run)["stage"], 9)
        self.assertTrue(run["evidence_review"])
        with self.assertRaises(AgentError):
            W.reopen(self.ws, run, "Anna", 8)  # automatic steps cannot be changed by hand

    def test_changing_source_details_redoes_the_appraisal_only_when_it_matters(self):
        run = self.to_draft()
        W.update_details(self.ws, run, "Anna", {"title": "A clearer title"})
        self.assertIsNotNone(run["draft"], "a title change needs no redo")
        W.update_details(self.ws, run, "Anna", {"organisation": "Another institute"})
        self.assertEqual(run["appraisal"], {}, "the appraisal relied on the organisation")
        self.assertEqual(W.status(run)["task"], "appraise")

    def test_blocking_on_second_thought_removes_the_text_everywhere(self):
        run = W.start(self.ws, dict(FORM, privacy="unknown"), text=TEXT)
        W.decide_privacy(self.ws, run, "Anna", True, "published report")
        W.submit_answer(self.ws, self.ctx, run, appraisal_answer())
        W.reopen(self.ws, run, "Anna", 2)
        W.decide_privacy(self.ws, run, "Anna", False, "contains client names after all")
        self.assertEqual(run["paragraphs"], [])
        self.assertIsNone(run["history"][-1]["data"])
        stored = "".join(p.read_text(errors="ignore") for p in self.tmp.rglob("*") if p.is_file())
        self.assertNotIn("42 percent of agencies", stored)

    def test_dutch_title_is_translated_for_display(self):
        run = W.start(self.ws, dict(FORM, language="nl", title="Onderzoek naar AI"), text="Een test.\n\nNog een alinea.")
        W.submit_answer(self.ws, self.ctx, run, json.dumps({"title": "Research on AI", "paragraphs": [
            {"id": "P1", "english": "A test."}, {"id": "P2", "english": "Another paragraph."}]}))
        self.assertEqual(W.display_title(run), "Research on AI")
        self.assertEqual(run["source"]["title"], "Onderzoek naar AI", "the original title is kept")

    def test_deleting_a_run_needs_a_name_and_keeps_run_numbers_unique(self):
        first = W.start(self.ws, FORM, text=TEXT)
        second = W.start(self.ws, FORM, text=TEXT, started_by="Anna Jansen", started_login="anna.j")
        W.delete_run(self.ws, second["id"], ANNA)
        self.assertEqual(self.ws.ids(), [first["id"]])
        moved = json.loads((self.tmp / "deleted" / second["id"] / "run.json").read_text(encoding="utf-8"))
        self.assertEqual(moved["deleted"]["by"], "Anna Jansen")
        self.assertEqual(W.start(self.ws, FORM, text=TEXT)["id"], "RUN-003")   # RUN-002 is never reused

    def test_only_the_person_who_started_a_run_can_delete_it(self):
        annas = W.start(self.ws, FORM, text=TEXT, started_by="Anna Jansen", started_login="anna.j")
        with self.assertRaises(AgentError):
            W.delete_run(self.ws, annas["id"], BEN)
        old = W.start(self.ws, FORM, text=TEXT, started_by="Anna")          # from before accounts: typed first name
        self.assertTrue(W.may_delete(old, ANNA))
        self.assertFalse(W.may_delete(old, BEN))
        W.delete_run(self.ws, annas["id"], ANNA)
        self.assertEqual(self.ws.ids(), [old["id"]])

    def test_personal_statistics(self):
        run = W.start(self.ws, FORM, text=TEXT, started_by="Anna Jansen", started_login="anna.j")
        W.submit_answer(self.ws, self.ctx, run, appraisal_answer())
        W.decide_appraisal(self.ws, self.ctx, run, "Anna Jansen", dict(SCORES, relevance=2), "accepted", "sure")
        W.start(self.ws, FORM, text=TEXT, started_by="Ben de Vries", started_login="ben")
        st = W.stats(self.ws, ANNA)
        self.assertEqual((st["runs"]["started"], st["runs"]["contributed"]), (1, 0))
        self.assertEqual((st["decisions"]["appraisals"], st["decisions"]["accepted"]), (1, 1))
        self.assertEqual(st["appraisal"]["ai_scores_changed"], 1)          # Anna changed one AI score
        self.assertEqual(W.stats(self.ws, BEN)["decisions"]["appraisals"], 0)

    def test_recently_deleted_can_be_restored_or_removed_for_good(self):
        run = W.start(self.ws, FORM, text=TEXT, started_by="Anna Jansen", started_login="anna.j")
        W.delete_run(self.ws, run["id"], ANNA)
        [gone] = W.deleted_for(self.ws, ANNA)
        self.assertEqual((gone["id"], gone["deleted_by"]), (run["id"], "Anna Jansen"))
        self.assertEqual(W.deleted_for(self.ws, BEN), [])                   # Ben does not see Anna's deleted runs
        with self.assertRaises(AgentError):
            W.restore_run(self.ws, gone["folder"], BEN)
        self.assertEqual(W.restore_run(self.ws, gone["folder"], ANNA), run["id"])
        back = self.ws.load(run["id"])
        self.assertNotIn("deleted", back)
        self.assertIn("restored", back["log"][-1]["what"])
        W.delete_run(self.ws, run["id"], ANNA)
        with self.assertRaises(AgentError):
            W.purge_run(self.ws, W.deleted_for(self.ws, ANNA)[0]["folder"], BEN)
        W.purge_run(self.ws, W.deleted_for(self.ws, ANNA)[0]["folder"], ANNA)
        self.assertEqual((self.ws.ids(), self.ws.deleted()), ([], []))
        self.assertFalse(any((self.tmp / "deleted").iterdir()))

    def test_accounts_protect_names_and_never_store_passwords(self):
        from agent.accounts import Accounts
        acc = Accounts(self.tmp / "accounts")
        token = acc.create("Anna", "Jansen", "anna.j", "correct horse")
        self.assertEqual(acc.user_for(token)["name"], "Anna Jansen")   # logs show first + last name
        self.assertNotIn("correct horse", (self.tmp / "accounts" / "users.json").read_text(encoding="utf-8"))
        self.assertNotIn(token, (self.tmp / "accounts" / "sessions.json").read_text(encoding="utf-8"))
        with self.assertRaises(AgentError):
            acc.sign_in("anna.j", "wrong password")
        with self.assertRaises(AgentError):
            acc.create("Someone", "Else", "ANNA.J", "another pass")      # login taken (case does not matter)
        with self.assertRaises(AgentError):
            acc.create("anna", "jansen", "anna2", "another pass")        # same person twice: logs would be ambiguous
        with self.assertRaises(AgentError):
            acc.create("Ben", "de Vries", "ben", "short")                # password too short
        self.assertEqual(acc.user_for(acc.sign_in(" Anna.J ", "correct horse"))["name"], "Anna Jansen")
        acc.sign_out(token)
        self.assertIsNone(acc.user_for(token))
        acc.change_password("anna.j", "correct horse", "new password!")
        with self.assertRaises(AgentError):
            acc.sign_in("anna.j", "correct horse")

    def test_rubric_is_read_from_the_project_document(self):
        rubric = self.ctx["rubric"]
        self.assertEqual((rubric["version"], rubric["file"]), ("1.0", "week 2 search strategy.md"))
        self.assertEqual([t["tier"] for t in rubric["tiers"]], ["A", "B", "C"])

    def test_restricted_material_is_blocked_and_never_stored(self):
        run = W.start(self.ws, dict(FORM, material="transcript_identifiable"), text="SECRET interview text")
        self.assertEqual(W.status(run)["who"], "stopped")
        self.assertIsNone(W.prompt(run, self.ctx), "no prompt is ever made for blocked material")
        stored = "".join(p.read_text(errors="ignore") for p in self.tmp.rglob("*") if p.is_file())
        self.assertNotIn("SECRET", stored)

    def test_unclear_privacy_stops_for_a_person(self):
        run = W.start(self.ws, dict(FORM, privacy="unknown"), text=TEXT)
        self.assertEqual((W.status(run)["stage"], W.status(run)["who"]), (2, "human"))
        self.assertIsNone(W.prompt(run, self.ctx))
        W.decide_privacy(self.ws, run, "Anna", True, "Published report")
        self.assertEqual(W.status(run)["task"], "appraise")

    def test_dutch_source_is_translated_before_appraisal(self):
        run = W.start(self.ws, dict(FORM, language="nl"), text="Een test.\n\nNog 12 procent.")
        self.assertEqual(W.status(run)["task"], "translate")
        with self.assertRaises(AgentError):  # every paragraph is needed
            W.submit_answer(self.ws, self.ctx, run, json.dumps({"paragraphs": [{"id": "P1", "english": "A test."}]}))
        W.submit_answer(self.ws, self.ctx, run, json.dumps({"paragraphs": [
            {"id": "P1", "english": "A test."}, {"id": "P2", "english": "Another 13 percent."}]}))
        self.assertIn("P2: figures differ", " ".join(run["translation"]["notes"]))
        self.assertEqual(W.status(run)["task"], "appraise")

    def test_ai_appraisal_is_only_a_suggestion(self):
        run = W.start(self.ws, FORM, text=TEXT)
        W.submit_answer(self.ws, self.ctx, run, appraisal_answer())
        self.assertEqual(W.status(run)["who"], "human", "the agent waits for a person")
        for name in ("", "Claude", "AI agent"):
            with self.assertRaises(AgentError):
                W.decide_appraisal(self.ws, self.ctx, run, name, SCORES, "accepted", None)
        with self.assertRaises(AgentError):  # changed score without a reason
            W.decide_appraisal(self.ws, self.ctx, run, "Anna", dict(SCORES, evidence=1), "accepted", "")
        low = dict.fromkeys(SCORES, 0)
        with self.assertRaises(AgentError):  # Tier C cannot be accepted
            W.decide_appraisal(self.ws, self.ctx, run, "Anna", low, "accepted", "low")
        W.decide_appraisal(self.ws, self.ctx, run, "Anna", low, "rejected", "low")
        self.assertEqual(W.status(run)["who"], "stopped")

    def test_quotes_and_figures_are_checked_against_the_source(self):
        run = self.to_evidence_review()
        problems = {e["id"]: e["problems"] for e in run["evidence"]}
        self.assertEqual(problems["E1"], [])
        self.assertIn("not found word for word", " ".join(problems["E2"]))
        self.assertIn("80", " ".join(problems["E3"]))
        with self.assertRaises(AgentError):
            W.decide_evidence(self.ws, run, "Anna", ["E1", "E2"])

    def test_draft_may_only_use_approved_evidence(self):
        run = self.to_evidence_review()
        W.decide_evidence(self.ws, run, "Anna", ["E1"])
        self.assertNotIn("Half of agencies", W.prompt(run, self.ctx))
        draft = {"title": "T", "sections": [{"purpose": "context", "heading": "H", "blocks": [
            {"kind": "evidence", "text": "42 percent check every draft; 90 percent like it.", "evidence": ["E1", "E2"]},
            {"kind": "evidence", "text": "No source here.", "evidence": []}]}]}
        W.submit_answer(self.ws, self.ctx, run, json.dumps(draft))
        errors = " ".join(i["text"] for i in run["check"]["items"] if i["level"] == "error")
        self.assertIn("not approved: E2", errors)
        self.assertIn("90", errors)
        self.assertIn("has no citation", errors)
        self.assertEqual(W.status(run)["stage"], 8, "a page with errors cannot reach the final review")

    def test_page_approval_is_human_and_nothing_is_published(self):
        run = self.to_evidence_review()
        W.decide_evidence(self.ws, run, "Anna", ["E1"])
        draft = {"title": "T", "sections": [{"purpose": p, "heading": p, "blocks": [
            {"kind": "evidence", "text": "42 percent of surveyed agencies have a person check AI drafts.", "evidence": ["E1"]}]}
            for p in W.REQUIRED_SECTIONS], "decision_questions": ["Who checks our drafts?"]}
        W.submit_answer(self.ws, self.ctx, run, json.dumps(draft))
        self.assertEqual((W.status(run)["stage"], W.status(run)["who"]), (9, "human"))
        W.review_page(self.ws, run, "Bram", "changes", "Add an example")
        self.assertEqual(W.status(run)["task"], "draft")
        self.assertIn("Add an example", W.prompt(run, self.ctx))
        self.assertEqual(len(run["history"]), 1, "the earlier draft is kept")
        W.submit_answer(self.ws, self.ctx, run, json.dumps(draft))
        W.review_page(self.ws, run, "Bram", "approve", "")
        self.assertEqual(W.status(run)["who"], "done")
        self.assertIn("Not published", run["review"]["publication"])


if __name__ == "__main__":
    unittest.main()
