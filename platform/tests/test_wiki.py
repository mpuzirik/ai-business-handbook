"""Send to wiki (agent/wiki.py). Run: python -m unittest discover tests"""

import json
import shutil
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from agent import workflow as W  # noqa: E402
from agent import wiki as WK  # noqa: E402
from agent.text import AgentError  # noqa: E402
from tests.test_rules import FORM, SCORES, TEXT, appraisal_answer  # noqa: E402

INDEX = "# Index\n\n## Sources\n\n- [[older-source]]: an older source.\n\n## Entities\n\n- [[test-institute]]: the test institute.\n"
LOG = "# Log\n\nNewest first.\n\n---\n\n## [2026-10-01] ingest | Older source\n\n- Added by: Sam\n"
EVIDENCE = {"evidence": [
    {"claim": "42 percent of surveyed agencies say a \"person checks every draft\" of AI.",
     "quote": "42 percent of agencies said a person checks every AI draft", "paragraph": "P2"},
    {"claim": "Most small agencies use AI for first drafts.",
     "quote": "Most small agencies use AI for first drafts", "paragraph": "P1"}]}


class SendToWiki(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.ctx = W.load_context()

    def setUp(self):
        self.tmp = Path(tempfile.mkdtemp())
        self.ws = W.Workspace(self.tmp / "workspace")
        self.wiki = self.tmp / "wiki-repo"
        (self.wiki / "raw").mkdir(parents=True)
        (self.wiki / "wiki" / "sources").mkdir(parents=True)
        (self.wiki / "wiki" / "entities").mkdir(parents=True)
        (self.wiki / "wiki" / "index.md").write_text(INDEX, encoding="utf-8")
        (self.wiki / "wiki" / "log.md").write_text(LOG, encoding="utf-8")
        (self.wiki / "wiki" / "entities" / "test-institute.md").write_text("---\ntype: entity\n---\n", encoding="utf-8")

    def tearDown(self):
        shutil.rmtree(self.tmp, ignore_errors=True)

    def read(self, rel):
        return (self.wiki / rel).read_text(encoding="utf-8")

    def appraised_run(self):
        run = W.start(self.ws, dict(FORM, url="https://example.org/survey"), text=TEXT)
        W.submit_answer(self.ws, self.ctx, run, appraisal_answer())
        W.decide_appraisal(self.ws, self.ctx, run, "Anna", SCORES, "accepted", None)
        return run

    def approved_run(self):
        run = self.appraised_run()
        W.submit_answer(self.ws, self.ctx, run, json.dumps(EVIDENCE))
        W.decide_evidence(self.ws, run, "Anna", ["E1"])
        return run

    def approve_page(self, run):
        draft = {"title": "Who checks AI drafts", "sections": [{"purpose": p, "heading": p, "blocks": [
            {"kind": "evidence", "text": "42 percent of surveyed agencies have a person check AI drafts.", "evidence": ["E1"]}]}
            for p in W.REQUIRED_SECTIONS], "decision_questions": ["Who checks our drafts?"]}
        W.submit_answer(self.ws, self.ctx, run, json.dumps(draft))
        W.review_page(self.ws, run, "Bram", "approve", "")
        return run

    def send(self, run, today="2026-10-12"):
        return WK.send(self.ws.root, run, "Anna Jansen", str(self.wiki), push=False, today=today)

    def test_an_approved_source_gets_a_run_page_source_page_raw_file_index_lines_and_a_log_entry(self):
        run = self.approved_run()
        done = self.send(run)
        self.assertEqual((done["run_page"], done["source_page"], done["handbook_page"]), (run["id"].lower(), "2025-10-01-test-survey", None))
        page = self.read("wiki/sources/2025-10-01-test-survey.md")
        self.assertIn("> 42 percent of agencies said a person checks every AI draft", page, "approved quote, verbatim")
        self.assertNotIn("Most small agencies use AI for first drafts", page, "evidence that was not approved stays off the source page")
        self.assertNotIn('"person checks', page, "AI-written text carries no double quotes (lint would read them as quotes)")
        self.assertIn("[[test-institute]]", page, "links the organisation when it already has an entity page")
        self.assertIn(f"[[{done['run_page']}]]", page, "the source page links its run")
        self.assertIn("42 percent of agencies said a person checks every AI draft", self.read(done["raw"]))
        record = self.read(f"wiki/runs/{done['run_page']}.md")
        for part in ("type: run", "## Input", "## Appraisal", "| authority | 2 | 2 |", "## Evidence", "**E2** (not approved",
                     "## Activity log", "[[2025-10-01-test-survey]]"):
            self.assertIn(part, record)
        index = self.read("wiki/index.md")
        self.assertLess(index.index("[[2025-10-01-test-survey]]"), index.index("[[older-source]]"), "newest source first")
        self.assertIn("## Agent runs", index)
        log = self.read("wiki/log.md")
        self.assertLess(log.index(f"## [2026-10-12] ingest | {run['id']} from the panel"), log.index("## [2026-10-01]"), "newest entry first")

    def test_before_the_evidence_is_approved_only_the_run_page_is_written(self):
        done = self.send(self.appraised_run())
        self.assertFalse(done["new_source"])
        self.assertEqual(list((self.wiki / "wiki" / "sources").glob("*.md")), [])
        self.assertIn("Appraisal accepted by Anna", self.read(f"wiki/runs/{done['run_page']}.md"))

    def test_the_approved_handbook_page_goes_to_the_wiki_and_an_unchanged_run_is_not_sent_twice(self):
        run = self.approve_page(self.approved_run())
        done = self.send(run)
        self.assertEqual(done["handbook_page"], "who-checks-ai-drafts")
        page = self.read("wiki/handbook/who-checks-ai-drafts.md")
        for part in ("type: handbook", "approved_by: \"Bram\"", "**Evidence:** 42 percent", "[E1]", "## Quotes",
                     "> 42 percent of agencies said a person checks every AI draft", "## Questions for your agency"):
            self.assertIn(part, page)
        self.assertIn("## Handbook pages", self.read("wiki/index.md"))
        with self.assertRaisesRegex(AgentError, "already up to date"):
            self.send(run, today="2026-10-13")

    def test_research_notes_and_interview_material_never_go_to_the_wiki(self):
        run = self.approved_run()
        run["source"]["material"] = "transcript_anonymised"
        with self.assertRaisesRegex(AgentError, "Only published"):
            self.send(run)
        self.assertEqual(list((self.wiki / "wiki").rglob("run-*.md")), [])

    def test_a_source_already_in_the_wiki_is_linked_not_filed_twice_and_raw_is_never_overwritten(self):
        older = self.wiki / "wiki" / "sources" / "older-source.md"
        older.write_text('---\ntype: source\nurl: "https://example.org/survey"\n---\n\n## Links\n\n[[test-institute]]\n', encoding="utf-8")
        done = self.send(self.approved_run())
        self.assertEqual((done["source_page"], done["new_source"]), ("older-source", False))
        self.assertIn(f"[[test-institute]] · [[{done['run_page']}]]", older.read_text(encoding="utf-8"))
        older.unlink()
        (self.wiki / "raw" / "articles").mkdir()
        (self.wiki / "raw" / "articles" / "test-survey.md").write_text("earlier copy", encoding="utf-8")
        with self.assertRaisesRegex(AgentError, "never overwritten"):
            self.send(self.approved_run())
        self.assertEqual(self.read("raw/articles/test-survey.md"), "earlier copy")

    def test_nothing_is_written_when_the_wiki_check_finds_a_new_error(self):
        (self.wiki / "tools").mkdir()
        (self.wiki / "tools" / "lint.py").write_text(
            "from pathlib import Path\n"
            "bad = list(Path('wiki').rglob('run-*.md'))\n"
            "print('ERROR  quote  something is wrong' if bad else '')\n"
            "print(f'{len(bad)} error(s), 0 warning(s).')\n", encoding="utf-8")
        with self.assertRaisesRegex(AgentError, "nothing was filed"):
            self.send(self.approved_run())
        self.assertEqual(sorted(p.name for p in (self.wiki / "wiki").rglob("*.md")), ["index.md", "log.md", "test-institute.md"])
        self.assertEqual(list((self.wiki / "raw").rglob("*.md")), [])
        self.assertEqual(self.read("wiki/index.md"), INDEX)
        self.assertEqual(self.read("wiki/log.md"), LOG)

    def test_the_folder_must_be_the_wiki(self):
        with self.assertRaisesRegex(AgentError, "does not look like the LLM wiki"):
            WK.send(self.ws.root, self.approved_run(), "Anna Jansen", str(self.tmp), push=False)


if __name__ == "__main__":
    unittest.main()
