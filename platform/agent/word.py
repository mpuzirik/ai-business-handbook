"""Export a draft handbook page as a Word (.docx) file. Standard library only (a .docx is a zip of XML files)."""

from __future__ import annotations

import zipfile
from io import BytesIO
from xml.sax.saxutils import escape

KIND_LABEL = {"evidence": "Evidence", "interpretation": "Interpretation", "assumption": "Assumption",
              "recommendation": "Recommendation", "example": "Example"}

_CONTENT_TYPES = """<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<Types xmlns="http://schemas.openxmlformats.org/package/2006/content-types">
<Default Extension="rels" ContentType="application/vnd.openxmlformats-package.relationships+xml"/>
<Default Extension="xml" ContentType="application/xml"/>
<Override PartName="/word/document.xml" ContentType="application/vnd.openxmlformats-officedocument.wordprocessingml.document.main+xml"/>
<Override PartName="/word/styles.xml" ContentType="application/vnd.openxmlformats-officedocument.wordprocessingml.styles+xml"/>
</Types>"""
_RELS = """<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships">
<Relationship Id="rId1" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/officeDocument" Target="word/document.xml"/>
</Relationships>"""
_DOC_RELS = """<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships">
<Relationship Id="rId1" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/styles" Target="styles.xml"/>
</Relationships>"""
_STYLES = """<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<w:styles xmlns:w="http://schemas.openxmlformats.org/wordprocessingml/2006/main">
<w:docDefaults><w:rPrDefault><w:rPr><w:rFonts w:ascii="Calibri" w:hAnsi="Calibri" w:cs="Calibri"/><w:sz w:val="22"/></w:rPr></w:rPrDefault>
<w:pPrDefault><w:pPr><w:spacing w:after="120" w:line="276" w:lineRule="auto"/></w:pPr></w:pPrDefault></w:docDefaults>
<w:style w:type="paragraph" w:default="1" w:styleId="Normal"><w:name w:val="Normal"/></w:style>
<w:style w:type="paragraph" w:styleId="Title"><w:name w:val="Title"/><w:basedOn w:val="Normal"/><w:pPr><w:spacing w:after="80"/></w:pPr><w:rPr><w:b/><w:sz w:val="40"/><w:color w:val="1D2433"/></w:rPr></w:style>
<w:style w:type="paragraph" w:styleId="Heading1"><w:name w:val="heading 1"/><w:basedOn w:val="Normal"/><w:pPr><w:keepNext/><w:spacing w:before="280" w:after="80"/><w:outlineLvl w:val="0"/></w:pPr><w:rPr><w:b/><w:sz w:val="28"/><w:color w:val="2F5BEA"/></w:rPr></w:style>
<w:style w:type="paragraph" w:styleId="Heading2"><w:name w:val="heading 2"/><w:basedOn w:val="Normal"/><w:pPr><w:keepNext/><w:spacing w:before="200" w:after="60"/><w:outlineLvl w:val="1"/></w:pPr><w:rPr><w:b/><w:sz w:val="24"/></w:rPr></w:style>
<w:style w:type="paragraph" w:styleId="Small"><w:name w:val="Small"/><w:basedOn w:val="Normal"/><w:rPr><w:sz w:val="18"/><w:color w:val="667085"/></w:rPr></w:style>
</w:styles>"""


def _run(text: str, bold=False, italic=False, color=None, size=None) -> str:
    props = ("<w:b/>" if bold else "") + ("<w:i/>" if italic else "") + \
            (f'<w:color w:val="{color}"/>' if color else "") + (f'<w:sz w:val="{size}"/>' if size else "")
    return f'<w:r>{"<w:rPr>" + props + "</w:rPr>" if props else ""}<w:t xml:space="preserve">{escape(text)}</w:t></w:r>'


def _p(runs: str, style: str | None = None, indent: int = 0) -> str:
    ppr = (f'<w:pStyle w:val="{style}"/>' if style else "") + (f'<w:ind w:left="{indent}"/>' if indent else "")
    return f'<w:p>{"<w:pPr>" + ppr + "</w:pPr>" if ppr else ""}{runs}</w:p>'


def draft_to_docx(run: dict) -> bytes:
    d, s = run["draft"], run["source"]
    review = run.get("review")
    ev = {e["id"]: e for e in run["evidence"] or []}
    body = [_p(_run(d["title"]), "Title"),
            _p(_run("Question: " + run["question"], italic=True), "Small")]
    status = (f"Approved by {review['by']} on {review['at'][:10]}. Not published." if review
              else "DRAFT - not yet approved by a human reviewer.")
    body.append(_p(_run(status, bold=True, color="16874A" if review else "B25E00")))
    en_title = (run.get("translation") or {}).get("title")
    source_title = f"{en_title} (original: {s['title']})" if en_title and en_title != s["title"] else s["title"]
    body.append(_p(_run(f"Source: {source_title} - {s['organisation'] or 'organisation not recorded'}, "
                        f"{s['date'] or 'date not recorded'}. {s['url'] or s['file'] or ''}"), "Small"))

    cited = []
    for section in d["sections"]:
        body.append(_p(_run(section.get("heading") or ""), "Heading1"))
        for b in section.get("blocks") or []:
            cites = b.get("evidence") or []
            cited += [c for c in cites if c not in cited]
            label = KIND_LABEL.get(b.get("kind"), b.get("kind") or "")
            if b.get("kind") == "example" and not cites:
                label += " (hypothetical)"
            body.append(_p(_run(label + ": ", bold=True, color="667085", size=18) + _run(b.get("text") or "") +
                           (_run(" [" + ", ".join(cites) + "]", color="2F5BEA", size=18) if cites else "")))
    if d.get("decision_questions"):
        body.append(_p(_run("Questions for your agency"), "Heading1"))
        body += [_p(_run("•  " + q), indent=360) for q in d["decision_questions"]]

    body.append(_p(_run("Evidence used"), "Heading1"))
    body.append(_p(_run("Every citation above points to a quote in the original source (paragraph numbers refer to the "
                        "stored copy of the source)."), "Small"))
    for cid in cited:
        e = ev.get(cid)
        if not e:
            continue
        body.append(_p(_run(f"[{cid}] ", bold=True) + _run(e["claim"])))
        body.append(_p(_run(f"“{e['quote']}”", italic=True) + _run(f"  (paragraph {e['paragraph']})", color="667085"), indent=360))
        if e.get("quote_en"):
            body.append(_p(_run("English: " + e["quote_en"], color="667085"), indent=360))
    body.append(_p(_run(f"Produced with AEL Research Agent v0 ({run['id']}). The automated check confirms structure and "
                        "traceability only; it does not prove claims true."), "Small"))

    document = ('<?xml version="1.0" encoding="UTF-8" standalone="yes"?>'
                '<w:document xmlns:w="http://schemas.openxmlformats.org/wordprocessingml/2006/main"><w:body>'
                + "".join(body) +
                '<w:sectPr><w:pgSz w:w="11906" w:h="16838"/><w:pgMar w:top="1134" w:right="1134" w:bottom="1134" '
                'w:left="1134" w:header="708" w:footer="708" w:gutter="0"/></w:sectPr></w:body></w:document>')
    buf = BytesIO()
    with zipfile.ZipFile(buf, "w", zipfile.ZIP_DEFLATED) as z:
        z.writestr("[Content_Types].xml", _CONTENT_TYPES)
        z.writestr("_rels/.rels", _RELS)
        z.writestr("word/_rels/document.xml.rels", _DOC_RELS)
        z.writestr("word/document.xml", document)
        z.writestr("word/styles.xml", _STYLES)
    return buf.getvalue()
