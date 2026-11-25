"""Сақталатын HTML есеп / Сохраняемый HTML-отчёт (печать в PDF из браузера)."""
from __future__ import annotations

import html
import re
from datetime import date

import pandas as pd

from .i18n import cond_name, t

CSS = """
:root{--ink:#14213D;--muted:#55657A;--line:#D9E0E7;--surface:#F2F5F8;--better:#0B7A55;--worse:#B33636}
*{box-sizing:border-box}
body{font-family:Onest,Inter,'Segoe UI',Arial,sans-serif;color:var(--ink);background:#fff;margin:0 auto;padding:32px 28px;
  max-width:1080px;line-height:1.5;font-variant-numeric:tabular-nums}
h1{font-size:30px;letter-spacing:-.02em;margin:0 0 6px}
h2{font-size:18px;font-weight:650;margin:34px 0 10px;padding-bottom:6px;border-bottom:1px solid var(--line)}
.sub{color:var(--muted);font-size:13px}
.meta{display:flex;flex-wrap:wrap;gap:4px 22px;margin:4px 0 0;font-size:14px;color:var(--muted)}
.meta b{color:var(--ink);font-weight:600}
.cards{display:grid;grid-template-columns:repeat(3,1fr);margin-top:22px;border-top:1px solid var(--line)}
.card{padding:12px 16px 4px 0}
.card+.card{padding-left:16px;border-left:1px solid var(--line)}
.card .k{font-size:13px;font-weight:500;display:flex;gap:7px;align-items:center}
.card .k i{width:10px;height:10px;border-radius:3px;display:inline-block}
.card .v{font-size:32px;font-weight:700;letter-spacing:-.03em;margin:4px 0}
.card .d{font-size:13px;color:var(--muted)}
.good{color:var(--better)!important;font-weight:600}.bad{color:var(--worse)!important;font-weight:600}
table{border-collapse:collapse;width:100%;font-size:12px}
th,td{border-bottom:1px solid var(--line);padding:6px 8px;text-align:left;vertical-align:top}
th{font-weight:600;color:var(--muted);background:var(--surface)}
.summary{border-left:3px solid var(--ink);padding-left:18px}
.summary h3{font-size:14.5px;margin:14px 0 4px}
.summary ul{margin:0 0 6px 18px;padding:0}
.summary li{margin:3px 0;max-width:80ch}
.strip h3{font-size:13px;font-weight:500;color:var(--muted);margin:14px 0 2px}
.disc{margin-top:28px;padding:12px 14px;background:var(--surface);border-radius:10px;font-size:13px}
.foot{margin-top:20px;font-size:11px;color:var(--muted)}
@media print{body{padding:0}.pb{page-break-before:always}}
@media (max-width:700px){.cards{grid-template-columns:1fr}.card+.card{border-left:0;padding-left:0;border-top:1px solid var(--line)}}
"""


def _font_css() -> str:
    """Embed the bundled Onest subsets so the saved report keeps its typography offline."""
    import base64
    from pathlib import Path

    from .theme import FONT_FACES

    root = Path(__file__).resolve().parent.parent / "static" / "fonts"
    css = FONT_FACES
    for name in ("onest-latin", "onest-cyrillic-ext", "onest-cyrillic"):
        f = root / f"{name}.woff2"
        if f.exists():
            b64 = base64.b64encode(f.read_bytes()).decode("ascii")
            css = css.replace(f'url("/app/static/fonts/{name}.woff2")', f'url("data:font/woff2;base64,{b64}")')
    return css


def _md_inline(s: str) -> str:
    s = html.escape(s)
    return re.sub(r"\*\*(.+?)\*\*", r"<b>\1</b>", s)


def summary_html(md: str) -> str:
    """Minimal markdown → HTML for the summary (bold lines as headers, '- ' bullets)."""
    out, in_list = [], False
    for line in md.splitlines():
        s = line.strip()
        if not s:
            continue
        if s.startswith(("- ", "* ")):
            if not in_list:
                out.append("<ul>")
                in_list = True
            out.append(f"<li>{_md_inline(s[2:])}</li>")
            continue
        if in_list:
            out.append("</ul>")
            in_list = False
        s = s.lstrip("#").strip()
        if s.startswith("**") and s.endswith("**"):
            out.append(f"<h3>{_md_inline(s.strip('*'))}</h3>")
        else:
            out.append(f"<p>{_md_inline(s)}</p>")
    if in_list:
        out.append("</ul>")
    return "\n".join(out)


def patient_report(subject: str, lang: str, exclude_unstable: bool = False,
                   summary_md: str | None = None) -> str:
    """Full standalone HTML report for one patient (used by the app and scripts/make_demo.py)."""
    from . import analysis, charts, data, model

    A = analysis.analyze_subject(subject, exclude_unstable)
    info = data.subject_info(subject)
    info_r = {"side": info["side"], "weight": float(info["weight"]), "height": float(info["height"]),
              "leg_length": float(info["LegLength"])}
    md = summary_md or analysis.template_markdown(A, lang)
    metrics = model.load_metrics()
    note = None
    if metrics:
        acc = metrics["binary"]["results"]["logreg"].get("per_subject", {}).get(subject)
        if acc is not None:
            note = t("model_separability", lang, acc=acc)
    from .gait_anim import filmstrip_svg
    from .theme import COND_COLORS

    kine_full = data.subject_kine(subject)
    strips = [(f"{cond_name('Baseline', lang)} — {cond_name(c, lang)}", filmstrip_svg(kine_full, c, COND_COLORS))
              for c in ("Verbal", "VR")]
    return build_report(analysis.subject_label(subject, lang), info_r, lang, A["counts"], A["gps"],
                        analysis.changes_table(A["cmp"], lang), md,
                        [charts.curves_figure(A["kine"], lang), charts.discrete_figure(A["disc"], lang)],
                        A["unstable"], model_note=note, strips=strips)


def build_report(subject_label: str, info: dict, lang: str, counts: dict, gps: dict,
                 table: pd.DataFrame, summary_md: str, figs: list, unstable: dict,
                 model_note: str | None = None, strips: list | None = None) -> str:
    from .theme import COND_COLORS

    cards = []
    for c in ["Baseline", "Verbal", "VR"]:
        g = gps.get(c, {})
        d = g.get("delta")
        delta_html = ""
        if d is not None and c != "Baseline":
            cls, word = ("good", t("gps_better", lang)) if d < 0 else ("bad", t("gps_worse", lang))
            delta_html = f'<div class="d {cls}">{"▼" if d < 0 else "▲"} {d:+.2f}° {word}</div>'
        else:
            delta_html = f'<div class="d">{t("gps_reference", lang)}</div>'
        sub = t("cycles_short", lang, n=counts.get(c, 0))
        if unstable.get(c):
            sub += ", " + t("unstable_short", lang, k=unstable[c])
        cards.append(
            f'<div class="card"><div class="k"><i style="background:{COND_COLORS[c]}"></i>'
            f'{html.escape(cond_name(c, lang))}</div>'
            f'<div class="v">{g.get("mean", float("nan")):.2f}°</div>{delta_html}'
            f'<div class="d">{sub}</div></div>')
    tbl = table.copy()
    for col in tbl.columns:
        if tbl[col].dtype.kind == "f":
            tbl[col] = tbl[col].map(lambda v: "—" if pd.isna(v) else f"{v:.3g}")
    fig_html = []
    for i, f in enumerate(figs):
        fig_html.append(f.to_html(full_html=False, include_plotlyjs="cdn" if i == 0 else False,
                                  config={"displaylogo": False}))
    side = t("side_" + info["side"], lang)
    strips_html = ""
    if strips:
        strips_html = f"<h2>{t('gait_title', lang)}</h2><div class='strip'>" + "".join(
            f"<h3>{html.escape(ttl)}</h3>{svg}" for ttl, svg in strips if svg) +             f"<p class='sub'>{t('strip_caption', lang)}</p></div>"
    return f"""<!doctype html>
<html lang="{'kk' if lang == 'kk' else 'ru'}"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>GaitLens — {html.escape(subject_label)}</title><style>{_font_css()}{CSS}</style></head>
<body>
<div class="sub">GaitLens, {date.today().isoformat()}</div>
<h1>{html.escape(subject_label)}</h1>
<div class="meta"><span>{t('measured_side', lang)} <b>{side}</b></span>
<span>{t('weight', lang)} <b>{info['weight']:.1f} {t('kg', lang)}</b></span>
<span>{t('height', lang)} <b>{info['height']:.2f} {t('m', lang)}</b></span>
<span>{t('leg_length', lang)} <b>{info['leg_length']:.2f} {t('m', lang)}</b></span></div>
<div class="sub" style="margin-top:22px">{t('gps_title', lang)}</div>
<div class="cards" style="margin-top:8px">{''.join(cards)}</div>
<h2>{t('ai_summary', lang)}</h2>
<div class="summary">{summary_html(summary_md)}</div>
{f'<p class="sub">{html.escape(model_note)}</p>' if model_note else ''}
{strips_html}
<h2 class="pb">{t('tab_table', lang)}</h2>
<div class="sub">{t('table_help', lang)}</div>
{tbl.to_html(index=False, escape=True, border=0)}
<h2 class="pb">{t('tab_curves', lang)}</h2>
{''.join(fig_html)}
<div class="disc">{t('disclaimer', lang)}</div>
<div class="foot">Data: De Mulder T. et al., KU Leuven RDR, 2024, https://doi.org/10.48804/JUNNWW (CC-BY-NC-SA-4.0). Generated by GaitLens.</div>
</body></html>"""
