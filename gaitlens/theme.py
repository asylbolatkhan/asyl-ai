"""Дизайн токендері және жалпы CSS / Дизайн-токены и общий CSS («клиникалық таза» стиль)."""
from __future__ import annotations

TOKENS = {
    "ink": "#14213D",
    "muted": "#55657A",
    "paper": "#FFFFFF",
    "surface": "#F2F5F8",
    "line": "#D9E0E7",
    "focus": "#3451D1",
    # condition colours (Baseline = de-emphasis reference; Verbal/VR validated pair)
    "Baseline": "#8492A6",
    "Verbal": "#3451D1",
    "VR": "#E8710A",
    # status: marks vs text (text variants keep >= 5:1 on white)
    "better": "#0E9F6E", "better_text": "#0B7A55",
    "worse": "#D64545", "worse_text": "#B33636",
}
COND_COLORS = {c: TOKENS[c] for c in ("Baseline", "Verbal", "VR")}
FONT_STACK = "Onest, Inter, 'Segoe UI', system-ui, sans-serif"

FONT_FACES = """
@font-face { font-family: Onest; src: url("/app/static/fonts/onest-latin.woff2") format("woff2"); font-weight: 400 700; font-display: swap;
  unicode-range: U+0000-00FF, U+0131, U+0152-0153, U+02BB-02BC, U+02C6, U+02DA, U+02DC, U+2000-206F, U+20AC, U+2122, U+2191, U+2193, U+2212, U+2215, U+FEFF, U+FFFD; }
@font-face { font-family: Onest; src: url("/app/static/fonts/onest-cyrillic.woff2") format("woff2"); font-weight: 400 700; font-display: swap;
  unicode-range: U+0301, U+0400-045F, U+0490-0491, U+04B0-04B1, U+2116; }
@font-face { font-family: Onest; src: url("/app/static/fonts/onest-cyrillic-ext.woff2") format("woff2"); font-weight: 400 700; font-display: swap;
  unicode-range: U+0460-052F, U+1C80-1C8A, U+20B4, U+2DE0-2DFF, U+A640-A69F, U+FE2E-FE2F; }
"""


def css() -> str:
    T = TOKENS
    return f"""<style>
{FONT_FACES}
:root {{
  --ink:{T['ink']}; --muted:{T['muted']}; --paper:{T['paper']}; --surface:{T['surface']}; --line:{T['line']};
  --focus:{T['focus']}; --better:{T['better']}; --better-text:{T['better_text']};
  --worse:{T['worse']}; --worse-text:{T['worse_text']};
}}
html, body, [data-testid="stAppViewContainer"], [data-testid="stSidebar"], button, input, textarea, select {{
  font-family: {FONT_STACK}; }}
[data-testid="stAppViewContainer"] {{ color: var(--ink); }}
[data-testid="stHeader"] {{ background: transparent; height: 2.5rem; }}
[data-testid="stDecoration"], footer {{ display: none; }}
[data-testid="stMainBlockContainer"] {{ padding-top: 2.2rem; padding-bottom: 4rem; max-width: 1320px; }}

/* headings */
h1, h2, h3 {{ color: var(--ink); letter-spacing: -0.015em; }}
h1 {{ font-weight: 700 !important; font-size: 2.35rem !important; line-height: 1.1 !important; }}
h2 {{ font-weight: 650 !important; font-size: 1.45rem !important; }}
h3 {{ font-weight: 600 !important; font-size: 1.12rem !important; }}

/* sidebar */
[data-testid="stSidebar"] {{ background: var(--surface); border-right: 1px solid var(--line); }}
[data-testid="stSidebarNav"] a span {{ font-weight: 500; }}

/* tabs (react-aria in Streamlit >= 1.5x): ink marks the open tab */
[data-testid="stTabs"] [role="tablist"] {{ gap: 1.6rem; }}
[data-testid="stTab"] p {{ font-size: 1rem; font-weight: 500; color: var(--muted); }}
[data-testid="stTab"][aria-selected="true"] p {{ color: var(--ink); font-weight: 650; }}

/* expander, containers */
[data-testid="stExpander"] details {{ border: 1px solid var(--line); border-radius: 12px; }}
[data-testid="stExpander"] summary p {{ font-weight: 600; }}

/* dataframe numbers */
[data-testid="stDataFrame"] {{ font-variant-numeric: tabular-nums; }}

/* focus */
a:focus-visible, button:focus-visible, [role="tab"]:focus-visible, input:focus-visible {{
  outline: 2px solid var(--focus) !important; outline-offset: 2px; }}

/* ---------- GaitLens blocks ---------- */
.gl-hero h1 {{ margin: 0 0 .55rem; padding: 0; }}
.gl-meta {{ display: flex; flex-wrap: wrap; gap: .35rem 1.6rem; margin: 0 !important; padding: 0 !important; color: var(--muted); font-size: .95rem; }}
.gl-meta div {{ display: flex; gap: .4rem; margin: 0; padding: 0; }}
.gl-meta dt, .gl-meta dd {{ margin: 0 !important; padding: 0 !important; }}
.gl-meta dt {{ font-weight: 400; }}
.gl-meta dd {{ margin: 0; color: var(--ink); font-weight: 600; font-variant-numeric: tabular-nums; }}
.gl-note {{ color: var(--muted); font-size: .86rem; margin: .9rem 0 0; }}

.gl-gps {{ margin-top: 1.6rem; }}
.gl-gps-title {{ font-size: .9rem; color: var(--muted); margin-bottom: .7rem; }}
.gl-gps-row {{ display: grid; grid-template-columns: repeat(3, minmax(0, 1fr)); gap: 0; border-top: 1px solid var(--line); }}
.gl-gps-col {{ padding: .8rem 1rem .2rem 0; }}
.gl-gps-col + .gl-gps-col {{ padding-left: 1rem; border-left: 1px solid var(--line); }}
.gl-cond {{ display: flex; align-items: flex-start; gap: .45rem; font-size: .9rem; font-weight: 500;
  line-height: 1.3; min-height: 2.6em; }}
.gl-sw {{ width: 10px; height: 10px; border-radius: 3px; flex: none; margin-top: .28em; }}
.gl-num {{ font-size: 2.6rem; font-weight: 700; letter-spacing: -0.03em; line-height: 1.05; margin: .35rem 0 .25rem;
  font-variant-numeric: tabular-nums; }}
.gl-num small {{ font-size: 1.1rem; font-weight: 500; color: var(--muted); margin-left: .1rem; }}
.gl-delta {{ font-size: .88rem; font-weight: 600; font-variant-numeric: tabular-nums; }}
.gl-delta.better {{ color: var(--better-text); }} .gl-delta.worse {{ color: var(--worse-text); }}
.gl-delta .within {{ font-weight: 400; color: var(--muted); }}
.gl-sub {{ font-size: .82rem; color: var(--muted); margin-top: .15rem; }}
.gl-scale {{ margin-top: .7rem; width: 100%; height: auto; display: block; }}

.gl-summary {{ border-left: 3px solid var(--ink); padding: .2rem 0 .2rem 1.3rem; margin: .4rem 0 1rem;
  display: grid; grid-template-columns: repeat(2, minmax(0, 1fr)); gap: 1.1rem 2.4rem; }}
.gl-summary section h4 {{ font-size: .98rem; font-weight: 650; margin: 0 0 .35rem; padding: 0; color: var(--ink); }}
.gl-summary ul {{ list-style: none; margin: 0; padding: 0; }}
.gl-summary li {{ position: relative; padding-left: 1.05rem; margin: .28rem 0; font-size: .93rem; line-height: 1.5; max-width: 72ch; }}
.gl-summary li::before {{ content: ""; position: absolute; left: 0; top: .55em; width: 7px; height: 7px; border-radius: 50%;
  background: var(--line); }}
.gl-summary li.better::before {{ background: var(--better); }}
.gl-summary li.worse::before {{ background: var(--worse); border-radius: 1px; transform: rotate(45deg); }}
.gl-summary li.note {{ color: var(--ink); }}
.gl-summary li.note::before {{ background: var(--ink); }}
.gl-summary .gl-full {{ grid-column: 1 / -1; }}
.gl-source {{ color: var(--muted); font-size: .8rem; }}

@media (max-width: 900px) {{
  .gl-summary {{ grid-template-columns: 1fr; }}
  .gl-num {{ font-size: 2rem; }}
}}
@media (max-width: 560px) {{
  .gl-gps-row {{ grid-template-columns: 1fr; }}
  .gl-gps-col + .gl-gps-col {{ border-left: 0; padding-left: 0; border-top: 1px solid var(--line); }}
  .gl-cond {{ min-height: 0; }}
}}
@media (max-width: 640px) {{
  [data-testid="stMainBlockContainer"] {{ padding-top: 4rem; }}
}}
@media (prefers-reduced-motion: reduce) {{
  *, *::before, *::after {{ transition: none !important; animation: none !important; }}
}}
</style>"""


def inject() -> None:
    import streamlit as st

    st.html(css())
