"""The appraisal rubric, read live from the official project document.

Source: ../Context/week 2 search strategy.md, Section 1.1, rubric version 1.0.
The rubric is not copied into the code. If the section is missing or has a different
version number, the agent stops instead of using an old copy.
"""

from __future__ import annotations

import re
from pathlib import Path

from agent.text import AgentError

KEYS = {"Authority": "authority", "Evidence": "evidence", "Recency": "recency", "Relevance": "relevance",
        "Independence and bias": "independence_bias"}
CHECKS = ["Transparency", "Comparability", "Traceability", "Cross-checking"]


def load_rubric(path: Path, expected_version: str = "1.0") -> dict:
    if not path.exists():
        raise AgentError(f"Rubric document not found: {path}")
    match = re.search(r"^###\s*1\.1\s+Source-Appraisal Rubric\s*$(.*?)(?=^###\s*1\.2\b|^##\s|\Z)",
                      path.read_text(encoding="utf-8"), re.M | re.S)
    if not match:
        raise AgentError("Section 1.1 (Source-Appraisal Rubric) not found in the search strategy.")
    section = match.group(1)
    version = re.search(r"\*\*Rubric version:\s*([0-9.]+)\*\*", section)
    if not version or version.group(1) != expected_version:
        raise AgentError(f"The search strategy has rubric version {version and version.group(1)}, but the agent "
                         f"is set up for version {expected_version}. A researcher must confirm the new rubric first.")

    criteria = []
    for row in re.finditer(r"^\|\s*\*\*(.+?)\*\*\s*\|(.+?)\|(.+?)\|(.+?)\|\s*$", section, re.M):
        name = row.group(1).strip()
        if name in KEYS:
            criteria.append({"key": KEYS[name], "name": name,
                             "levels": [row.group(i).strip() for i in (2, 3, 4)]})
    tiers = [{"tier": m.group(3), "low": int(m.group(1)), "high": int(m.group(2)), "meaning": m.group(4).strip()}
             for m in re.finditer(r"\*\*(\d+)\s*[–-]\s*(\d+) points\s*[—–-]+\s*Tier ([A-Z]):\*\*\s*(.+)", section)]
    checks = {m.group(1): m.group(2).strip()
              for m in re.finditer(r"^- \*\*(" + "|".join(CHECKS) + r"):\*\*\s*(.+)$", section, re.M)}
    if [c["name"] for c in criteria] != list(KEYS) or len(tiers) != 3 or list(checks) != CHECKS:
        raise AgentError("The rubric in Section 1.1 could not be read completely (criteria, tiers or checks).")
    return {"version": version.group(1), "file": path.name, "criteria": criteria,
            "tiers": sorted(tiers, key=lambda t: -t["high"]), "checks": checks}


def tier_for(rubric: dict, total: int) -> str:
    return next(t["tier"] for t in rubric["tiers"] if t["low"] <= total <= t["high"])


def as_prompt_text(rubric: dict) -> str:
    lines = [f"Official rubric: {rubric['file']}, Section 1.1, version {rubric['version']}. "
             "Each criterion scores 0, 1 or 2 points (maximum 10)."]
    for c in rubric["criteria"]:
        lines.append(f"- {c['name']} (key: {c['key']})")
        lines += [f"    {i} = {text}" for i, text in enumerate(c["levels"])]
    lines.append("Tiers (calculated by the agent, not by you):")
    lines += [f"- {t['low']}-{t['high']} points = Tier {t['tier']}: {t['meaning']}" for t in rubric["tiers"]]
    lines.append("Additional checks (not scored; a high score does not override them):")
    lines += [f"- {name}: {q}" for name, q in rubric["checks"].items()]
    return "\n".join(lines)
