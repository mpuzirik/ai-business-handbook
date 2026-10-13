"""Text tools (no AI): read a source, split it into paragraphs, check quotes and figures, spot privacy signals."""

from __future__ import annotations

import re
import sys
import urllib.error
import urllib.request
import zipfile
from html.parser import HTMLParser
from io import BytesIO
from pathlib import Path
from xml.etree import ElementTree


class AgentError(Exception):
    """A problem the researcher can fix. The message is shown in the control panel."""


# ---------------------------------------------------------------- reading a source

class _HtmlText(HTMLParser):
    SKIP = {"script", "style", "noscript", "nav", "header", "footer", "aside", "form", "svg", "button",
            "iframe", "template", "select", "figure"}
    BLOCK = {"p", "div", "section", "article", "main", "h1", "h2", "h3", "h4", "h5", "h6", "ul", "ol",
             "table", "tr", "blockquote", "pre", "li"}

    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.skip = self.main = 0
        self.all, self.main_parts, self.h1, self.title = [], [], "", ""
        self.in_h1 = self.in_title = False

    def _add(self, text):
        self.all.append(text)
        if self.main:
            self.main_parts.append(text)

    def handle_starttag(self, tag, attrs):
        if tag in self.SKIP:
            self.skip += 1
        elif tag in ("article", "main"):
            self.main += 1
        self.in_title = self.in_title or tag == "title"
        self.in_h1 = self.in_h1 or (tag == "h1" and not self.h1)
        if not self.skip and tag in self.BLOCK:
            self._add("\n\n" + ("- " if tag == "li" else ""))

    def handle_endtag(self, tag):
        if tag in self.SKIP and self.skip:
            self.skip -= 1
        elif tag in ("article", "main") and self.main:
            self.main -= 1
        if tag == "title":
            self.in_title = False
        if tag == "h1":
            self.in_h1 = False
        if not self.skip and tag in self.BLOCK:
            self._add("\n\n")

    def handle_data(self, data):
        if self.in_title:
            self.title += data
        if self.in_h1:
            self.h1 += data
        if not self.skip:
            self._add(re.sub(r"[ \t\r\f\v]+", " ", data))


def _tidy(raw: str) -> str:
    text = "\n".join(line.strip() for line in raw.replace(" ", " ").split("\n"))
    return re.sub(r"\n{3,}", "\n\n", text).strip() + "\n"


def html_to_text(html: str) -> tuple[str, str]:
    """(title, text) of a web page. Prefers the <article>/<main> part; drops menus, scripts and footers."""
    p = _HtmlText()
    p.feed(html)
    main = _tidy("".join(p.main_parts))
    text = main if len(main) > 400 else _tidy("".join(p.all))
    return re.sub(r"\s+", " ", p.h1 or p.title).strip(), text


def docx_to_text(data: bytes) -> str:
    try:
        with zipfile.ZipFile(BytesIO(data)) as z:
            xml = z.read("word/document.xml")
    except (zipfile.BadZipFile, KeyError) as exc:
        raise AgentError("This .docx file could not be read. Paste the text instead.") from exc
    ns = "{http://schemas.openxmlformats.org/wordprocessingml/2006/main}"
    paragraphs = ["".join(t.text or "" for t in p.iter(ns + "t")).strip() for p in ElementTree.fromstring(xml).iter(ns + "p")]
    return _tidy("\n\n".join(p for p in paragraphs if p))


def _pdf_paragraphs(page_text: str) -> list[str]:
    """PDF text comes line by line. Rebuild paragraphs: join wrapped lines, undo end-of-line hyphenation,
    and start a new paragraph after a blank line, a bullet, or a line that stops well short of the full width."""
    lines = [line.strip() for line in page_text.replace("\r", "").split("\n")]
    lengths = sorted(len(line) for line in lines if line)
    full = lengths[int(len(lengths) * 0.8)] if lengths else 0  # a typical full line
    paras, current = [], []
    for line in lines:
        if not line:
            if current:
                paras.append(" ".join(current))
            current = []
            continue
        if current:
            prev = current[-1]
            if prev.endswith("-") and line[:1].islower() and not prev.endswith(" -"):
                current[-1] = prev[:-1] + line  # "hyphen-\nated" -> "hyphenated"
                continue
            short_line = len(prev) < 0.7 * full  # wrapped lines run (almost) full width; a short one ends a paragraph or heading
            ends_sentence = re.search(r"[.!?:;\"\u201d)]$", prev) and len(prev) < 0.85 * full
            heading_next = (re.search(r"[.!?]$", prev) and len(line) < 0.6 * full
                            and not re.search(r"[.,;:]$", line))  # "... end of paragraph." then "A short heading"
            if short_line or ends_sentence or heading_next or re.match(r"^([\u2022\u25cf\u25aa\u2013*-]|\d{1,2}[.)])\s", line):
                paras.append(" ".join(current))
                current = []
        current.append(line)
    if current:
        paras.append(" ".join(current))
    return [re.sub(r"\s+", " ", p).strip() for p in paras if re.search(r"\w", p)]


def pdf_to_text(data: bytes) -> tuple[str, str]:
    """(title, text) of a PDF with a text layer. Each page starts with a '[Page N]' marker."""
    title, text, _ = _pdf_read(data)
    return title, text


def _pdf_read(data: bytes) -> tuple[str, str, dict]:
    vendor = str(Path(__file__).parent / "vendor")
    if vendor not in sys.path:
        sys.path.insert(0, vendor)  # the bundled pypdf, so nothing has to be installed
    import logging
    import warnings
    with warnings.catch_warnings():
        warnings.simplefilter("ignore")
        from pypdf import PdfReader
    logging.getLogger("pypdf").setLevel(logging.ERROR)
    try:
        reader = PdfReader(BytesIO(data))
        if reader.is_encrypted and not reader.decrypt(""):
            raise AgentError("This PDF is password-protected. Save an unprotected copy, or paste the text instead.")
        parts = []
        for number, page in enumerate(reader.pages, start=1):
            paras = _pdf_paragraphs(page.extract_text() or "")
            if paras:
                parts.append(f"[Page {number}]\n\n" + "\n\n".join(paras))
        info = {k: str(v).strip() for k, v in (reader.metadata or {}).items() if v}
        title = info.get("/Title", "")
    except AgentError:
        raise
    except Exception as exc:
        raise AgentError(f"This PDF could not be read ({exc}). Open it and paste the text instead.") from exc
    text = "\n\n".join(parts)
    if len(re.sub(r"\[Page \d+\]|\s", "", text)) < 100:
        raise AgentError("This PDF has no readable text (it is probably a scan or images). "
                         "Copy the text from the PDF and paste it instead.")
    if re.match(r"(?i)^(microsoft (word|powerpoint)|untitled|document\d*$)", title) or len(title) < 4:
        title = ""  # file-maker defaults are not real titles
    return title, _tidy(text), info


def upload_to_text(filename: str, data: bytes) -> str:
    suffix = "." + filename.lower().rsplit(".", 1)[-1] if "." in filename else ""
    if suffix == ".pdf" or data[:5] == b"%PDF-":
        return pdf_to_text(data)[1]
    if suffix == ".docx":
        return docx_to_text(data)
    if suffix in (".html", ".htm"):
        return html_to_text(data.decode("utf-8", errors="replace"))[1]
    if suffix in (".txt", ".md"):
        return data.decode("utf-8", errors="replace")
    raise AgentError(f"v0 cannot read '{suffix or filename}' files. Use .pdf, .docx, .txt, .md or .html, "
                     "or open the file and paste the text.")


def fetch_url(url: str) -> tuple[str, str]:
    """Download a web page: (title, text)."""
    if not re.match(r"^https?://", url):
        raise AgentError("The link must start with http:// or https://")
    request = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0 (AEL Research Agent v0)"})
    try:
        with urllib.request.urlopen(request, timeout=20) as resp:
            ctype = resp.headers.get("Content-Type", "").lower()
            body = resp.read(30_000_000)
            charset = resp.headers.get_content_charset() or "utf-8"
    except (urllib.error.URLError, TimeoutError, OSError) as exc:
        raise AgentError(f"Could not download the page ({exc}). Copy the text from your browser and paste it instead.") from exc
    if "pdf" in ctype or body[:5] == b"%PDF-":
        return pdf_to_text(body)
    title, text = html_to_text(body.decode(charset, errors="replace"))
    if len(text) < 200:
        raise AgentError("No readable text found on this page. Copy the text from your browser and paste it instead.")
    return title, text


# ---------------------------------------------------------------- details found in the source itself
# Only details the source states about itself (page metadata, file properties). Nothing is guessed:
# every detail says where it was found, and the researcher can change it.

class _MetaParser(HTMLParser):
    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.meta, self.lang, self.times, self.jsonld, self._ld = {}, "", [], [], None

    def handle_starttag(self, tag, attrs):
        a = {k.lower(): (v or "") for k, v in attrs}
        if tag == "html":
            self.lang = a.get("lang", "")
        elif tag == "meta":
            key = (a.get("property") or a.get("name") or a.get("itemprop") or "").lower()
            if key and a.get("content") and key not in self.meta:
                self.meta[key] = a["content"].strip()
        elif tag == "time" and a.get("datetime"):
            self.times.append(a["datetime"])
        elif tag == "script" and "ld+json" in a.get("type", ""):
            self._ld = []

    def handle_endtag(self, tag):
        if tag == "script" and self._ld is not None:
            self.jsonld.append("".join(self._ld))
            self._ld = None

    def handle_data(self, data):
        if self._ld is not None:
            self._ld.append(data)


def _iso_date(value: str) -> str | None:
    m = re.search(r"(\d{4})-?(\d{2})-?(\d{2})", value or "")
    if m and 1990 <= int(m.group(1)) <= 2100 and 1 <= int(m.group(2)) <= 12 and 1 <= int(m.group(3)) <= 31:
        return f"{m.group(1)}-{m.group(2)}-{m.group(3)}"
    return None


def _names(value) -> list[str]:
    """Names from JSON-LD author/publisher values (a string, an object or a list)."""
    if isinstance(value, list):
        return [n for v in value for n in _names(v)]
    if isinstance(value, dict):
        return [str(value.get("name")).strip()] if value.get("name") else []
    return [value.strip()] if isinstance(value, str) and value.strip() and not value.startswith("http") else []


def _combine(author: str | None, publisher: str | None) -> str | None:
    if author and publisher and author.lower() not in publisher.lower() and publisher.lower() not in author.lower():
        return f"{author} ({publisher})"
    return author or publisher


def html_details(html: str) -> dict:
    import json
    p = _MetaParser()
    try:
        p.feed(html)
    except Exception:  # broken markup: use what was read
        pass
    m, ld = p.meta, {}
    for block in p.jsonld:
        try:
            data = json.loads(block)
        except ValueError:
            continue
        items = data if isinstance(data, list) else data.get("@graph", [data]) if isinstance(data, dict) else []
        for item in items:
            if isinstance(item, dict) and (item.get("datePublished") or item.get("author") or item.get("headline")):
                ld = ld or item
    first = lambda *keys: next(((m[k], k) for k in keys if m.get(k)), (None, None))  # noqa: E731
    details = {}
    author, a_key = first("author", "article:author", "citation_author", "dc.creator", "dcterms.creator", "parsely-author")
    if author and author.startswith("http"):
        author = None
    if not author and _names(ld.get("author")):
        author, a_key = ", ".join(_names(ld.get("author"))[:3]), "structured data (author)"
    publisher, p_key = first("og:site_name", "citation_publisher", "dc.publisher", "dcterms.publisher", "application-name")
    if not publisher and _names(ld.get("publisher")):
        publisher, p_key = _names(ld.get("publisher"))[0], "structured data (publisher)"
    org = _combine(author, publisher)
    if org:
        used = [k for k, v in ((a_key, author), (p_key, publisher)) if v]
        details["organisation"] = {"value": org, "where": "page metadata (" + ", ".join(used) + ")"}
    date, d_key = None, None
    for key in ("article:published_time", "citation_publication_date", "citation_date", "dc.date", "dcterms.issued",
                "dcterms.date", "date", "pubdate", "publish-date", "datepublished"):
        if _iso_date(m.get(key, "")):
            date, d_key = _iso_date(m[key]), f"page metadata ({key})"
            break
    if not date and _iso_date(str(ld.get("datePublished", ""))):
        date, d_key = _iso_date(str(ld["datePublished"])), "structured data (datePublished)"
    if not date and p.times and _iso_date(p.times[0]):
        date, d_key = _iso_date(p.times[0]), "first date shown on the page"
    if date:
        details["date"] = {"value": date, "where": d_key}
    title = m.get("og:title") or m.get("citation_title") or (ld.get("headline") if isinstance(ld.get("headline"), str) else None)
    if title:
        details["title"] = {"value": title.strip(), "where": "page metadata"}
    lang = p.lang.lower()[:2]
    if lang in ("nl", "en"):
        details["language"] = {"value": lang, "where": "page language setting"}
    return details


def pdf_details(info: dict) -> dict:
    details = {}
    if info.get("/Author"):
        details["organisation"] = {"value": info["/Author"], "where": "PDF properties (Author)"}
    for key, label in (("/CreationDate", "creation date"), ("/ModDate", "last-modified date")):
        if _iso_date(info.get(key, "")):
            details["date"] = {"value": _iso_date(info[key]), "where": f"PDF properties ({label}) - check the date printed in the document"}
            break
    return details


def docx_details(data: bytes) -> dict:
    details = {}
    try:
        with zipfile.ZipFile(BytesIO(data)) as z:
            xml = z.read("docProps/core.xml").decode("utf-8", errors="replace")
    except (zipfile.BadZipFile, KeyError):
        return details
    creator = re.search(r"<dc:creator>([^<]+)</dc:creator>", xml)
    created = re.search(r"<dcterms:created[^>]*>([^<]+)<", xml)
    title = re.search(r"<dc:title>([^<]+)</dc:title>", xml)
    if creator:
        details["organisation"] = {"value": creator.group(1).strip(), "where": "Word file properties (author)"}
    if created and _iso_date(created.group(1)):
        details["date"] = {"value": _iso_date(created.group(1)), "where": "Word file properties (created) - check the date in the document"}
    if title:
        details["title"] = {"value": title.group(1).strip(), "where": "Word file properties (title)"}
    return details


_SOURCE_CACHE: dict[str, tuple[float, dict]] = {}


def read_source(url: str | None = None, filename: str | None = None, data: bytes | None = None,
                text: str | None = None) -> dict:
    """Read a source from an upload, pasted text or a link.

    Returns {"text", "title", "kind", "details"}: details = what the source states about itself
    ({field: {"value", "where"}}). No AI is used and nothing is guessed except the language.
    """
    import time
    details, title = {}, ""
    if data is not None and filename:
        if filename.lower().endswith(".pdf") or data[:5] == b"%PDF-":
            title, body, info = _pdf_read(data)
            kind, details = "pdf", pdf_details(info)
            if title:
                details["title"] = {"value": title, "where": "PDF properties (Title)"}
        else:
            body, kind = upload_to_text(filename, data), "file"
            if filename.lower().endswith(".docx"):
                details = docx_details(data)
            elif filename.lower().endswith((".html", ".htm")):
                html = data.decode("utf-8", errors="replace")
                title, details = html_to_text(html)[0], html_details(html)
    elif text and text.strip():
        body, kind = text, "paste"
    elif url:
        cached = _SOURCE_CACHE.get(url)
        if cached and time.time() - cached[0] < 900:
            return dict(cached[1])
        if not re.match(r"^https?://", url):
            raise AgentError("The link must start with http:// or https://")
        request = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0 (AEL Research Agent v0)"})
        try:
            with urllib.request.urlopen(request, timeout=20) as resp:
                ctype = resp.headers.get("Content-Type", "").lower()
                raw = resp.read(30_000_000)
                charset = resp.headers.get_content_charset() or "utf-8"
        except (urllib.error.URLError, TimeoutError, OSError) as exc:
            raise AgentError(f"Could not download the page ({exc}). Copy the text from your browser and paste it instead.") from exc
        if "pdf" in ctype or raw[:5] == b"%PDF-":
            title, body, info = _pdf_read(raw)
            kind, details = "pdf-link", pdf_details(info)
            if title:
                details["title"] = {"value": title, "where": "PDF properties (Title)"}
        else:
            html = raw.decode(charset, errors="replace")
            (title, body), details, kind = html_to_text(html), html_details(html), "web"
            if len(body) < 200:
                raise AgentError("No readable text found on this page. Copy the text from your browser and paste it instead.")
    else:
        raise AgentError("Give a link, upload a file, or paste the source text.")
    if title and "title" not in details:
        details["title"] = {"value": title, "where": "the source's own title"}
    if "language" not in details:
        details["language"] = {"value": guess_language(body), "where": "detected from the text"}
    result = {"text": body.replace("\r\n", "\n"), "title": title, "kind": kind, "details": details}
    if url and not (data or (text and text.strip())):
        _SOURCE_CACHE[url] = (time.time(), result)
    return dict(result)


def paragraphs(text: str) -> list[dict]:
    """Numbered paragraphs P1, P2 ... - the 'location' every piece of evidence points to."""
    blocks = [b.strip() for b in re.split(r"\n\s*\n", text.replace("\r\n", "\n"))]
    blocks = [b for b in blocks if b and re.search(r"\w", b)]  # drop lines that are only '-' etc.
    return [{"id": f"P{i}", "text": b} for i, b in enumerate(blocks, start=1)]


# ---------------------------------------------------------------- checks

_QUOTES = str.maketrans({"‘": "'", "’": "'", "“": '"', "”": '"', "„": '"', "–": "-", "—": "-", " ": " "})


def normalise(text: str) -> str:
    return re.sub(r"\s+", " ", (text or "").translate(_QUOTES)).strip().casefold()


def quote_in(quote: str, text: str) -> bool:
    """True if the quote appears word for word in the text (a '...' may skip words)."""
    parts = [normalise(p) for p in re.split(r"\s*(?:\.\.\.|…)\s*", quote or "") if normalise(p)]
    haystack, pos = normalise(text), 0
    for part in parts:
        pos = haystack.find(part, pos)
        if pos < 0:
            return False
        pos += len(part)
    return bool(parts)


def numbers_in(text: str) -> set[str]:
    """Figures in a text ('7,5' = '7.5'). Codes like P3 or E2 are not figures."""
    out = set()
    for raw in re.findall(r"(?<![A-Za-z])\d+(?:[.,]\d+)?", text or ""):
        value = raw.replace(",", ".")
        out.add(value.rstrip("0").rstrip(".") if "." in value else value)
    return out


OVERGENERAL = ["all agencies", "every agency", "all businesses", "every business", "always", "never", "guaranteed",
               "proven", "certainly", "without exception", "everyone", "will replace", "must adopt"]


def overgeneralisations(text: str) -> list[str]:
    low = normalise(text)
    return [t for t in OVERGENERAL if re.search(r"\b" + re.escape(t) + r"\b", low)]


# Wording that makes a page read as AI-written (Stage 8 warns; the Stage 7 prompt asks to avoid it).
AI_STOCK_PHRASES = [
    "delve", "in today's", "fast-paced", "ever-evolving", "ever-changing", "landscape", "game-changer", "game changer",
    "unlock", "harness the power", "leverage", "seamless", "seamlessly", "robust", "cutting-edge", "revolutionise",
    "revolutionize", "transformative", "paradigm", "synergy", "navigate the complexities", "it's important to note",
    "it is important to note", "it is worth noting", "it's worth noting", "in conclusion", "in summary", "furthermore",
    "moreover", "a testament to", "in the realm of", "embark", "tapestry", "pivotal", "crucial", "plays a vital role",
    "plays a crucial role", "not only", "whether you're", "at the end of the day", "elevate", "empower",
]


def ai_style_marks(text: str) -> list[str]:
    """Signs of AI-sounding text: dashes used as em-dashes and stock phrases. A hint for the reviewer, not an error."""
    raw, marks = text or "", []
    if "—" in raw or re.search(r"\s[–-]{1,2}\s", raw):
        marks.append("uses a dash (—) to join clauses; use a full stop, comma or colon")
    low = normalise(raw)
    marks += [f"stock phrase '{t}'" for t in AI_STOCK_PHRASES if re.search(r"\b" + re.escape(t) + r"\b", low)]
    return marks


def guess_language(text: str) -> str:
    words = re.findall(r"[a-zà-ÿ]+", (text or "").lower())
    nl = sum(w in {"de", "het", "een", "van", "en", "niet", "voor", "met", "zijn", "dat", "die", "ook", "wordt"} for w in words)
    en = sum(w in {"the", "and", "of", "to", "is", "not", "for", "with", "are", "that", "this", "by", "from"} for w in words)
    return "nl" if nl > 1.5 * en and nl >= 5 else "en"


_PRIVACY_SIGNALS = [
    ("email address", r"[\w.+-]+@[\w-]+\.[\w.-]+"),
    ("phone number", r"(?:\+31|0031|\b0)[\s-]?(?:6|[1-9]\d)[\s-]?\d{3,4}[\s-]?\d{3,4}\b"),
    ("interview speaker labels", r"(?im)^\s*(interviewer|respondent|interviewee|int\.|resp\.)\s*:"),
    ("recording timestamps", r"\[\d{1,2}:\d{2}(?::\d{2})?\]"),
    ("confidentiality marking", r"(?i)\b(confidential|vertrouwelijk|internal use only|niet verspreiden|do not distribute)\b"),
    ("personal ID number", r"(?i)\b(BSN|burgerservicenummer)\b"),
]


def privacy_signals(text: str) -> list[str]:
    """Names of privacy signals found (never the personal data itself)."""
    return [name for name, pattern in _PRIVACY_SIGNALS if re.search(pattern, text or "")]
