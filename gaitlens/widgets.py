"""Пациент бетінің HTML блоктары / HTML-блоки страницы пациента."""
from __future__ import annotations

import html
import re

import numpy as np

from .data import CONDITIONS, subject_num
from .i18n import cond_name, t
from .params import GPS_MCID
from .theme import COND_COLORS, TOKENS


def _md(s: str) -> str:
    return re.sub(r"\*\*(.+?)\*\*", r"<strong>\1</strong>", html.escape(s))


def hero_html(subject: str, info: dict, lang: str) -> str:
    items = [
        (t("measured_side", lang), t("side_" + info["side"], lang)),
        (t("weight", lang), f"{info['weight']:.1f} {t('kg', lang)}"),
        (t("height", lang), f"{info['height']:.2f} {t('m', lang)}"),
        (t("leg_length", lang), f"{info['LegLength']:.2f} {t('m', lang)}"),
        ("ID", subject),
    ]
    meta = "".join(f"<div><dt>{html.escape(k)}</dt><dd>{html.escape(v)}</dd></div>" for k, v in items)
    return (f'<div class="gl-hero"><h1>{t("patient", lang)} {subject_num(subject)}</h1>'
            f'<dl class="gl-meta">{meta}</dl></div>')


def _scale_svg(gps: dict, lang: str, width: int = 640, height: int = 46) -> str:
    vals = {c: gps[c]["mean"] for c in CONDITIONS if np.isfinite(gps[c]["mean"])}
    if "Baseline" not in vals:
        return ""
    b = vals["Baseline"]
    lo = min(min(vals.values()), b - GPS_MCID) - 0.6
    hi = max(max(vals.values()), b + GPS_MCID) + 0.6
    pad = 14
    x = lambda v: pad + (v - lo) / (hi - lo) * (width - 2 * pad)  # noqa: E731
    y = 18
    band = (f'<rect x="{x(b - GPS_MCID):.1f}" y="{y - 9}" width="{x(b + GPS_MCID) - x(b - GPS_MCID):.1f}" '
            f'height="18" rx="9" fill="{TOKENS["surface"]}"/>')
    axis = f'<line x1="{pad}" x2="{width - pad}" y1="{y}" y2="{y}" stroke="{TOKENS["line"]}" stroke-width="1"/>'
    ticks = ""
    for v in np.arange(np.ceil(lo), np.floor(hi) + 1):
        ticks += (f'<text x="{x(v):.1f}" y="{height - 4}" text-anchor="middle" font-size="11" '
                  f'fill="{TOKENS["muted"]}">{v:.0f}</text>')
    dots = ""
    for c in ["Baseline", "Verbal", "VR"]:  # feedback drawn last, on top
        if c not in vals:
            continue
        dots += (f'<circle cx="{x(vals[c]):.1f}" cy="{y}" r="7" fill="{COND_COLORS[c]}" stroke="#fff" stroke-width="2">'
                 f'<title>{html.escape(cond_name(c, lang))}: {vals[c]:.2f}°</title></circle>')
    label = ""
    svg = (f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {width} {height}" width="{width}" height="{height}" '
           f'font-family="Segoe UI, Inter, sans-serif">{band}{axis}{ticks}{label}{dots}</svg>')
    alt = "; ".join(f"{cond_name(c, lang)} {v:.2f}°" for c, v in vals.items())
    # st.html strips inline <svg>, so the scale is embedded as an image
    return (f'<img class="gl-scale" alt="GPS: {html.escape(alt)}" src="{svg_data_uri(svg)}">'
            f'<div class="gl-sub">{html.escape(t("gps_band", lang, mcid=GPS_MCID))}</div>')


def svg_data_uri(svg: str) -> str:
    import base64

    return "data:image/svg+xml;base64," + base64.b64encode(svg.encode("utf-8")).decode("ascii")


def gps_html(A: dict, lang: str) -> str:
    cols = []
    for c in CONDITIONS:
        g = A["gps"][c]
        num = "—" if not np.isfinite(g["mean"]) else f'{g["mean"]:.2f}<small>°</small>'
        delta = ""
        if c != "Baseline" and g["delta"] is not None:
            d = g["delta"]
            cls, arrow, word = ("better", "▼", t("gps_better", lang)) if d < 0 else ("worse", "▲", t("gps_worse", lang))
            within = f' <span class="within">({t("gps_within", lang)})</span>' if abs(d) < GPS_MCID else ""
            delta = f'<div class="gl-delta {cls}">{arrow} {d:+.2f}° {word}{within}</div>'
        else:
            delta = f'<div class="gl-delta" style="color:var(--muted);font-weight:400">{t("gps_reference", lang)}</div>'
        sub = t("cycles_short", lang, n=A["counts"][c])
        if A["unstable"][c]:
            sub += ", " + t("unstable_short", lang, k=A["unstable"][c])
        cols.append(f'<div class="gl-gps-col"><div class="gl-cond"><span class="gl-sw" style="background:{COND_COLORS[c]}">'
                    f'</span>{html.escape(cond_name(c, lang))}</div><div class="gl-num">{num}</div>{delta}'
                    f'<div class="gl-sub">{sub}</div></div>')
    return (f'<div class="gl-gps"><div class="gl-gps-title">{html.escape(t("gps_title", lang))}</div>'
            f'<div class="gl-gps-row">{"".join(cols)}</div>{_scale_svg(A["gps"], lang)}</div>')


def summary_html(sections: list, source_note: str) -> str:
    """Sections from summary.template_summary → two-column HTML; ICF and limits span full width."""
    out = []
    for i, (title, lines) in enumerate(sections):
        items = "".join(
            f'<li class="{getattr(ln, "kind", None) or ""}">{_md(ln)}</li>' for ln in lines)
        full = " gl-full" if i >= len(sections) - 2 else ""
        out.append(f'<section class="{full.strip()}"><h4>{html.escape(title)}</h4><ul>{items}</ul></section>')
    out.append(f'<div class="gl-full gl-source">{html.escape(source_note)}</div>')
    return f'<div class="gl-summary">{"".join(out)}</div>'
