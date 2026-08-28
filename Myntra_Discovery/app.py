"""Discovery Engine — Streamlit findings dashboard.

Reads ONLY data/snapshot.json. Live scraping writes a temp snapshot and
replaces the file on success; the currently displayed snapshot is never
cleared on a rerun or a failed scrape.
"""

from __future__ import annotations

import html
import json
import os

import streamlit as st

from paths import SNAPSHOT_PATH, SNAPSHOT_TMP

st.set_page_config(
    page_title="Discovery Engine- Myntra",
    layout="wide",
    initial_sidebar_state="collapsed",
)

CSS = """
<style>
@import url('https://fonts.googleapis.com/css2?family=Fraunces:opsz,wght@9..144,400;9..144,600&family=Instrument+Sans:wght@400;500;600&family=Spline+Sans+Mono:wght@400;500&display=swap');
:root{
  --ink:#3A1D3D;--ink-soft:#6B5468;--canvas:#F7F4EF;--card:#FFFFFF;--line:#E7DFD4;
  --marigold:#E8A317;--marigold-deep:#B67A05;--teal:#0E7C6B;--clay:#B45309;--slate:#5B5568;
  --shadow:0 1px 2px rgba(58,29,61,.06),0 8px 24px rgba(58,29,61,.06);
}
.stApp{background:var(--canvas);color:var(--ink);font-family:'Instrument Sans',system-ui,sans-serif}
.block-container{padding-top:1rem;padding-bottom:2rem;max-width:100%}
header[data-testid="stHeader"]{background:transparent}
#MainMenu, footer{visibility:hidden}
div[data-testid="stToolbar"]{display:none}

.brand b{font-family:'Fraunces',serif;font-weight:600;font-size:20px;color:var(--ink)}
.meta{font-family:'Spline Sans Mono',monospace;font-size:12px;color:var(--ink-soft)}
.snap-label{font-family:'Spline Sans Mono',monospace;font-size:11px;color:var(--ink-soft);margin-top:4px}

.stTabs [data-baseweb="tab-list"]{gap:8px;border-bottom:2px solid #E7DFD4;background:#fff}
.stTabs [data-baseweb="tab"]{height:52px;padding:0 24px;font-size:17px;font-weight:600;background:#fff;border-radius:10px 10px 0 0;color:#6B5468}
.stTabs [aria-selected="true"]{background:#E8A317;color:#3A1D3D;border-bottom:3px solid #0E7C6B}

.hero{padding:8px 0 8px}
.eyebrow{font-family:'Spline Sans Mono',monospace;font-size:12px;letter-spacing:.12em;text-transform:uppercase;color:var(--marigold-deep);margin:0 0 12px}
h1.de{font-family:'Fraunces',serif;font-weight:600;font-size:clamp(28px,3.4vw,44px);line-height:1.08;letter-spacing:-.02em;margin:0 0 14px;color:var(--ink)}
.lede{font-size:16px;color:var(--ink-soft);margin:0 0 22px;width:min(90ch,100%)}
h2.de{font-family:'Fraunces',serif;font-weight:600;font-size:26px;margin:0 0 6px;color:var(--ink)}
.sub{color:var(--ink-soft);font-size:15px;margin:0 0 22px;width:min(96ch,100%)}

.funnel{display:flex;flex-direction:column;gap:12px;width:100%}
.frow{display:grid;grid-template-columns:minmax(240px,1.6fr) minmax(200px,1fr);align-items:center;gap:20px;margin-bottom:10px}
.fbar{height:48px;border-radius:10px;display:flex;align-items:center;padding:0 16px;color:#fff;font-weight:600;font-size:14px;white-space:nowrap;box-shadow:var(--shadow);overflow:hidden;min-width:8%}
.fnote{font-size:14px;color:var(--ink-soft)}
.fnote b{color:var(--ink);font-family:'Spline Sans Mono',monospace;font-weight:500}
.sources{display:grid;grid-template-columns:repeat(4,1fr);gap:14px;margin-top:18px}
.src{background:#fff;border:1px solid var(--line);border-radius:12px;padding:16px 18px;box-shadow:var(--shadow)}
.src .k{font-size:12px;color:var(--ink-soft);font-family:'Spline Sans Mono',monospace}
.src .v{font-family:'Fraunces',serif;font-size:22px;font-weight:600;margin-top:2px}
.src .r{font-size:11px;color:var(--marigold-deep);font-family:'Spline Sans Mono',monospace;margin-top:2px}
.note{font-size:13px;color:var(--ink-soft);background:#faf5ec;border:1px solid #f0e2c4;border-radius:10px;padding:14px 16px;margin-top:20px}

.themes{display:flex;flex-direction:column;gap:14px;width:100%}
.theme{display:grid;grid-template-columns:220px 1fr 56px;align-items:center;gap:16px}
.theme .track{background:#efe9e0;border-radius:8px;height:26px;overflow:hidden}
.theme .fill{height:100%;border-radius:8px}
.theme .cnt{font-family:'Spline Sans Mono',monospace;font-size:14px;text-align:right;color:var(--ink-soft)}

.qrows{display:flex;flex-direction:column;gap:10px;width:100%}
.qrow{display:grid;grid-template-columns:minmax(220px,.92fr) minmax(240px,1.35fr);gap:18px 28px;align-items:start;background:#fff;border:1px solid var(--line);border-radius:12px;padding:16px 20px;box-shadow:var(--shadow);margin-bottom:10px}
.qask{margin:0;font-weight:600;font-size:14.5px}
.qans{margin:0;display:flex;align-items:flex-start;gap:12px}
.qans p{margin:0;font-size:14.5px}
.conf{display:flex;flex-direction:column;align-items:center;gap:4px;flex-shrink:0;padding-top:3px;min-width:52px}
.conf .dot{width:11px;height:11px;border-radius:50%;display:block;box-shadow:0 0 0 2px #fff,0 0 0 3px currentColor}
.conf.high{color:var(--teal)} .conf.high .dot{background:var(--teal)}
.conf.med{color:var(--clay)} .conf.med .dot{background:var(--clay)}
.conf.low{color:var(--slate)} .conf.low .dot{background:var(--slate)}
.conf span{font-family:'Spline Sans Mono',monospace;font-size:10px;font-weight:500;color:currentColor}

.callout{background:#fff;border:1px solid var(--line);border-left:4px solid var(--marigold);border-radius:12px;padding:28px 32px;box-shadow:var(--shadow)}
.callout h3{margin:0 0 10px;font-family:'Fraunces',serif;font-size:19px;font-weight:600}
.compare{display:flex;gap:14px;flex-wrap:wrap;margin:16px 0}
.cbox{flex:1;min-width:180px;border:1px solid var(--line);border-radius:10px;padding:14px}
.cbox .big{font-family:'Fraunces',serif;font-size:34px;font-weight:600;line-height:1}
.cbox .cap{font-size:12.5px;color:var(--ink-soft);margin-top:6px}
.cbox.was .big{color:var(--slate)}
.cbox.now .big{color:var(--teal)}

.quotes{display:grid;grid-template-columns:repeat(4,1fr);gap:16px}
.q{background:#fff;border:1px solid var(--line);border-radius:12px;padding:16px;box-shadow:var(--shadow)}
.q p{margin:0 0 10px;font-size:14.5px}
.q .tag{display:inline-flex;align-items:center;gap:7px;font-family:'Spline Sans Mono',monospace;font-size:11px;color:var(--ink-soft)}
.q .swatch{width:9px;height:9px;border-radius:2px}

.steps{display:grid;grid-template-columns:repeat(4,1fr);gap:14px}
.step{background:#fff;border:1px solid var(--line);border-radius:12px;padding:16px;box-shadow:var(--shadow)}
.step .n{font-family:'Spline Sans Mono',monospace;font-size:12px;color:var(--marigold-deep)}
.step h4{margin:6px 0;font-family:'Fraunces',serif;font-size:16px}
.step p{margin:0;font-size:13px;color:var(--ink-soft)}

.opp-chart{width:100%;height:auto;display:block;background:#fff;border:1px solid var(--line);border-radius:12px;box-shadow:var(--shadow)}
.opp-legend{display:flex;flex-wrap:wrap;gap:10px 22px;margin:16px 0 0;padding:0;list-style:none}
.opp-legend li{display:flex;align-items:center;gap:8px;font-size:13.5px}
.opp-legend .mark{width:14px;height:14px;flex-shrink:0}
.opp-legend .mark.pursue{background:var(--teal);border-radius:50%}
.opp-legend .mark.secondary{background:var(--clay);clip-path:polygon(50% 0,100% 50%,50% 100%,0 50%)}
.opp-legend .mark.drop{background:var(--slate);border-radius:2px}
.opp-legend .key{font-family:'Spline Sans Mono',monospace;font-size:11px;color:var(--ink-soft)}
.opp-cap{font-size:13px;color:var(--ink-soft);margin:14px 0 0}

@media(max-width:900px){
  .sources,.quotes,.steps{grid-template-columns:1fr 1fr}
  .qrow,.frow,.theme{grid-template-columns:1fr}
}
@media(max-width:640px){.quotes,.steps,.sources{grid-template-columns:1fr}}
</style>
"""


@st.cache_data
def load_snapshot():
    with SNAPSHOT_PATH.open(encoding="utf-8") as f:
        return json.load(f)


def _fmt(n):
    return f"{int(n):,}"


def _pct(n, d):
    return f"{(100 * n / d):.1f}" if d else "0.0"


def _esc(s):
    return html.escape(str(s or ""), quote=True)


def _conf_class(level: str) -> str:
    return {"high": "high", "medium": "med", "low": "low"}.get((level or "").lower(), "med")


def render_corpus(snap):
    total = snap["corpus_total"]
    rel = snap["relevant_count"]
    kw = snap.get("keyword", 0)
    rel_pct = _pct(rel, total)
    kw_w = max(10, round(100 * kw / total)) if total else 10
    rel_w = max(16, round(100 * rel / total * 6)) if total else 16
    sources = "".join(
        f'<div class="src"><div class="k">{_esc(s["key"])}</div>'
        f'<div class="v">{s["relevant"]}</div>'
        f'<div class="r">of {_fmt(s["total"])}'
        f'{(" · " + _pct(s["relevant"], s["total"]) + "%") if s.get("key") == "reddit" else ""}'
        f"</div></div>"
        for s in snap.get("sources") or []
    )
    reddit = next((s for s in snap.get("sources") or [] if s.get("key") == "reddit"), {"relevant": 0, "total": 1})
    app = next((s for s in snap.get("sources") or [] if s.get("key") == "app store"), {"relevant": 0, "total": 1})
    r_pct, a_pct = _pct(reddit["relevant"], reddit["total"]), _pct(app["relevant"], app["total"])
    dens = round(float(r_pct) / float(a_pct)) if float(a_pct) > 0 else "—"
    st.markdown(
        f"""
<div class="hero">
  <p class="eyebrow">AI-powered discovery · Part 1</p>
  <h1 class="de">What public conversation actually says about unbought wishlists.</h1>
  <p class="lede">A two-stage pipeline collected public reviews and threads about Myntra (Play Store and App Store v1+v2 merged, plus YouTube and Reddit), then classified each one for genuine wishlist-to-purchase behaviour — not sentiment. The headline finding is as much about what <em>isn't</em> there as what is: explicit save-then-abandon narrative is rare in short-form review text.</p>
</div>
<h2 class="de">From {_fmt(total)} merged items to {_fmt(rel)} with real signal</h2>
<p class="sub">Play Store and App Store v1+v2 were unioned and deduped, then combined with YouTube and Reddit. Most review text is about delivery, refunds, and app bugs. A strict LLM relevance pass — not keyword matching — found the small slice that actually describes saving, deferring, or abandoning a purchase.</p>
<div class="funnel">
  <div class="frow"><div class="fbar" style="background:#3A1D3D;width:{100}%">{_fmt(total)} items after v1+v2 merge</div><span class="fnote">Play Store, App Store, YouTube, Reddit · short/empty dropped</span></div>
  <div class="frow"><div class="fbar" style="background:#5B5568;width:{kw_w}%">{_fmt(kw)} keyword-adjacent</div><span class="fnote">surface tokens only — keywords miss paraphrased intent</span></div>
  <div class="frow"><div class="fbar" style="background:#0E7C6B;width:{rel_w}%">{_fmt(rel)} genuinely relevant</div><span class="fnote"><b>{rel_pct}%</b> of the corpus — LLM pass, the honest denominator</span></div>
</div>
<div class="sources">{sources}</div>
<div class="note"><b>Reddit was ~{dens}× denser in signal than App Store reviews</b> ({r_pct}% vs {a_pct}%) — long-form discussion carries behavioural narrative that star-rating reviews don't. It was also the hardest to collect (API now gated), so it's the smallest source despite being the richest per item.</div>
""",
        unsafe_allow_html=True,
    )


def render_themes(snap):
    themes = snap.get("themes") or []
    max_t = max((t["count"] for t in themes), default=1) or 1
    rows = "".join(
        f'<div class="theme"><span class="lbl">{_esc(t["name"])}</span>'
        f'<div class="track"><div class="fill" style="background:{_esc(t["color"])};width:{t["count"]/max_t*100:.0f}%"></div></div>'
        f'<span class="cnt">{t["count"]}</span></div>'
        for t in themes
    )
    st.markdown(
        f"""
<h2 class="de">What the relevant items are about</h2>
<p class="sub">Free-form tags from the classifier, grouped into canonical themes. Price and cross-platform comparison dominate — but see the honesty check before reading too much into raw counts.</p>
<div class="themes">{rows}</div>
""",
        unsafe_allow_html=True,
    )


def render_questions(snap):
    rows = []
    for q in snap.get("questions") or []:
        level = (q.get("confidence") or "medium").lower()
        cls = _conf_class(level)
        rows.append(
            f'<div class="qrow"><p class="qask">{_esc(q.get("question"))}</p>'
            f'<div class="qans"><span class="conf {cls}" aria-label="Confidence: {_esc(level)}">'
            f'<i class="dot"></i><span>{_esc(level)}</span></span>'
            f'<p>{_esc(q.get("answer"))}</p></div></div>'
        )
    st.markdown(
        f"""
<h2 class="de">The brief's questions, answered by the engine alone</h2>
<p class="sub">Each answer is constrained to what public reviews and threads actually surfaced. Where the corpus is silent, the row says so — it is not filled in from interviews or product intuition. Confidence is how strongly the relevant slice supports the line, not how important the question is.</p>
<div class="qrows">{''.join(rows)}</div>
""",
        unsafe_allow_html=True,
    )


def _opp_mark(cx, cy, verdict):
    if verdict == "pursue":
        return f'<circle class="hit" cx="{cx}" cy="{cy}" r="16" fill="transparent"/><circle cx="{cx}" cy="{cy}" r="9" fill="#0E7C6B" stroke="#fff" stroke-width="2"/>'
    if verdict == "secondary":
        return (
            f'<circle class="hit" cx="{cx}" cy="{cy}" r="16" fill="transparent"/>'
            f'<polygon points="{cx},{cy-11} {cx+11},{cy} {cx},{cy+11} {cx-11},{cy}" fill="#B45309" stroke="#fff" stroke-width="2"/>'
        )
    return (
        f'<circle class="hit" cx="{cx}" cy="{cy}" r="16" fill="transparent"/>'
        f'<rect x="{cx-9}" y="{cy-9}" width="18" height="18" rx="2" fill="#5B5568" stroke="#fff" stroke-width="2"/>'
    )


def render_opportunities(snap):
    marks = []
    for o in snap.get("opportunities") or []:
        ev, imp = float(o.get("evidence", 0.5)), float(o.get("impact", 0.5))
        cx = 96 + ev * 684
        cy = 468 - imp * 432
        name = _esc(o.get("name"))
        verdict = o.get("verdict", "drop")
        marks.append(
            f'<g class="pt" tabindex="0" focusable="true" role="img" '
            f'aria-label="{name}. Evidence {ev:.2f}, impact {imp:.2f}. {verdict}.">'
            f'{_opp_mark(cx, cy, verdict)}'
            f'<text class="pt-lbl" x="{cx}" y="{cy-16}" text-anchor="middle" '
            f'font-family="Instrument Sans,sans-serif" font-size="12.5" font-weight="500" fill="#3A1D3D">{name}</text></g>'
        )
    st.markdown(
        f"""
<h2 class="de">Where the engine would spend the next cycle</h2>
<p class="sub">A 2×2 of evidence strength (what the corpus actually supports) against estimated impact on wishlist→purchase. Verdict colour and shape travel together so the map stays readable without colour alone.</p>
<figure class="opp-fig">
<svg class="opp-chart" viewBox="0 0 1000 560" role="group" aria-label="Opportunity map">
  <rect x="0" y="0" width="1000" height="560" fill="#FFFFFF" rx="12"/>
  <rect x="96" y="36" width="342" height="216" fill="#f4faf8"/>
  <rect x="438" y="36" width="342" height="216" fill="#eef7f4"/>
  <rect x="96" y="252" width="342" height="216" fill="#f7f4ef"/>
  <rect x="438" y="252" width="342" height="216" fill="#faf7f2"/>
  <line x1="438" y1="36" x2="438" y2="468" stroke="#E7DFD4" stroke-width="1.5" stroke-dasharray="5 5"/>
  <line x1="96" y1="252" x2="780" y2="252" stroke="#E7DFD4" stroke-width="1.5" stroke-dasharray="5 5"/>
  <rect x="96" y="36" width="684" height="432" fill="none" stroke="#E7DFD4" stroke-width="1.5" rx="4"/>
  <line x1="96" y1="468" x2="780" y2="468" stroke="#3A1D3D" stroke-width="1.5"/>
  <line x1="96" y1="468" x2="96" y2="36" stroke="#3A1D3D" stroke-width="1.5"/>
  <text x="96" y="490" text-anchor="start" font-family="Spline Sans Mono,monospace" font-size="11" fill="#6B5468">low</text>
  <text x="780" y="490" text-anchor="end" font-family="Spline Sans Mono,monospace" font-size="11" fill="#6B5468">high</text>
  <text x="438" y="512" text-anchor="middle" font-family="Spline Sans Mono,monospace" font-size="12" fill="#6B5468">Evidence strength (engine) →</text>
  <text x="84" y="468" text-anchor="end" font-family="Spline Sans Mono,monospace" font-size="11" fill="#6B5468">low</text>
  <text x="84" y="48" text-anchor="end" font-family="Spline Sans Mono,monospace" font-size="11" fill="#6B5468">high</text>
  <text text-anchor="middle" transform="rotate(-90 28 252)" font-family="Spline Sans Mono,monospace" font-size="12" fill="#6B5468">Estimated impact on wishlist→purchase</text>
  {''.join(marks)}
</svg>
<ul class="opp-legend" aria-label="Verdict colours and shapes">
  <li><span class="mark pursue"></span> Pursue <span class="key">teal · circle</span></li>
  <li><span class="mark secondary"></span> Secondary <span class="key">clay · diamond</span></li>
  <li><span class="mark drop"></span> Drop <span class="key">slate · square</span></li>
</ul>
<p class="opp-cap">Impact scores are reasoned directional estimates, not measured — hypotheses, consistent with the 29→1 honesty check.</p>
</figure>
""",
        unsafe_allow_html=True,
    )


def render_honesty(snap):
    h = snap.get("honesty") or {}
    tagged, generic, deferral = h.get("tagged", 0), h.get("generic", 0), h.get("deferral", 0)
    st.markdown(
        f"""
<h2 class="de">The honesty check that changed the conclusion</h2>
<p class="sub">The first classification tagged any mention of price as “price/sale timing” — {tagged} items. A stricter re-read, separating genuine purchase-deferral from generic price sentiment, collapsed that almost entirely.</p>
<div class="callout">
  <h3>“Price/sale timing”: {tagged} → {deferral} under strict definition</h3>
  <div class="compare">
    <div class="cbox was"><div class="big">{generic}</div><div class="cap">generic price sentiment — “costly”, “love the discounts”. Not deferral.</div></div>
    <div class="cbox now"><div class="big">{deferral}</div><div class="cap">genuine price-driven purchase deferral — someone actually waiting/abandoning on price.</div></div>
  </div>
  <p>The same discipline still shrinks “wishlist/save” (heart-emoji false positives) and “forgot/stale” (mostly stock-availability) once you read the rows. <b>Conclusion:</b> short-form store reviews under-evidence save-then-abandon behaviour; the denser signal remains in long-form Reddit.</p>
</div>
""",
        unsafe_allow_html=True,
    )


def render_verbatims(snap):
    cards = "".join(
        f'<div class="q"><p>“{_esc(v["text"])}”</p>'
        f'<span class="tag"><span class="swatch" style="background:{_esc(v.get("color","#3A1D3D"))}"></span>'
        f'{_esc(v.get("source"))} · {_esc(v.get("tag"))}</span></div>'
        for v in snap.get("verbatims") or []
    )
    st.markdown(
        f"""
<h2 class="de">Representative verbatims</h2>
<p class="sub">A sample of genuinely relevant items, across sources. Paraphrased where needed; each is tagged by the mechanism it evidences.</p>
<div class="quotes">{cards}</div>
""",
        unsafe_allow_html=True,
    )


def render_engine(snap):
    engine = snap.get("engine") or {}
    steps = "".join(
        f'<div class="step"><div class="n">{_esc(s.get("n"))}</div>'
        f'<h4>{_esc(s.get("title"))}</h4><p>{_esc(s.get("body"))}</p></div>'
        for s in engine.get("steps") or []
    )
    note = _esc(engine.get("note") or "")
    st.markdown(
        f"""
<h2 class="de">How the engine works</h2>
<p class="sub">Collection is scripted (Play/App Store scrapers, YouTube Data API, Reddit); classification is an LLM pass against a fixed taxonomy, validated by a manual agreement check on a sample.</p>
<div class="steps">{steps}</div>
<div class="note">{note}</div>
""",
        unsafe_allow_html=True,
    )


def _init_state():
    st.session_state.setdefault("scrape_requested", False)
    st.session_state.setdefault("scrape_error", None)


def _load_or_none():
    path = ROOT / "data" / "snapshot.json"
    if not path.exists():
        return None
    try:
        os.chdir(ROOT)
        return load_snapshot()
    except Exception:
        return None


_init_state()
st.markdown(CSS, unsafe_allow_html=True)
os.chdir(ROOT)

status_slot = st.empty()
snap = _load_or_none()

head_l, head_r = st.columns([3, 2])
with head_l:
    st.markdown('<div class="brand"><b>Discovery Engine- Myntra</b></div>', unsafe_allow_html=True)
    if snap:
        st.markdown(
            f'<div class="meta">corpus {_fmt(snap["corpus_total"])} · relevant {_fmt(snap["relevant_count"])} · cached extract</div>',
            unsafe_allow_html=True,
        )
with head_r:
    scrape_clicked = st.button(
        "Scrape again",
        type="secondary",
        disabled=bool(st.session_state.scrape_requested),
        help="Runs the pipeline in the background and swaps the snapshot only if it succeeds.",
    )
    if snap:
        st.caption(f"Uses a cached snapshot — last extracted {snap.get('extracted_at', '—')}.")
    else:
        st.caption("No snapshot found — run the pipeline to generate data/snapshot.json")

if scrape_clicked and not st.session_state.scrape_requested:
    st.session_state.scrape_requested = True
    st.session_state.scrape_error = None

if st.session_state.scrape_error:
    st.error(st.session_state.scrape_error)

if not snap:
    st.warning("No snapshot found — run the pipeline to generate data/snapshot.json")
else:
    tab_corpus, tab_themes, tab_questions, tab_opps, tab_honesty, tab_verbs, tab_engine = st.tabs(
        ["Corpus", "Themes", "Questions", "Opportunities", "Honesty check", "Verbatims", "Engine"]
    )
    with tab_corpus:
        render_corpus(snap)
    with tab_themes:
        render_themes(snap)
    with tab_questions:
        render_questions(snap)
    with tab_opps:
        render_opportunities(snap)
    with tab_honesty:
        render_honesty(snap)
    with tab_verbs:
        render_verbatims(snap)
    with tab_engine:
        render_engine(snap)

# Scrape AFTER tabs so the current snapshot stays on screen the whole time.
if st.session_state.scrape_requested:
    with status_slot.status("Scraping… the current snapshot stays on screen.", expanded=True) as status:
        try:
            from pipeline.snapshot_pipeline import run_live_scrape_to_path

            SNAPSHOT_TMP.parent.mkdir(parents=True, exist_ok=True)
            if SNAPSHOT_TMP.exists():
                SNAPSHOT_TMP.unlink()

            def _progress(msg: str) -> None:
                status.write(msg)

            run_live_scrape_to_path(SNAPSHOT_TMP, progress=_progress)
            os.replace(SNAPSHOT_TMP, SNAPSHOT_PATH)
            load_snapshot.clear()
            st.session_state.scrape_requested = False
            st.session_state.scrape_error = None
            status.update(label="Snapshot updated", state="complete")
            st.rerun()
        except Exception as exc:  # noqa: BLE001
            st.session_state.scrape_requested = False
            st.session_state.scrape_error = str(exc)
            try:
                if SNAPSHOT_TMP.exists():
                    SNAPSHOT_TMP.unlink()
            except OSError:
                pass
            status.update(label="Scrape failed — snapshot unchanged", state="error")
            st.error(str(exc))
