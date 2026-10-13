// AEL Research Agent v0 - control panel. Shows the run and sends button clicks to the agent.
// No research rules live here: the agent (agent/workflow.py) checks everything.
"use strict";

let CFG = null;
const $ = (s) => document.querySelector(s);
const main = $("#main");

function h(tag, attrs, ...kids) {
  const e = document.createElement(tag);
  for (const [k, v] of Object.entries(attrs || {})) {
    if (v === null || v === undefined || v === false) continue;
    if (k.startsWith("on")) e.addEventListener(k.slice(2), v);
    else if (k === "class") e.className = v;
    else e.setAttribute(k, v === true ? "" : v);
  }
  for (const k of kids.flat()) if (k !== null && k !== undefined && k !== false) e.append(k instanceof Node ? k : String(k));
  return e;
}
const note = (kind, text) => h("div", { class: "note " + kind }, text);

async function api(path, body) {
  const res = await fetch(path, body === undefined ? {} : { method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify(body) });
  const data = await res.json();
  if (res.status === 401 && data.signin && !/\/api\/sign(in|up)$/.test(path)) { USER = null; renderAccount(); showSignIn(); }
  if (res.status === 404 && data.error === "Unknown request.")
    throw new Error("The control panel was updated but is still running the old version. Close the black window, double-click start.bat again, then retry.");
  if (!res.ok) { const err = new Error(data.error || "Something went wrong."); err.answer = data.answer || null; throw err; }
  return data;
}
function toast(msg) { const t = $("#toast"); t.textContent = msg; t.hidden = false; clearTimeout(t._t); t._t = setTimeout(() => (t.hidden = true), Math.max(2500, msg.length * 60)); }
let USER = null;   // the signed-in account: { login, name }  (name = first + last name, shown in all logs)
let AI = { mode: "manual" };   // this account's AI settings: mode (manual | api), model, has_key (the key itself never comes back)
async function loadAI() { try { AI = await api("/api/settings"); } catch (e) { AI = { mode: "manual" }; } return AI; }
function me() {
  if (!USER) { showSignIn(); throw new Error("Please sign in first."); }
  return USER.name;
}
const myName = () => (USER ? USER.name : "");
// "Mine" = runs you started (the server decides, with the same rule as deleting)
const isMine = (x) => !!(x && x.mine);
const sameName = (a, b) => (a || "").trim().toLowerCase() === (b || "").trim().toLowerCase();
const fmtDate = (iso) => {
  if (!iso) return "";
  const d = new Date(iso), today = new Date();
  const time = d.toLocaleTimeString("en-GB", { hour: "2-digit", minute: "2-digit" });
  return d.toDateString() === today.toDateString() ? `Today ${time}` : d.toLocaleDateString("en-GB", { day: "numeric", month: "short", year: "numeric" });
};
const stateText = (x) => ({ done: "Finished", stopped: "Stopped", ai: "AI step",
  human: isMine(x) ? "Waiting for you" : "Needs a decision" }[x.who] + (x.who === "done" || x.who === "stopped" ? "" : ` · ${x.step}`));
// run an action from a button; show errors in the given box; re-draw with the new state
async function act(button, errBox, fn, done) {
  errBox.hidden = true;
  button.disabled = true;
  const label = button.textContent;
  button.classList.add("busy");
  button.textContent = "Working…";
  try {
    const view = await fn();
    if (done) toast(done);
    showRun(view);
    loadRuns();
    window.scrollTo({ top: 0, behavior: "smooth" });
  } catch (e) {
    errBox.textContent = e.message; errBox.hidden = false;
  } finally { button.disabled = false; button.classList.remove("busy"); button.textContent = label; }
}
const errorBox = () => h("div", { class: "note error", hidden: true });

// ------------------------------------------------------------------ start screen
function showNew() {
  location.hash = "#new";
  let mode = "link", file = null;
  const f = {};
  const field = (key, label, input) => {
    f[key] = input;
    const hint = h("span", { class: "hint", hidden: true });
    return h("label", { class: "f" }, label, input, hint);
  };
  const tabs = h("div", { class: "tabs" });
  const panes = {
    link: field("url", "Link to the source", h("input", { type: "url", placeholder: "https://..." })),
    upload: h("div", {}),
    paste: field("text", "Source text", h("textarea", { rows: 8, placeholder: "Paste the full text of the source here" })),
  };
  const fileInput = h("input", { type: "file", accept: ".pdf,.docx,.txt,.md,.html,.htm", hidden: true });
  const dropHint = "Drop a file here, or click to choose (.pdf, .docx, .txt, .md, .html)";
  const drop = h("div", { class: "drop", onclick: () => fileInput.click() }, dropHint);
  const pick = (chosen) => {
    file = chosen || null;
    drop.textContent = file ? `${file.name} (${Math.max(1, Math.round(file.size / 1024))} KB)` : dropHint;
    drop.classList.toggle("has", !!file);
    if (file) toB64(file).then((b64) => detect({ filename: file.name, file_b64: b64, material: material.value }));
  };
  fileInput.addEventListener("change", () => pick(fileInput.files[0]));
  // --- read the details the source states about itself (metadata / file properties) into EMPTY fields
  const auto = {};   // field -> value the agent filled in (so a new source can replace it, never your own typing)
  const found = h("div", { class: "found-note", hidden: true });
  const hints = {};
  const setField = (key, input, d) => {
    const mine = input.value.trim() && auto[key] !== input.value;
    if (!d || mine) return false;
    input.value = d.value; auto[key] = d.value;
    hints[key].textContent = "From the source: " + d.where; hints[key].hidden = false;
    return true;
  };
  let detectToken = 0;
  async function detect(body) {
    if (CFG.restricted.includes(material.value)) return;
    const token = ++detectToken;
    found.hidden = false; found.className = "found-note busy"; found.textContent = "Reading the source for details…";
    try {
      const d = await api("/api/detect", body);
      if (token !== detectToken) return;
      const filled = [];
      for (const key of ["title", "organisation", "date"]) if (setField(key, f[key], d.details[key])) filled.push(key);
      const lang = d.details.language;
      if (lang && (!language.value || auto.language === language.value)) {
        language.value = lang.value; auto.language = lang.value; language.dispatchEvent(new Event("change"));
        hints.language.textContent = (lang.where === "detected from the text" ? "Detected from the text" : "From the source: " + lang.where);
        hints.language.hidden = false; filled.push("language");
      }
      const missing = ["organisation", "date"].filter((k) => !f[k].value.trim());
      found.className = "found-note ok";
      found.textContent = (filled.length ? `Filled in from the source: ${filled.join(", ")}. Check them; you can change anything.` : "The source does not state extra details.")
        + (missing.length ? ` Not found: ${missing.join(", ")} (fill in if you know it).` : "");
    } catch (e) {
      if (token !== detectToken) return;
      found.className = "found-note warn"; found.textContent = e.message;
    }
  }
  drop.addEventListener("dragover", (e) => { e.preventDefault(); drop.classList.add("over"); });
  drop.addEventListener("dragleave", () => drop.classList.remove("over"));
  drop.addEventListener("drop", (e) => { e.preventDefault(); drop.classList.remove("over"); pick(e.dataTransfer.files[0]); });
  panes.upload.append(drop, fileInput);
  const setMode = (m) => {
    mode = m;
    for (const [k, pane] of Object.entries(panes)) pane.hidden = k !== m;
    [...tabs.children].forEach((b) => b.classList.toggle("on", b.dataset.m === m));
  };
  for (const [m, label] of [["link", "Link"], ["upload", "Upload a file"], ["paste", "Paste text"]])
    tabs.append(h("button", { type: "button", "data-m": m, onclick: () => setMode(m) }, label));

  const material = h("select", {}, Object.entries(CFG.material).map(([k, v]) => h("option", { value: k }, v + (CFG.restricted.includes(k) ? " (restricted)" : ""))));
  const privacy = h("select", {}, Object.entries(CFG.privacy).map(([k, v]) => h("option", { value: k, selected: k === "public" }, v)));
  const language = h("select", {}, h("option", { value: "" }, "Detect automatically"), h("option", { value: "en" }, "English"), h("option", { value: "nl" }, "Dutch"));
  const readsDutch = h("input", { type: "checkbox" });
  const dutchRow = h("label", { class: "check", hidden: true }, readsDutch, "I can read Dutch myself (skip the translation step)");
  language.addEventListener("change", () => (dutchRow.hidden = language.value !== "nl"));
  const restrictedNote = note("warn", "Restricted material is registered by name only. Its content is never read, stored or sent to an AI. The agent will stop at the privacy check.");
  restrictedNote.hidden = true;
  const sourceBox = h("div", {}, tabs, panes.link, panes.upload, panes.paste);
  material.addEventListener("change", () => {
    const r = CFG.restricted.includes(material.value);
    restrictedNote.hidden = !r; sourceBox.hidden = r;
  });
  hints.language = h("span", { class: "hint", hidden: true });
  const err = errorBox();
  const startBtn = h("button", { class: "btn big" }, "Start research");
  startBtn.addEventListener("click", () => act(startBtn, err, async () => {
    const form = {};
    for (const k of ["title", "organisation", "date", "intended_use", "question"]) form[k] = f[k].value;
    Object.assign(form, { material: material.value, privacy: privacy.value, language: language.value, reads_dutch: readsDutch.checked });
    const body = { form, reviewer: me() };
    if (CFG.restricted.includes(material.value)) { body.filename = file ? file.name : form.title; }
    else if (mode === "link") body.url = f.url.value;
    else if (mode === "paste") body.text = f.text.value;
    else if (file) { body.filename = file.name; body.file_b64 = await toB64(file); }
    else throw new Error("Choose a file first.");
    return api("/api/start", body);
  }, "Research started"));

  main.replaceChildren(
    h("h1", {}, "Start a research run"),
    h("p", { class: "muted" }, "Give one source. The agent takes it through the 9 workflow steps and stops whenever a decision belongs to you."),
    h("div", { class: "card" },
      h("h2", {}, "1. The source"), sourceBox, restrictedNote,
      h("h2", { style: "margin-top:16px" }, "2. What you know about it"),
      h("p", { class: "muted small" }, "Details the source states about itself (page metadata, file properties) are filled in for you, with where they were found. Anything still empty is flagged, never guessed."),
      found,
      h("div", { class: "grid" },
        field("title", "Title", h("input", { placeholder: "Taken from the page if empty" })),
        field("organisation", "Author / organisation", h("input", { placeholder: "e.g. CBS" })),
        field("date", "Publication date", h("input", { placeholder: "e.g. 2025-12-11" })),
        h("label", { class: "f" }, "Language", language, hints.language || ""),
        h("label", { class: "f" }, "What is it?", material),
        h("label", { class: "f" }, "Privacy status", privacy)),
      dutchRow,
      field("intended_use", "What do you want to use it for? (optional)", h("input", { placeholder: "e.g. figures on AI use in Dutch businesses" })),
      field("question", "Handbook question the page should answer (optional)", h("input", { placeholder: CFG.default_question })),
      err, h("div", { class: "row" }, startBtn, h("span", { class: "muted small" }, "Your earlier runs are under All research runs."))));
  renderWaiting();
  for (const key of ["title", "organisation", "date"]) {
    const el = f[key];
    hints[key] = el.nextSibling;
    el.addEventListener("input", () => { if (el.value !== auto[key]) { hints[key].hidden = true; delete auto[key]; } });
  }
  language.addEventListener("input", () => { hints.language.hidden = true; delete auto.language; });
  f.url.addEventListener("change", () => { const u = f.url.value.trim(); if (/^https?:\/\//.test(u)) detect({ url: u, material: material.value }); });
  setMode("link");
}
function toB64(file) {
  return new Promise((ok, fail) => { const r = new FileReader(); r.onload = () => ok(r.result.split(",")[1]); r.onerror = fail; r.readAsDataURL(file); });
}

// ------------------------------------------------------------------ run screen
function showRun(v) {
  location.hash = "#" + v.run.id;
  const r = v.run, s = r.source, st = v.status;
  const who = r.started_by || (CFG.runs.find((x) => x.id === r.id) || {}).owner;
  const metaBits = [s.organisation || "organisation not recorded", s.date || "date not recorded", s.language === "nl" ? "Dutch" : "English",
    `${r.id}${who ? " · started by " + who : ""} · ${fmtDate(r.created)}`];
  main.replaceChildren(
    h("h1", {}, (r.translation && r.translation.title) || s.title),
    r.translation && r.translation.title && r.translation.title !== s.title ? h("div", { class: "orig-title" }, "Original title: " + s.title) : "",
    h("div", { class: "muted small" }, metaBits.join(" · "), s.url ? [" · ", h("a", { href: s.url, target: "_blank", rel: "noopener" }, "open source")] : null),
    stepper(v),
    nowCard(v),
    ...results(v, st));
}

// ------------------------------------------------------------------ stepper with a short summary per step
const STEP_INFO = [
  "Reads the source and numbers its paragraphs (P1, P2 …). No AI.",
  "Checks whether the source may go to an AI. Restricted material is blocked; if unclear, you decide. No AI.",
  "Makes an English working translation of a Dutch source. The Dutch original stays the evidence.",
  "The AI suggests scores with rubric v1.0; you decide the final scores and whether the source is used.",
  "The AI proposes evidence; the agent checks every quote and figure against the source; you tick what may be used.",
  "Numbers the approved evidence (E1, E2 …) and hands only that to the draft. No AI.",
  "The AI writes a handbook page from the approved evidence only.",
  "Checks citations, figures, required sections and wording. Structure and traceability, not truth. No AI.",
  "You approve the page or request changes. Nothing is published.",
];
const plural = (n, word) => `${n} ${word}${n === 1 ? "" : "s"}`;

function stepSummary(n, v) {
  const r = v.run, s = r.source, ev = r.evidence || [], ai = r.appraisal.ai, hm = r.appraisal.human;
  const approved = ev.filter((e) => e.approved);
  switch (n) {
    case 1: {
      const lines = [s.capture || "Registered by name only (restricted material)."];
      if (r.paragraphs.length) lines.push(`${plural(r.paragraphs.length, "numbered paragraph")} (P1–P${r.paragraphs.length}).`);
      const found = Object.entries(s.found_in_source || {}).filter(([k]) => k !== "language").map(([k, d]) => `${k}: ${d.value}`);
      if (found.length) lines.push("Stated in the source itself: " + found.join(" · "));
      const missing = ["organisation", "date"].filter((k) => !s[k]);
      if (missing.length) lines.push("Not recorded: " + missing.join(", ") + ".");
      return lines;
    }
    case 2: {
      const p = r.privacy;
      const lines = [{ clear: "Passed: public source, no privacy signals.", allowed: "Allowed by a person.", blocked: "Blocked.", ask: "Waiting for your decision." }[p.result] || "", p.reason];
      if (p.decided_by) lines.push(`Decided by ${p.decided_by}: ${p.note}`);
      return lines;
    }
    case 3: {
      const tr = r.translation;
      if (!tr || !tr.needed) return [s.language === "nl" ? "Not needed: you read Dutch yourself." : "Not needed: the source is in English."];
      if (!tr.paragraphs) return ["Waiting for the AI translation."];
      const lines = [`${plural(Object.keys(tr.paragraphs).length, "paragraph")} translated into English (working translation).`];
      if ((tr.uncertain_terms || []).length) lines.push(`${plural(tr.uncertain_terms.length, "uncertain term")} flagged by the AI.`);
      const figs = (tr.notes || []).filter((x) => String(x).includes("figures differ"));
      if (figs.length) lines.push(`${plural(figs.length, "paragraph")} where figures differ from the original: check these.`);
      return lines;
    }
    case 4: {
      const lines = [];
      if (ai) lines.push(`AI suggested ${ai.total}/10, Tier ${ai.tier} (provisional).`);
      if (hm) lines.push("The decision is saved in the appraisal feedback log and calibrates future Stage 4 prompts.");
      if (hm) {
        lines.push(`${hm.by} ${hm.decision} the source with ${hm.total}/10, Tier ${hm.tier}.`);
        if (hm.changed.length) lines.push("Scores changed by the researcher: " + hm.changed.map((k) => k.replace(/_/g, " and ").replace("independence and bias", "independence and bias")).join(", ") + ".");
        if (hm.note) lines.push("Note: " + hm.note);
      } else if (ai) lines.push("Waiting for your decision.");
      return lines;
    }
    case 5: {
      if (!r.evidence) return ["Waiting for the AI's evidence proposal."];
      const bad = ev.filter((e) => e.problems.length).length;
      const lines = [`${plural(ev.length, "item")} proposed by the AI; ${bad} failed the automatic quote or figure check.`];
      if (r.evidence_review) lines.push(`${r.evidence_review.by} approved ${approved.length}: ${approved.map((e) => e.id).join(", ") || "none"}.`);
      else lines.push("Waiting for you to tick the usable items.");
      return lines;
    }
    case 6:
      return [`${plural(approved.length, "approved evidence item")} (${approved.map((e) => e.id).join(", ")}) handed to the draft. Rejected items are never used.`];
    case 7: {
      const d = r.draft;
      const lines = d ? [`"${d.title}"`, `${plural(d.sections.length, "section")}, ${plural(d.sections.reduce((a, x) => a + (x.blocks || []).length, 0), "labelled block")}.`] : ["Waiting for the AI draft."];
      if (d && d.style_rewrite) lines.push(`Wording rewritten for style (asked by ${d.style_rewrite.by}); claims, figures and citations checked unchanged.`);
      const earlier = r.history.filter((x) => x.draft || (x.data && x.data.draft)).length;
      if (earlier) lines.push(`${plural(earlier, "earlier draft")} kept in the history.`);
      const resets = r.history.filter((x) => x.reset_from);
      if (resets.length) lines.push(`Redone after a change: ${resets.map((x) => x.reason).join("; ")}.`);
      return lines;
    }
    case 8: {
      const c = r.check;
      if (!c) return ["Runs automatically after each draft."];
      const verify = c.items.filter((i) => i.level === "verify").length;
      return [`${plural(c.errors, "error")}, ${plural(c.warnings, "warning")}, ${plural(verify, "point")} for a person to verify.`,
        c.errors ? "Errors block approval: ask for a new draft." : "No errors: the page can go to the final review."];
    }
    case 9: {
      if (r.review) return [`Approved by ${r.review.by} on ${r.review.at.slice(0, 10)}.`, "Not published: publication is a separate manual step."];
      const asked = r.history.filter((x) => x.change_request).map((x) => `${x.change_request.by}: "${x.change_request.note}"`);
      return [r.draft && !r.check.errors ? "Waiting for your final review." : "Not reached yet.", ...asked.map((a) => "Changes requested earlier by " + a)];
    }
  }
  return [];
}

// "Change this step": go back to a completed step. The agent compares the new outcome with the old one.
const REDO_TEXT = { 2: "Blocking the source now removes its text and everything after the privacy check.",
  3: "If the new translation differs, the appraisal and everything after it are redone.",
  4: "Only a different decision or tier redoes the evidence, draft and review; score changes within the same tier keep them.",
  5: "Only a different selection redoes the draft and review.",
  9: "Withdraws the approval; the draft stays as it is." };
function stepActions(x, v) {
  const r = v.run, n = x.n;
  if (x.state === "todo" || r.reopened) return r.reopened && r.reopened.stage === n ? h("div", { class: "step-actions muted small" }, "This step is open for changes below.") : null;
  const err = errorBox();
  const ok = { 2: r.privacy.result === "allowed", 3: !!(r.translation && r.translation.paragraphs), 4: !!r.appraisal.human,
    5: !!r.evidence_review, 9: !!r.review }[n];
  if (ok) {
    const btn = h("button", { class: "btn light" }, n === 9 ? "Withdraw approval" : "Change this step");
    btn.addEventListener("click", () => act(btn, err, () => api(`/api/run/${r.id}/reopen`, { reviewer: me(), stage: n }), `Step ${n} reopened`));
    return h("div", { class: "step-actions" }, h("p", { class: "small muted" }, REDO_TEXT[n]), h("div", { class: "row" }, btn), err);
  }
  if (n === 7 && r.draft && x.state === "done") {
    const note = h("textarea", { class: "f", rows: 2, placeholder: "What should the new draft change?" });
    const btn = h("button", { class: "btn light" }, "Ask for a new draft");
    btn.addEventListener("click", () => act(btn, err, () => api(`/api/run/${r.id}/redraft`, { reviewer: me(), note: note.value }), "New draft requested"));
    return h("div", { class: "step-actions" }, h("p", { class: "small muted" }, "The current draft is kept in the history; the check and review are redone."), note, h("div", { class: "row" }, btn), err);
  }
  if (n === 1 && r.paragraphs.length) {
    const s = r.source, f = {};
    const inp = (key, label, value, ph) => { f[key] = h("input", { value: value || "", placeholder: ph || "" }); return h("label", { class: "f" }, label, f[key]); };
    const btn = h("button", { class: "btn light" }, "Save details");
    btn.addEventListener("click", () => act(btn, err, () => api(`/api/run/${r.id}/details`, { reviewer: me(),
      fields: Object.fromEntries(Object.entries(f).map(([k, el]) => [k, el.value])) }), "Details saved"));
    return h("details", { class: "step-actions edit-details" }, h("summary", {}, "Edit source details"),
      h("div", { class: "grid" }, inp("title", "Title", s.title), inp("organisation", "Author / organisation", s.organisation),
        inp("date", "Publication date", s.date, "e.g. 2025-12-11"), inp("intended_use", "Intended use", s.intended_use)),
      inp("question", "Handbook question", r.question),
      h("p", { class: "small muted" }, "Changing the organisation, date or intended use redoes the appraisal and what follows. Changing the question needs a new draft. A title change needs no redo."),
      h("div", { class: "row" }, btn), err);
  }
  return null;
}

function stepper(v) {
  const wrap = h("div", { class: "stepwrap" });
  const panel = h("div", { class: "stepinfo", hidden: true });
  const row = h("div", { class: "steps" });
  let open = null;
  v.stages.forEach((x) => {
    const btn = h("button", { type: "button", class: "step " + x.state, "aria-expanded": "false" },
      h("b", {}, x.state === "done" ? "✓" : x.state === "skipped" ? "–" : x.n), h("span", {}, x.name));
    btn.addEventListener("click", () => {
      [...row.children].forEach((b) => { b.classList.remove("open"); b.setAttribute("aria-expanded", "false"); });
      if (open === x.n) { open = null; panel.hidden = true; return; }
      open = x.n; btn.classList.add("open"); btn.setAttribute("aria-expanded", "true");
      const reached = x.state !== "todo";
      const label = { done: "Done", skipped: "Skipped", ai: "AI step now", human: "Your turn", stopped: "Stopped", todo: "Not reached yet" }[x.state];
      panel.replaceChildren(
        h("div", { class: "stepinfo-head" }, h("b", {}, `Step ${x.n} · ${x.name}`), h("span", { class: "tag " + (x.state === "todo" || x.state === "skipped" ? "idle" : x.state) }, label),
          h("button", { type: "button", class: "close", "aria-label": "Close", onclick: () => btn.click() }, "×")),
        h("p", { class: "muted small" }, STEP_INFO[x.n - 1]),
        reached ? h("ul", {}, stepSummary(x.n, v).filter(Boolean).map((line) => h("li", {}, line))) : null,
        stepActions(x, v));
      panel.hidden = false;
      const caret = btn.offsetLeft + btn.offsetWidth / 2;
      panel.style.setProperty("--caret", `${Math.max(24, Math.min(caret, row.offsetWidth - 24))}px`);
    });
    row.append(btn);
  });
  wrap.append(row, panel);
  return wrap;
}

function nowCard(v) {
  const st = v.status, who = st.who;
  const label = { ai: "AI step", human: "Your decision", stopped: "Stopped", done: "Finished" }[who];
  const ro = v.run.reopened;
  const keepErr = errorBox();
  const banner = ro ? h("div", { class: "reopen-banner" },
    h("div", {}, h("b", {}, `You reopened step ${ro.stage} to change it.`),
      h("div", { class: "small" }, `If the outcome stays the same, everything after it is kept. If it changes, the steps that depend on it are redone (earlier work stays in the history).`)),
    h("button", { class: "btn light", onclick: (e) => act(e.currentTarget, keepErr, () => api(`/api/run/${v.run.id}/keep`, { reviewer: me() }), "Kept as it was") }, "Keep it as it was"),
    keepErr) : null;
  const card = h("div", { class: "card now " + who },
    banner,
    h("span", { class: "tag " + who }, label),
    h("h2", {}, `Step ${st.stage} · ${CFG.stages[st.stage - 1]}`),
    h("p", {}, st.message));
  if (who === "ai") card.append(aiStep(v));
  else if (who === "human") card.append({ 2: privacyDecision, 4: appraisalDecision, 5: evidenceDecision, 8: redraft, 9: finalReview }[st.stage](v));
  return card;
}

// A switch between manual (copy and paste) and automatic (Claude API). Saved per account.
function modeSwitch(onChange) {
  const input = h("input", { type: "checkbox", role: "switch", "aria-label": "Automatic mode (Claude API)" });
  input.checked = AI.mode === "api";
  const label = (on) => [h("span", { class: on ? "" : "on" }, "Manual paste"), h("span", { class: "switch" }, input, h("i", {})), h("span", { class: on ? "on" : "" }, "Automatic (Claude API)")];
  const wrap = h("label", { class: "mode-switch" }, ...label(input.checked));
  input.addEventListener("change", async () => {
    const mode = input.checked ? "api" : "manual";
    try { AI = await api("/api/settings", { mode }); toast(mode === "api" ? "Automatic mode: AI steps are sent to Claude" : "Manual mode: copy and paste the prompts"); }
    catch (e) { input.checked = !input.checked; toast(e.message); return; }
    if (onChange) onChange();
  });
  return wrap;
}

function aiStep(v) {
  const holder = h("div", {});
  const draw = () => holder.replaceChildren(aiStepBody(v, () => draw()));
  draw();
  return holder;
}

function aiStepBody(v, redraw) {
  const answer = h("textarea", { class: "f", rows: 6, placeholder: "Paste Claude's complete answer here (it starts with { )" });
  const err = errorBox();
  const copy = h("button", { class: "btn light", onclick: async (e) => {
    const b = e.currentTarget;
    try { await navigator.clipboard.writeText(v.prompt); } catch (err) { toast("Copy failed: open 'Show the prompt' and copy it by hand."); return; }
    b.textContent = "Copied ✓"; b.classList.add("done"); setTimeout(() => { b.textContent = "Copy prompt"; b.classList.remove("done"); }, 2000);
  } }, "Copy prompt");
  const send = h("button", { class: "btn" }, "Submit answer");
  send.addEventListener("click", () => act(send, err, () => api(`/api/run/${v.run.id}/answer`, { answer: answer.value }), "Answer accepted"));
  const pasteHint = h("div", { class: "paste-hint" });
  const checkPaste = () => {
    const s = answer.value.trim(), a = s.indexOf("{"), b = s.lastIndexOf("}");
    let ok = false;
    if (a >= 0 && b > a) { try { JSON.parse(s.slice(a, b + 1)); ok = true; } catch (e) { ok = false; } }
    pasteHint.textContent = !s ? "" : ok ? "Looks complete. The agent will now check the content." : "This doesn't look complete yet. Paste Claude's whole answer, from { to }.";
    pasteHint.className = "paste-hint " + (!s ? "" : ok ? "ok" : "warn");
  };
  answer.addEventListener("input", checkPaste);
  answer.addEventListener("keydown", (e) => { if (e.key === "Enter" && (e.ctrlKey || e.metaKey)) send.click(); });
  const task = v.status.task;
  const chat = { translate: "Step 3 – Translation", appraise: "Step 4 – Appraisal", extract: "Step 5 – Evidence extraction", draft: "Step 7 – Draft", polish: "Step 7b – Style rewrite" }[task];
  const extras = [];
  if (task === "appraise") extras.push(note("info", v.calibration
    ? `This prompt includes calibration from ${plural(v.calibration, "earlier researcher decision")} (how often researchers changed the AI's scores, and why). The rubric v1.0 still decides the scores; you still decide the appraisal.`
    : "No earlier appraisal decisions are recorded yet. From the first decision on, Stage 4 prompts carry the researchers' corrections as calibration."));
  if (task === "polish") {
    const cancel = h("button", { class: "btn light" }, "Cancel the rewrite (keep the draft)");
    cancel.addEventListener("click", () => act(cancel, err, () => api(`/api/run/${v.run.id}/cancel_polish`, { reviewer: me() }), "Draft kept as it was"));
    extras.push(h("div", { class: "row" }, cancel));
  }
  const manual = [
    h("ol", { class: "howto" },
      h("li", {}, copy, " "),
      h("li", {}, `Paste it into your "${chat}" chat in Claude (a new chat for each source).`),
      h("li", {}, "Paste Claude's answer below and submit. The agent checks it before storing it.")),
    answer, pasteHint, err, h("div", { class: "row" }, send, h("span", { class: "muted small" }, "or Ctrl+Enter"))];
  const prompt = h("details", { class: "prompt" }, h("summary", { class: "small muted" }, "Show the prompt"), h("pre", {}, v.prompt));
  const sw = modeSwitch(redraw);
  if (AI.mode !== "api") return h("div", {}, sw, ...extras, ...manual, prompt);

  // automatic mode: one click sends the same prompt to Claude; the reply goes through the same checks
  const autoErr = errorBox();
  const run = h("button", { class: "btn" }, "Run with Claude");
  const waitNote = h("p", { class: "small muted", hidden: true }, "Claude is working on it. Long sources can take a few minutes; keep this page open.");
  const ready = AI.has_key && AI.sdk_installed;
  run.disabled = !ready || v.calling;
  run.addEventListener("click", async () => {
    autoErr.hidden = true; run.disabled = true; run.classList.add("busy"); run.textContent = "Claude is working…"; waitNote.hidden = false;
    try {
      const view = await api(`/api/run/${v.run.id}/claude`, {});
      toast("Claude's answer was checked and accepted"); showRun(view); loadRuns(); window.scrollTo({ top: 0, behavior: "smooth" });
    } catch (e) {
      autoErr.textContent = e.message; autoErr.hidden = false;
      if (e.answer) { answer.value = e.answer; checkPaste(); byHand.open = true; }
      run.disabled = false; run.classList.remove("busy"); run.textContent = "Run with Claude"; waitNote.hidden = true;
    }
  });
  const missing = !AI.sdk_installed ? note("warn", "Automatic mode needs the Anthropic Python package: close the black window, run  py -m pip install anthropic  in a command prompt, then start start.bat again.")
    : !AI.has_key ? h("div", { class: "note warn" }, "No Claude API key saved yet. ", h("button", { class: "linkbtn", type: "button", onclick: () => aiSettings(redraw) }, "Add one in AI settings"), ".") : null;
  const byHand = h("details", { class: "byhand" }, h("summary", { class: "small muted" }, "Or paste an answer by hand"), ...manual);
  return h("div", {}, sw, ...extras, missing,
    h("p", { class: "small muted" }, `Sends this prompt to ${(AI.models || {})[AI.model] || AI.model} with your API key. The agent checks Claude's answer exactly like a pasted one before storing it.`),
    v.calling ? note("info", "Claude is already working on this step (started from another window). Reload in a moment.") : null,
    autoErr, h("div", { class: "row" }, run, h("button", { class: "linkbtn", type: "button", onclick: () => aiSettings(redraw) }, "AI settings")), waitNote,
    byHand, prompt);
}

function privacyDecision(v) {
  const why = h("textarea", { class: "f", rows: 2, placeholder: "Reason (required), e.g. consent form signed, names removed" });
  const err = errorBox();
  const go = (allow) => (e) => act(e.currentTarget, err, () => api(`/api/run/${v.run.id}/privacy`, { reviewer: me(), allow, note: why.value }), allow ? "AI processing allowed" : "Source blocked");
  return h("div", {}, why, err, h("div", { class: "row" },
    h("button", { class: "btn green", onclick: go(true) }, "Allow AI processing"),
    h("button", { class: "btn red", onclick: go(false) }, "Block this source")));
}

function tierOf(total) { return CFG.rubric.tiers.find((t) => t.low <= total && total <= t.high).tier; }

function appraisalDecision(v) {
  const ai = v.run.appraisal.ai, mine = {};
  const totalBox = h("div", { class: "total" });
  const noteBox = h("textarea", { class: "f", rows: 2, placeholder: "Your note (required if you change a score; for Tier B, say what it may be used for)" });
  const approve = h("button", { class: "btn green" }, "Approve source");
  const reject = h("button", { class: "btn red" }, "Reject source");
  const update = () => {
    const total = Object.values(mine).reduce((a, b) => a + b, 0), tier = tierOf(total);
    const meaning = CFG.rubric.tiers.find((t) => t.tier === tier).meaning;
    totalBox.replaceChildren(`Your total: ${total}/10`, h("span", { class: "tier " + tier }, "Tier " + tier), h("span", { class: "small muted", style: "font-weight:400" }, meaning));
    approve.disabled = tier === "C";
    approve.title = tier === "C" ? "Tier C sources cannot be accepted (rubric v1.0)" : "";
  };
  const earlier = (((v.run.reopened || {}).saved || {}).appraisal || {}).human;
  if (earlier && earlier.note) noteBox.value = earlier.note;
  const rows = CFG.rubric.criteria.map((c) => {
    const a = ai.scores[c.key];
    const start = earlier ? earlier.scores[c.key] : a.score;
    mine[c.key] = start;
    const seg = h("div", { class: "seg" });
    [0, 1, 2].forEach((n) => seg.append(h("button", {
      type: "button", class: n === start ? "on" : "", title: c.levels[n],
      onclick: (e) => { mine[c.key] = n; [...seg.children].forEach((b, i) => b.classList.toggle("on", i === n)); update(); },
    }, n)));
    [...seg.children][a.score].classList.add("ai-pick");
    return h("tr", {},
      h("td", {}, h("b", {}, c.name), h("div", { class: "meta" }, c.levels[a.score])),
      h("td", {}, h("b", {}, `AI: ${a.score}`), " – ", a.reason, a.paragraphs.length ? h("div", { class: "meta" }, "See " + a.paragraphs.join(", ")) : null),
      h("td", {}, seg));
  });
  const err = errorBox();
  const send = (decision) => (e) => act(e.currentTarget, err, () => api(`/api/run/${v.run.id}/appraisal`, { reviewer: me(), scores: mine, decision, note: noteBox.value }), decision === "accepted" ? "Source approved" : "Source rejected");
  approve.addEventListener("click", send("accepted"));
  reject.addEventListener("click", send("rejected"));
  update();
  const extras = [...ai.flags.map((x) => x), ...ai.questions.map((x) => "Question: " + x)];
  return h("div", {},
    h("table", { class: "scores" }, h("tr", {}, h("th", {}, "Criterion"), h("th", {}, "AI suggestion (provisional)"), h("th", {}, "Your score")), rows),
    totalBox,
    Object.keys(ai.checks).length ? h("div", { class: "checks" }, h("div", { class: "checks-title" }, "Additional checks (AI suggestion)"), Object.entries(ai.checks).map(([k, x]) => h("div", { class: "checkrow" }, h("b", {}, k.replace(/_/g, " ").replace(/^./, (c) => c.toUpperCase())), h("span", {}, x)))) : null,
    extras.length ? note("warn", extras.join("\n")) : null,
    noteBox, h("p", { class: "small muted" }, "Your scores and note are saved in the appraisal feedback log, next to the AI's suggestion. Future Stage 4 prompts use them as calibration examples, so a short, concrete reason for each change helps the AI most."),
    err, h("div", { class: "row" }, approve, reject));
}

function evidenceCard(e, withBox, onToggle) {
  const bad = e.problems.length > 0;
  const box = withBox ? h("input", { type: "checkbox", disabled: bad, onchange: onToggle }) : null;
  const card = h("label", { class: "ev" + (bad ? " bad" : e.approved ? " yes" : "") }, box,
    h("div", {},
      h("div", { class: "claim" }, `${e.id} · ${e.claim}`),
      h("blockquote", {}, `"${e.quote}"`),
      e.quote_en ? h("div", { class: "meta" }, "English: " + e.quote_en) : null,
      h("div", { class: "meta" }, `${e.type} · paragraph ${e.paragraph || "?"}`, e.limitation ? ` · scope: ${e.limitation}` : "",
        !withBox && e.approved !== null ? (e.approved ? " · approved" : " · not used") : ""),
      bad ? h("div", { class: "meta", style: "color:var(--red)" }, "Cannot be approved: " + e.problems.join("; ")) : null));
  return { card, box };
}

function evidenceDecision(v) {
  const chosen = new Set();
  const count = h("span", { class: "muted small" });
  const send = h("button", { class: "btn" });
  const refresh = () => { send.textContent = `Confirm selection (${chosen.size} approved)`; };
  const boxes = [];
  const list = v.run.evidence.map((e) => {
    const { card, box } = evidenceCard(e, true, () => { box.checked ? chosen.add(e.id) : chosen.delete(e.id); card.classList.toggle("yes", box.checked); refresh(); });
    if (v.run.reopened && e.approved && !e.problems.length) { box.checked = true; chosen.add(e.id); card.classList.add("yes"); }
    boxes.push(box);
    return card;
  });
  const setAll = (on) => boxes.forEach((b) => { if (!b.disabled && b.checked !== on) { b.checked = on; b.dispatchEvent(new Event("change")); } });
  const passed = v.run.evidence.filter((e) => !e.problems.length).length;
  const err = errorBox();
  send.addEventListener("click", () => act(send, err, () => api(`/api/run/${v.run.id}/evidence`, { reviewer: me(), approved: [...chosen] }), "Evidence review saved"));
  refresh();
  return h("div", {},
    h("div", { class: "ev-tools" },
      h("span", { class: "small muted" }, `${passed} of ${v.run.evidence.length} passed the automatic quote check. Only ticked items can be used in the draft.`),
      h("button", { type: "button", class: "linkbtn", onclick: () => setAll(true) }, "Select all that passed"),
      h("button", { type: "button", class: "linkbtn", onclick: () => setAll(false) }, "Clear")),
    list, err, h("div", { class: "row" }, send, count));
}

function redraft(v) {
  const errors = v.run.check.items.filter((i) => i.level === "error").map((i) => "- " + i.text).join("\n");
  const text = h("textarea", { class: "f", rows: 4 }, "Fix these problems:\n" + errors);
  const err = errorBox();
  const btn = h("button", { class: "btn" }, "Ask for a new draft");
  btn.addEventListener("click", () => act(btn, err, () => api(`/api/run/${v.run.id}/redraft`, { reviewer: me(), note: text.value }), "New draft requested"));
  return h("div", {}, note("error", errors), h("p", { class: "small" }, "These notes are added to the next draft prompt:"), text, err, h("div", { class: "row" }, btn));
}

function finalReview(v) {
  const c = v.run.check;
  const text = h("textarea", { class: "f", rows: 2, placeholder: "Notes (required when you request changes)" });
  const err = errorBox();
  const go = (decision) => (e) => act(e.currentTarget, err, () => api(`/api/run/${v.run.id}/review`, { reviewer: me(), decision, note: text.value }), decision === "approve" ? "Page approved" : "Changes requested");
  const styleCount = c.items.filter((i) => i.group === "Wording & style").length;
  const polish = h("button", { class: "btn light" }, "Rewrite to sound less AI-written");
  polish.addEventListener("click", () => act(polish, err, () => api(`/api/run/${v.run.id}/polish`, { reviewer: me(), note: text.value }), "Style rewrite requested"));
  return h("div", {},
    note(c.warnings ? "warn" : "ok", `Automated check: ${c.errors} errors, ${c.warnings} warnings. Read the draft and the check below, and verify the points marked in blue.`),
    text, err, h("div", { class: "row" },
      h("button", { class: "btn green", onclick: go("approve") }, "Approve page"),
      h("button", { class: "btn red", onclick: go("changes") }, "Request changes"), polish),
    h("p", { class: "small muted" }, (styleCount ? `The check found ${plural(styleCount, "wording point")} that can make the page read as AI-written. ` : "") +
      "The style rewrite changes wording only: the agent refuses it if any section, label, citation or figure changes. Anything typed in the notes box is passed on as extra wishes."));
}

// ------------------------------------------------------------------ results (below the current step)
function section(title, open, ...body) {
  return h("details", { class: "sec", open: open || null }, h("summary", {}, title), h("div", {}, ...body));
}

// Send to wiki: put this run (inputs, AI suggestions, decisions, outputs) in the team's LLM wiki, with its source page
// and, once approved, its handbook page (agent/wiki.py)
function wikiReady(r) {
  return r.source.material === "published" && r.source.privacy !== "confidential" && ["clear", "allowed"].includes(r.privacy.result);
}
function wikiCard(v, st) {
  const r = v.run, w = r.wiki, s = v.wiki || {};
  const folder = h("input", { type: "text", spellcheck: "false", value: s.folder || "", placeholder: "C:\\Users\\you\\Documents\\GitHub\\ael-llm-wiki" });
  const push = h("input", { type: "checkbox" }); push.checked = s.push !== false;
  const err = errorBox();
  const btn = h("button", { class: "btn green" }, w ? "Update the wiki" : "Send to wiki");
  btn.addEventListener("click", () => act(btn, err, () => api(`/api/run/${r.id}/wiki`, { reviewer: me(), folder: folder.value, push: push.checked }), "Wiki updated"));
  const accepted = r.appraisal.human && r.appraisal.human.decision === "accepted" && (r.evidence || []).some((e) => e.approved);
  const approvedPage = r.review && r.review.decision === "approved";
  const what = ["the run page (the source details, the AI's suggestions next to your decisions, every evidence item, the check, the review and the activity log)",
    accepted ? "the source text and a source page from the approved evidence, if this source is not in the wiki yet" : null,
    approvedPage ? "the approved handbook page" : null].filter(Boolean);
  return h("div", {},
    w ? note(w.pushed ? "ok" : "info", `Last sent by ${w.by} on ${w.at}: ${[w.run_page, w.handbook_page].filter(Boolean).join(", ")}. ${w.lint.replace(/\.$/, "")}.` +
      (w.commit ? ` Commit ${w.commit}${w.pushed ? ", pushed to GitHub." : "."}` : "")) : "",
    w && w.git ? note("warn", w.git) : "",
    h("p", { class: "small muted" }, "Writes to the team's LLM wiki: " + what.join("; ") + ". The wiki's own check runs first; if it finds a problem, nothing is written. " +
      (approvedPage ? "" : "Send again after the final review to add the handbook page. ") + "Entity and concept pages are left to the full ingest with the AI assistant."),
    h("label", { class: "f" }, "Wiki folder on this computer (your clone of ael-llm-wiki)", folder),
    h("label", { class: "check" }, push, "Get the latest version first, then commit with git and push to GitHub"),
    err, h("div", { class: "row" }, btn));
}

function results(v, st) {
  const r = v.run, out = [];
  const reviewing = st.stage >= 8;
  if (wikiReady(r) && r.paragraphs.length) out.push(section(r.wiki ? `LLM wiki: sent on ${r.wiki.at}` : "LLM wiki: send this run", !r.wiki && st.who === "done", wikiCard(v, st)));
  if (r.draft) out.push(section("Draft handbook page", reviewing, draftView(r)));
  if (r.check) out.push(section(`Quality check (${r.check.errors} errors, ${r.check.warnings} warnings)`, reviewing, checkView(r.check)));
  if (r.evidence && !(st.stage === 5 && st.who === "human")) out.push(section(`Evidence (${r.evidence.filter((e) => e.approved).length} approved)`, false, r.evidence.map((e) => evidenceCard(e, false).card)));
  if (r.appraisal.human) {
    const hmn = r.appraisal.human, ai = r.appraisal.ai;
    out.push(section(`Appraisal: ${hmn.total}/10, Tier ${hmn.tier}, ${hmn.decision} by ${hmn.by}`, false,
      h("table", { class: "scores" }, h("tr", {}, h("th", {}, "Criterion"), h("th", {}, "AI"), h("th", {}, "Researcher")),
        CFG.rubric.criteria.map((c) => h("tr", {}, h("td", {}, c.name), h("td", {}, ai.scores[c.key].score), h("td", {}, hmn.scores[c.key])))),
      hmn.note ? h("p", {}, "Note: " + hmn.note) : null));
  }
  if (r.paragraphs.length) {
    const tr = (r.translation && r.translation.paragraphs) || {};
    out.push(section(`Source text (${r.paragraphs.length} paragraphs${Object.keys(tr).length ? ", with English translation" : ""})`, false,
      h("p", { class: "small muted" }, r.source.capture || ""),
      r.paragraphs.map((p) => h("div", { class: "para", id: "para-" + p.id }, h("b", {}, p.id), h("div", {}, p.text, tr[p.id] ? h("div", { class: "en" }, tr[p.id]) : null)))));
  }
  out.push(section("Activity log", false, r.log.map((l) => h("div", { class: "log" }, `${l.time.replace("T", " ")} · ${l.who} · ${l.what}`))));
  return out;
}

function draftView(r) {
  const ev = Object.fromEntries(r.evidence.map((e) => [e.id, e]));
  const d = r.draft;
  const body = h("div", { class: "card draft" }, h("h2", {}, d.title), h("p", { class: "muted small" }, "Question: " + r.question,
    d.style_rewrite ? " · wording rewritten for style (the earlier wording is in the history)" : ""));
  for (const s of d.sections) {
    body.append(h("h3", {}, s.heading));
    for (const b of s.blocks || []) {
      const pop = h("div", { class: "pop", hidden: true });
      const cites = (b.evidence || []).map((id) => h("button", { class: "cite", onclick: () => {
        const e = ev[id];
        const show = pop.hidden || pop.dataset.id !== id; pop.hidden = !show; pop.dataset.id = id;
        pop.replaceChildren(...(e ? [h("b", {}, `${id} · paragraph ${e.paragraph}: `), `"${e.quote}"`, e.quote_en ? h("div", { class: "meta" }, "English: " + e.quote_en) : ""] : [`${id} does not exist`]));
      } }, id));
      body.append(h("div", { class: "block" }, h("span", { class: "kind " + b.kind }, b.kind === "example" && !cites.length ? "example (hypothetical)" : b.kind), b.text, cites), pop);
    }
  }
  if (d.decision_questions.length) body.append(h("h3", {}, "Questions for your agency"), h("ul", {}, d.decision_questions.map((q) => h("li", {}, q))));
  const word = h("button", { class: "btn light", onclick: (ev) => downloadWord(ev.currentTarget, r.id) }, "Download as Word");
  return [h("div", { class: "row", style: "justify-content:space-between;margin-top:0" },
    h("span", { class: "small muted" }, "Click an evidence number to see the source passage."), word), body];
}

function checkView(c) {
  const groups = ["Citations & traceability", "Unsupported claims", "Missing information", "Wording & style", "Needs human verification"];
  return [note("info", c.note), ...groups.map((g) => {
    const items = c.items.filter((i) => i.group === g);
    return h("div", { class: "qgroup" }, h("b", {}, g),
      items.length ? items.map((i) => h("div", { class: "qitem" }, h("i", { class: "dot " + i.level }), i.text)) : h("div", { class: "qitem" }, h("i", { class: "dot ok" }), "No problems found"));
  })];
}

// ------------------------------------------------------------------ start
// "Waiting for you": runs that need a decision from the person named in the top bar.
function renderWaiting() {
  const box = $("#waiting");
  if (!box || !CFG) return;
  const name = myName();
  const runs = name ? CFG.runs.filter((x) => x.who === "human" && isMine(x)) : [];
  box.replaceChildren(...(runs.length ? [h("div", { class: "waiting-title" }, `Waiting for you (${runs.length})`),
    ...runs.slice(0, 4).map((x) => h("a", { class: "waitcard", href: "#" + x.id },
      h("b", {}, x.title), h("span", { class: "meta" }, `${x.id} · ${x.step} · ${fmtDate(x.updated)}`)))] : []));
  box.hidden = !runs.length;
}

async function loadRuns() {
  CFG = await api("/api/config");
  const waiting = CFG.runs.filter((x) => x.who === "human" && isMine(x)).length;
  renderWaiting();
  const count = $("#runsCount");
  count.hidden = !waiting; count.textContent = waiting; count.title = `${waiting} waiting for you`;
  renderRunList();
}

// ------------------------------------------------------------------ all research runs (own page)
// Grouped by the person who started each run, newest first, with dates and status. Runs can be deleted (with confirmation).
let listScope = null, listQuery = "";
function showRuns() {
  if (location.hash !== "#runs") location.hash = "#runs";
  if (listScope === null) listScope = myName() ? "mine" : "all";
  const search = h("input", { class: "list-search", type: "search", placeholder: "Search by title, person or RUN-number", value: listQuery });
  search.addEventListener("input", () => { listQuery = search.value; renderRunList(); });
  const scope = h("div", { class: "tabs small-tabs" });
  const drawScope = () => scope.replaceChildren(...[["mine", "Mine"], ["all", "Everyone"]].map(([k, label]) =>
    h("button", { type: "button", class: listScope === k ? "on" : "", onclick: () => { listScope = k; drawScope(); renderRunList(); } }, label)));
  drawScope();
  main.replaceChildren(
    h("div", { class: "page-head" },
      h("div", {}, h("h1", {}, "All research runs"),
        h("p", { class: "muted" }, "Every research run saved on this computer, grouped by who started it."))),
    h("div", { class: "list-tools" }, search, scope),
    h("div", { id: "runList" }),
    h("div", { id: "deletedList", class: "deleted" }));
  renderRunList();
  setNav();
}
function renderRunList() {
  const box = $("#runList");
  if (!box || !CFG) return;
  renderDeleted();
  const q = listQuery.trim().toLowerCase();
  let runs = CFG.runs.filter((x) => !q || [x.title, x.id, x.owner, ...(x.people || [])].join(" ").toLowerCase().includes(q));
  if (listScope === "mine") runs = runs.filter(isMine);
  const groups = new Map();
  for (const x of [...runs].sort((a, b) => (b.updated || "").localeCompare(a.updated || ""))) {
    const key = x.owner || "No name recorded";
    if (!groups.has(key)) groups.set(key, []);
    groups.get(key).push(x);
  }
  const order = [...groups.keys()].sort((a, b) => (sameName(b, myName()) - sameName(a, myName())) || (a === "No name recorded") - (b === "No name recorded") || a.localeCompare(b));
  if (!runs.length) {
    box.replaceChildren(h("div", { class: "card list-empty" }, CFG.runs.length
      ? (listScope === "mine" && !myName() ? "Sign in to see your runs." : listScope === "mine" ? "You have no runs yet. Switch to Everyone to see the whole team." : "No runs match your search.")
      : "No research runs yet. Start one with New research."));
    return;
  }
  box.replaceChildren(...order.map((person) => h("section", { class: "card run-group" },
    h("div", { class: "group-person" }, h("span", { class: "avatar" }, person === "No name recorded" ? "?" : person.trim()[0].toUpperCase()),
      h("b", {}, sameName(person, myName()) ? `${person} (you)` : person), h("span", { class: "muted" }, plural(groups.get(person).length, "run"))),
    groups.get(person).map((x) => h("div", { class: "run-row" },
      h("a", { class: "run-link", href: "#" + x.id },
        h("div", { class: "run-main" }, h("span", { class: "run-title" }, x.title),
          h("span", { class: "meta" }, `${x.id} · started ${fmtDate(x.created)}${x.updated !== x.created ? " · last change " + fmtDate(x.updated) : ""}`)),
        h("span", { class: "st " + x.who }, stateText(x))),
      x.can_delete ? h("button", { class: "icon-btn", type: "button", title: `Delete ${x.id}`, "aria-label": `Delete ${x.id}`, onclick: () => confirmDelete(x) }, trashIcon())
        : h("span", { class: "icon-spacer", title: `Only ${x.owner || "the person who started it"} can delete this run` }))))));
}
function trashIcon() {
  const svg = document.createElementNS("http://www.w3.org/2000/svg", "svg");
  svg.setAttribute("viewBox", "0 0 24 24"); svg.setAttribute("aria-hidden", "true");
  svg.innerHTML = '<path d="M4 7h16M9 7V4.8c0-.4.4-.8.8-.8h4.4c.4 0 .8.4.8.8V7m-8.5 0 .9 12.2c.1.9.8 1.8 1.8 1.8h5.6c1 0 1.7-.9 1.8-1.8L17.5 7M10 11v6M14 11v6" fill="none" stroke="currentColor" stroke-width="1.6" stroke-linecap="round" stroke-linejoin="round"/>';
  return svg;
}
// "Are you sure?" dialog. Cancel is the default button; the action needs a second, deliberate click.
function confirmDialog({ title, body, action, run, danger }) {
  const err = errorBox();
  const close = () => { overlay.remove(); document.removeEventListener("keydown", onKey); };
  const onKey = (e) => { if (e.key === "Escape") close(); };
  const cancel = h("button", { class: "btn light", type: "button", onclick: close }, "Cancel");
  const go = h("button", { class: danger === false ? "btn" : "btn danger", type: "button" }, action);
  go.addEventListener("click", async () => {
    go.disabled = true; cancel.disabled = true; go.textContent = "Working…"; err.hidden = true;
    try { await run(); close(); }
    catch (e) { err.textContent = e.message; err.hidden = false; go.disabled = false; cancel.disabled = false; go.textContent = action; }
  });
  const overlay = h("div", { class: "overlay", onclick: (e) => { if (e.target === overlay) close(); } },
    h("div", { class: "dialog", role: "alertdialog", "aria-modal": "true", "aria-labelledby": "dlgTitle" },
      h("h2", { id: "dlgTitle" }, title), ...body, err, h("div", { class: "row dialog-buttons" }, cancel, go)));
  document.body.append(overlay);
  document.addEventListener("keydown", onKey);
  cancel.focus();
}
function confirmDelete(x) {
  const others = (x.people || []).filter((p) => !sameName(p, myName()));
  confirmDialog({
    title: `Delete ${x.id}?`, action: "Delete run",
    body: [h("p", { class: "dialog-run" }, h("b", {}, x.title), h("span", { class: "muted small" }, `${stateText(x)} · started ${fmtDate(x.created)}`)),
      h("p", { class: "muted" }, "The run moves to Recently deleted at the bottom of this page. You can restore it from there."),
      x.who === "done" ? note("warn", "This page has been approved by a reviewer.") : "",
      others.length ? note("warn", `${others.join(", ")} also worked on this run.`) : ""],
    run: async () => { await api(`/api/run/${x.id}/delete`, {}); toast(`${x.id} moved to Recently deleted`); await loadRuns(); },
  });
}
// Recently deleted: restore, or delete permanently (after a second confirmation).
let showDeleted = false;
function renderDeleted() {
  const box = $("#deletedList");
  if (!box || !CFG) return;
  const list = CFG.deleted || [];
  if (!list.length) { box.replaceChildren(); return; }
  const toggle = h("button", { class: "deleted-toggle", type: "button", "aria-expanded": String(showDeleted),
    onclick: () => { showDeleted = !showDeleted; renderDeleted(); } }, h("span", { class: "chev" + (showDeleted ? " open" : "") }), `Recently deleted (${list.length})`);
  box.replaceChildren(toggle, showDeleted ? h("section", { class: "card run-group deleted-group" },
    h("p", { class: "muted small deleted-note" }, "Runs you deleted are kept here until you delete them permanently. Only you can see and restore them."),
    list.map((x) => h("div", { class: "run-row deleted-row" },
      h("div", { class: "run-main" }, h("span", { class: "run-title" }, x.title),
        h("span", { class: "meta" }, `${x.id} · started by ${x.owner || "no name recorded"} · deleted ${fmtDate(x.deleted_at)}${x.deleted_by ? " by " + x.deleted_by : ""}`)),
      h("button", { class: "btn light small-btn", type: "button", onclick: (e) => restoreRun(e.currentTarget, x) }, "Restore"),
      h("button", { class: "btn red small-btn", type: "button", onclick: () => purgeRun(x) }, "Delete permanently")))) : "");
}
async function restoreRun(btn, x) {
  btn.disabled = true; btn.textContent = "Restoring…";
  try { await api(`/api/deleted/${x.folder}/restore`, {}); toast(`${x.id} restored`); await loadRuns(); }
  catch (e) { toast(e.message); btn.disabled = false; btn.textContent = "Restore"; }
}
function purgeRun(x) {
  confirmDialog({
    title: `Delete ${x.id} permanently?`, action: "Delete permanently",
    body: [h("p", { class: "dialog-run" }, h("b", {}, x.title), h("span", { class: "muted small" }, `started by ${x.owner || "no name recorded"}`)),
      note("error", "This removes the run's files from this computer. It cannot be undone.")],
    run: async () => { await api(`/api/deleted/${x.folder}/purge`, {}); toast(`${x.id} permanently deleted`); await loadRuns(); },
  });
}

// ------------------------------------------------------------------ home page
// What needs you, your latest runs, your numbers, what the team did recently, and how a run works.
const FLOW = [["Ingest", "auto"], ["Privacy check", "auto"], ["Translate", "ai"], ["Appraise", "you"], ["Extract evidence", "you"],
  ["Organise", "auto"], ["Draft", "ai"], ["Check", "auto"], ["Human review", "you"]];
const FLOW_LABEL = { auto: "Automatic", ai: "AI", you: "You decide" };
function greeting() { const hr = new Date().getHours(); return hr < 12 ? "Good morning" : hr < 18 ? "Good afternoon" : "Good evening"; }
async function showHome() {
  if (!["#home", "", "#"].includes(location.hash)) history.replaceState(null, "", "#home");
  setNav();
  await loadRuns();   // always fresh: teammates may have changed things
  const first = USER.first_name || USER.name.split(" ")[0];
  const mine = CFG.runs.filter(isMine).sort((a, b) => (b.updated || "").localeCompare(a.updated || ""));
  const waiting = mine.filter((x) => x.who === "human");
  const inProgress = mine.filter((x) => x.who === "ai" || x.who === "human").length;
  const numbers = h("div", { class: "home-numbers" }, h("p", { class: "muted small" }, "Loading…"));
  const runRow = (x) => h("a", { class: "home-run", href: "#" + x.id },
    h("div", { class: "run-main" }, h("span", { class: "run-title" }, x.title), h("span", { class: "meta" }, `${x.id} · last change ${fmtDate(x.updated)}`)),
    h("span", { class: "st " + x.who }, stateText(x)));
  main.replaceChildren(
    h("section", { class: "home-hero" },
      h("div", {}, h("h1", {}, `${greeting()}, ${first}`),
        h("p", { class: "muted" }, waiting.length ? `${plural(waiting.length, "run")} ${waiting.length === 1 ? "is" : "are"} waiting for your decision.`
          : inProgress ? `Nothing needs you right now. ${plural(inProgress, "run")} of yours ${inProgress === 1 ? "is" : "are"} in progress.`
          : mine.length ? "Nothing needs you right now." : "Start your first research run to get going."))),
    waiting.length ? h("section", { class: "home-block" }, h("h2", { class: "home-h" }, "Waiting for you"),
      h("div", { class: "waiting" }, waiting.slice(0, 6).map((x) => h("a", { class: "waitcard", href: "#" + x.id },
        h("b", {}, x.title), h("span", { class: "meta" }, `${x.id} · ${x.step} · ${fmtDate(x.updated)}`))))) : "",
    h("div", { class: "home-grid" },
      h("section", { class: "card home-card" },
        h("div", { class: "home-card-head" }, h("h2", {}, "Your recent runs"), mine.length ? h("a", { href: "#runs" }, "See all") : ""),
        mine.length ? mine.slice(0, 4).map(runRow) : h("p", { class: "muted" }, "You have not started a run yet. ",
          h("a", { href: "#new" }, "Start one"), ".")),
      h("section", { class: "card home-card" },
        h("div", { class: "home-card-head" }, h("h2", {}, "Your numbers"), h("a", { href: "#stats" }, "Statistics")), numbers)),
    h("section", { class: "card home-card" },
      h("div", { class: "home-card-head" }, h("h2", {}, "Recent team activity"), h("span", { class: "muted small" }, "Decisions by people, newest first")),
      CFG.activity.length ? h("div", { class: "activity" }, CFG.activity.map((a) => h("a", { class: "act-row", href: "#" + a.id },
        h("span", { class: "avatar" }, initials(a.who)),
        h("div", { class: "run-main" },
          h("span", { class: "act-what" }, h("b", {}, sameName(a.who, myName()) ? "You" : a.who), " · ", a.what.length > 90 ? a.what.slice(0, 88) + "…" : a.what),
          h("span", { class: "meta" }, `${a.id} · ${a.title} · ${fmtDate(a.time)}`)))))
        : h("p", { class: "muted" }, "No decisions yet. They will show up here as the team works.")),
    h("section", { class: "home-block" },
      h("h2", { class: "home-h" }, "How a research run works"),
      h("div", { class: "flow" }, FLOW.map(([name, who], i) => h("div", { class: "flow-step " + who },
        h("span", { class: "flow-n" }, i + 1), h("span", { class: "flow-name" }, name), h("span", { class: "flow-who" }, FLOW_LABEL[who])))),
      h("p", { class: "muted small" }, "The AI only suggests. Every decision that shapes the handbook is made, and recorded, by a person. Nothing is published automatically.")));
  try {
    const st = await api("/api/stats");
    numbers.replaceChildren(
      h("div", { class: "mini" }, h("b", {}, st.runs.started), h("span", {}, "runs started")),
      h("div", { class: "mini" }, h("b", {}, st.decisions.total), h("span", {}, "decisions recorded")),
      h("div", { class: "mini" }, h("b", {}, st.decisions.pages_approved), h("span", {}, "pages approved")),
      h("div", { class: "mini" }, h("b", {}, st.decisions.appraisals), h("span", {}, "sources appraised")));
  } catch (e) { numbers.replaceChildren(h("p", { class: "muted small" }, e.message)); }
}

// ------------------------------------------------------------------ personal statistics
async function showStats() {
  main.replaceChildren(h("h1", {}, "Your statistics"), h("p", { class: "muted" }, "Loading…"));
  let st;
  try { st = await api("/api/stats"); } catch (e) { main.replaceChildren(note("error", e.message)); return; }
  const R = st.runs, D = st.decisions, A = st.appraisal;
  const tile = (value, label, sub) => h("div", { class: "stat" }, h("div", { class: "stat-value" }, value), h("div", { class: "stat-label" }, label), sub ? h("div", { class: "stat-sub" }, sub) : "");
  const pct = (a, b) => (b ? Math.round((100 * a) / b) + "%" : "–");
  // one labelled row per item, with a thin bar showing its share of the group total
  const rows = (items) => { const max = Math.max(1, ...items.map((x) => x[1]));
    return h("div", { class: "stat-rows" }, items.map(([label, n, cls]) => h("div", { class: "stat-row" },
      h("span", { class: "stat-row-label" }, label), h("span", { class: "stat-bar" }, h("span", { class: "stat-fill " + (cls || ""), style: `width:${(100 * n) / max}%` })),
      h("b", { class: "stat-row-n" }, n)))); };
  main.replaceChildren(
    h("h1", {}, "Your statistics"),
    h("p", { class: "muted" }, `${st.name} · login ${st.login}` + (st.member_since ? ` · member since ${fmtDate(st.member_since)}` : "") +
      (st.last_activity ? ` · last activity ${fmtDate(st.last_activity)}` : "")),
    h("div", { class: "stat-tiles" },
      tile(R.started, "Runs you started", R.contributed ? `+ ${plural(R.contributed, "run")} of others you worked on` : "Deleted runs not counted"),
      tile(R.waiting_for_you, "Waiting for you", R.waiting_for_you ? h("a", { href: "#runs" }, "Open your runs") : "Nothing needs you now"),
      tile(D.total, "Decisions recorded", "Every action logged under your name"),
      tile(D.pages_approved, "Pages you approved", D.changes_requested ? `${plural(D.changes_requested, "draft")} sent back for changes` : "Final human approval of a page")),
    h("div", { class: "stat-grid" },
      h("section", { class: "card" }, h("h2", {}, "Your runs"),
        R.started ? rows([["Finished", R.done, "done"], ["Waiting for a person", R.human, "human"], ["At an AI step", R.ai, "ai"], ["Stopped", R.stopped, "stopped"]])
          : h("p", { class: "muted" }, "You have not started a run yet.")),
      h("section", { class: "card" }, h("h2", {}, "Your decisions"),
        rows([["Privacy decisions", D.privacy], ["Sources appraised", D.appraisals], ["Evidence reviews", D.evidence_reviews],
          ["Page reviews", D.pages_approved + D.changes_requested], ["Steps changed afterwards", D.steps_changed]])),
      h("section", { class: "card" }, h("h2", {}, "Sources you appraised"),
        D.appraisals ? [
          rows([["Tier A", A.tiers.A], ["Tier B", A.tiers.B], ["Tier C", A.tiers.C]]),
          h("p", { class: "muted small stat-foot" }, `${D.accepted} accepted, ${D.rejected} rejected · average score ${A.average}/10`)]
          : h("p", { class: "muted" }, "No appraisals yet.")),
      h("section", { class: "card" }, h("h2", {}, "You and the AI"),
        h("div", { class: "stat-pair" },
          tile(pct(A.ai_scores_changed, D.appraisals), "Appraisals where you changed the AI's score", `${A.ai_scores_changed} of ${D.appraisals}`),
          tile(pct(D.evidence_approved, D.evidence_seen), "AI-proposed evidence you approved", `${D.evidence_approved} of ${D.evidence_seen} items`)),
        h("p", { class: "muted small stat-foot" }, "The AI only suggests. These numbers show how often your judgement differed from its suggestions."))));
}

// ------------------------------------------------------------------ accounts: sign in, create an account, account menu
function showSignIn(mode) {
  if (!mode) mode = showSignIn.mode || "signin";
  showSignIn.mode = mode;
  document.body.classList.add("signed-out");
  const f = {};
  const input = (key, label, attrs) => { f[key] = h("input", attrs); return h("label", { class: "f" }, label, f[key]); };
  const err = errorBox();
  const signup = mode === "signup";
  const btn = h("button", { class: "btn big wide", type: "submit" }, signup ? "Create account" : "Sign in");
  const form = h("form", { class: "card auth", novalidate: true },
    h("h1", {}, signup ? "Create your account" : "Sign in"),
    h("p", { class: "muted" }, signup ? "Your first and last name are shown on every decision you make and in the activity log."
      : "Sign in to continue. Every decision is recorded under your name."),
    signup ? h("div", { class: "grid two" },
      input("first", "First name", { autocomplete: "given-name" }),
      input("last", "Last name", { autocomplete: "family-name" })) : "",
    input("login", "Login", { autocomplete: "username", autocapitalize: "none", spellcheck: "false", placeholder: signup ? "e.g. anna.jansen" : "" }),
    input("pw", "Password", { type: "password", autocomplete: signup ? "new-password" : "current-password", placeholder: signup ? "At least 8 characters" : "" }),
    signup ? input("pw2", "Repeat password", { type: "password", autocomplete: "new-password" }) : "",
    err, btn,
    h("p", { class: "auth-switch muted small" }, signup ? "Already have an account? " : "New here? ",
      h("button", { class: "linkbtn", type: "button", onclick: () => showSignIn(signup ? "signin" : "signup") }, signup ? "Sign in" : "Create an account")));
  form.addEventListener("submit", async (e) => {
    e.preventDefault(); err.hidden = true;
    if (signup && f.pw.value !== f.pw2.value) { err.textContent = "The two passwords are not the same."; err.hidden = false; return; }
    btn.disabled = true;
    try {
      const res = signup
        ? await api("/api/signup", { first_name: f.first.value, last_name: f.last.value, login: f.login.value, password: f.pw.value })
        : await api("/api/signin", { login: f.login.value, password: f.pw.value });
      USER = res.user; renderAccount(); listScope = null;
      toast(signup ? `Welcome, ${USER.name}` : `Signed in as ${USER.name}`);
      await Promise.all([loadRuns(), loadAI()]); if (location.hash === "#new") location.hash = "#home"; route();
    } catch (ex) { err.textContent = ex.message; err.hidden = false; f.pw.value = ""; if (f.pw2) f.pw2.value = ""; }
    finally { btn.disabled = false; }
  });
  main.replaceChildren(form);
  (signup ? f.first : f.login).focus();
}
function initials(name) { return (name || "?").split(" ").filter(Boolean).map((p) => p[0]).slice(0, 2).join("").toUpperCase(); }
function renderAccount() {
  const box = $("#account");
  document.body.classList.toggle("signed-out", !USER);
  if (!USER) { box.replaceChildren(); return; }
  const menu = h("div", { class: "acct-menu", hidden: true },
    h("div", { class: "acct-head" }, h("b", {}, USER.name), h("span", { class: "muted small" }, "Login: " + USER.login)),
    h("button", { type: "button", onclick: () => { menu.hidden = true; location.hash = "#stats"; } }, "Statistics"),
    h("button", { type: "button", onclick: () => { menu.hidden = true; aiSettings(); } }, "AI settings"),
    h("button", { type: "button", onclick: () => { menu.hidden = true; changePassword(); } }, "Change password"),
    h("button", { type: "button", onclick: signOut }, "Sign out"));
  const chip = h("button", { class: "acct-chip", type: "button", "aria-haspopup": "true" },
    h("span", { class: "avatar" }, initials(USER.name)), h("span", { class: "acct-name" }, USER.name));
  chip.addEventListener("click", (e) => { e.stopPropagation(); menu.hidden = !menu.hidden; });
  menu.addEventListener("click", (e) => e.stopPropagation());
  box.replaceChildren(chip, menu);
}
document.addEventListener("click", () => { const m = $(".acct-menu"); if (m) m.hidden = true; });
async function signOut() {
  try { await api("/api/signout", {}); } catch (e) { /* signed out anyway */ }
  USER = null; CFG = null; renderAccount(); showSignIn("signin"); toast("Signed out");
}
function changePassword() {
  const old = h("input", { type: "password", autocomplete: "current-password" });
  const nw = h("input", { type: "password", autocomplete: "new-password", placeholder: "At least 8 characters" });
  const nw2 = h("input", { type: "password", autocomplete: "new-password" });
  confirmDialog({
    title: "Change password", action: "Save new password", danger: false,
    body: [h("label", { class: "f" }, "Current password", old), h("label", { class: "f" }, "New password", nw), h("label", { class: "f" }, "Repeat new password", nw2)],
    run: async () => {
      if (nw.value !== nw2.value) throw new Error("The two new passwords are not the same.");
      await api("/api/password", { old: old.value, new: nw.value }); toast("Password changed");
    },
  });
  setTimeout(() => old.focus(), 0);
}

// AI settings: manual or automatic mode, the Claude model and this account's API key (stored on this computer only)
async function aiSettings(after) {
  await loadAI();
  const mode = h("div", { class: "seg wide-seg" });
  let chosen = AI.mode;
  const drawMode = () => mode.replaceChildren(...[["manual", "Manual paste"], ["api", "Automatic (Claude API)"]].map(([k, label]) =>
    h("button", { type: "button", class: chosen === k ? "on" : "", onclick: () => { chosen = k; drawMode(); } }, label)));
  drawMode();
  const model = h("select", {}, Object.entries(AI.models || {}).map(([k, label]) => h("option", { value: k, selected: k === AI.model }, label)));
  const key = h("input", { type: "password", autocomplete: "off", spellcheck: "false", placeholder: AI.has_key ? `Saved (${AI.key_hint}). Type a new key to replace it` : "sk-ant-..." });
  const clear = h("label", { class: "check" }, h("input", { type: "checkbox" }), "Remove my saved key");
  confirmDialog({
    title: "AI settings", action: "Save", danger: false,
    body: [
      h("p", { class: "muted small" }, "Manual: you copy each prompt into the team's Claude project and paste the answer back (the default). Automatic: the agent sends the prompt to Claude for you. Either way the agent checks every answer and every decision stays yours."),
      h("div", { class: "f" }, "Mode", mode),
      h("label", { class: "f" }, "Claude model (automatic mode)", model),
      h("label", { class: "f" }, "Your Claude API key", key),
      AI.has_key && AI.key_hint !== "from ANTHROPIC_API_KEY" ? clear : "",
      h("p", { class: "muted small" }, "The key is saved for your account in local_settings/ on this computer only. It is never shown again, never written to a research run or the activity log, and that folder is excluded from git. Create a key at console.anthropic.com. Usage is billed to that key's account."),
      AI.sdk_installed ? "" : note("warn", "Automatic mode also needs the Anthropic Python package: run  py -m pip install anthropic  once, then restart start.bat.")],
    run: async () => {
      AI = await api("/api/settings", { mode: chosen, model: model.value, api_key: key.value || null, clear_key: clear.querySelector("input").checked });
      toast(AI.mode === "api" ? "Saved: automatic mode" : "Saved: manual mode");
      if (after) after();
    },
  });
  setTimeout(() => key.focus(), 0);
}

// top bar: highlight "All research runs" when that page is open
function setNav() {
  $("#runsBtn").classList.toggle("on", location.hash === "#runs");
  $("#homeBtn").classList.toggle("on", ["", "#", "#home"].includes(location.hash));
}
$("#runsBtn").addEventListener("click", () => { location.hash = "#runs"; });
// Download the draft as a Word file; show a clear message if the server cannot make it.
async function downloadWord(button, runId) {
  button.disabled = true;
  try {
    const res = await fetch(`/api/run/${runId}/word`);
    if (!res.ok || !(res.headers.get("Content-Type") || "").includes("wordprocessingml")) {
      let msg = "The Word file could not be made. Close the black window and start start.bat again, then retry.";
      try { const d = await res.json(); if (d.error) msg = d.error; } catch (e) { /* not JSON */ }
      throw new Error(msg);
    }
    const name = ((res.headers.get("Content-Disposition") || "").match(/filename="([^"]+)"/) || [])[1] || `${runId}.docx`;
    const url = URL.createObjectURL(await res.blob());
    const a = h("a", { href: url, download: name });
    document.body.append(a); a.click(); a.remove();
    setTimeout(() => URL.revokeObjectURL(url), 5000);
    toast("Word file downloaded");
  } catch (e) { toast(e.message); } finally { button.disabled = false; }
}
async function route() {
  if (!USER) return showSignIn();
  const id = location.hash.slice(1);
  setNav();
  if (id === "runs") { showRuns(); loadRuns(); return; }
  if (id === "stats") return showStats();
  if (id === "new") return showNew();
  if (/^RUN-\d+$/.test(id)) {
    try { showRun(await api("/api/run/" + id)); return; } catch (e) { toast(e.message); }
  }
  showHome();
}
$("#homeBtn").addEventListener("click", () => { if (location.hash === "#home") showHome(); else location.hash = "#home"; });
$("#new").addEventListener("click", () => { location.hash = "#new"; loadRuns().then(showNew); });
window.addEventListener("hashchange", route);
// start: find out who is signed in; show the sign-in screen if nobody is
api("/api/me").then(async (res) => {
  USER = res.user; renderAccount();
  if (!USER) return showSignIn(res.has_accounts ? "signin" : "signup");
  await Promise.all([loadRuns(), loadAI()]); route();
}).catch((e) => main.replaceChildren(note("error", "Could not load the agent: " + e.message)));
