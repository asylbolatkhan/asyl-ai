"""Жүріс анимациясына арналған схемалық аяқ моделі / Схематическая модель ноги для анимации.

Сагитталь жазықтықтағы тура кинематика (орташа цикл, 51 кадр):
    сан   θt = ұршық бүгілуі − жамбас еңкеюі     (тік сызықтан, алға +)
    сирақ θs = θt − тізе бүгілуі
    табан φ  = θs + тобық дорсифлексиясы       (көлденеңнен, ұшы жоғары +)
Кесінділер ұзындығы LegLength бойынша: сан = сирақ = L/2, табан = 0.27·L.
Координаталар: x — алға, y — жоғары, ұршық буыны (0, 0) нүктесінде.
"""
from __future__ import annotations

import json
from pathlib import Path

import numpy as np
import pandas as pd

from .data import CONDITIONS, PCT
from .stats import curve_summary

FOOT_RATIO = 0.27
HEEL_RATIO = 0.25  # heel sits this fraction of foot length behind the ankle
PELVIS_RATIO = 0.32
COMPONENT = Path(__file__).resolve().parent / "components" / "gait.html"


def _mean(kine: pd.DataFrame, signal: str, cond: str) -> np.ndarray | None:
    d = curve_summary(kine, signal)[cond]
    if d["n"] == 0 or np.isnan(d["mean"]).any():
        return None
    return d["mean"]


def leg_points(p, h, k, a, leg_length: float = 1.0) -> dict[str, np.ndarray]:
    """Joint coordinates for arrays of angles (degrees). Returns name -> (n, 2)."""
    p, h, k, a = (np.radians(np.asarray(x, float)) for x in (p, h, k, a))
    lt = ls = leg_length / 2
    lf = FOOT_RATIO * leg_length
    th = h - p
    ts = th - k
    phi = ts + a
    hip = np.zeros((len(th), 2))
    knee = hip + lt * np.c_[np.sin(th), -np.cos(th)]
    ankle = knee + ls * np.c_[np.sin(ts), -np.cos(ts)]
    foot_dir = np.c_[np.cos(phi), np.sin(phi)]
    toe = ankle + (1 - HEEL_RATIO) * lf * foot_dir
    heel = ankle - HEEL_RATIO * lf * foot_dir
    pelvis_top = hip + PELVIS_RATIO * leg_length * np.c_[np.sin(p), np.cos(p)]
    return {"pelvis": pelvis_top, "hip": hip, "knee": knee, "ankle": ankle, "heel": heel, "toe": toe}


def figure_frames(kine: pd.DataFrame, leg_length: float = 1.0) -> dict[str, dict]:
    """Per condition: rounded joint coordinates for 51 frames + raw angles for the readout."""
    out = {}
    for cond in CONDITIONS:
        curves = {s: _mean(kine, s, cond) for s in ("aSagP", "aSagH", "aSagK", "aSagA")}
        if any(v is None for v in curves.values()):
            continue
        pts = leg_points(curves["aSagP"], curves["aSagH"], curves["aSagK"], curves["aSagA"], leg_length)
        out[cond] = {
            "points": {k: np.round(v, 4).tolist() for k, v in pts.items()},
            "hip": np.round(curves["aSagH"], 1).tolist(),
            "pelvis": np.round(curves["aSagP"], 1).tolist(),
            "knee": np.round(curves["aSagK"], 1).tolist(),
        }
    return out


def ground_level(frames: dict[str, dict]) -> float:
    """Lowest foot point across all conditions and frames (treadmill belt height)."""
    ys = [np.asarray(f["points"][j])[:, 1].min() for f in frames.values() for j in ("heel", "toe", "ankle")]
    return float(min(ys)) if ys else -1.0


def phase_key(pct: float) -> str:
    if pct < 10:
        return "loading"
    if pct < 30:
        return "midstance"
    if pct < 50:
        return "terminal_stance"
    if pct < 62:
        return "preswing"
    if pct < 87:
        return "swing"
    return "terminal_swing"


def component_html(kine: pd.DataFrame, leg_length: float, labels: dict, colors: dict,
                   initial: str = "VR") -> str:
    """Self-contained HTML (SVG + JS) for st.components.v1.html."""
    frames = figure_frames(kine, leg_length=1.0)  # normalised; the figure is scaled in JS
    payload = {
        "frames": frames, "ground": ground_level(frames), "pct": PCT.tolist(),
        "phases": [phase_key(p) for p in PCT], "labels": labels, "colors": colors,
        "initial": initial if initial in frames else next((c for c in ("VR", "Verbal") if c in frames), None),
        "toeOff": 60,
    }
    tpl = COMPONENT.read_text(encoding="utf-8")
    return tpl.replace("/*__DATA__*/null", json.dumps(payload, ensure_ascii=False))


def filmstrip_svg(kine: pd.DataFrame, cond: str, colors: dict, pcts=(0, 20, 40, 60, 80),
                  width: int = 640, height: int = 170) -> str:
    """Static SVG: a few phases of the cycle, Baseline ghost + `cond` (for the HTML report)."""
    frames = figure_frames(kine)
    if "Baseline" not in frames or cond not in frames:
        return ""
    g = ground_level(frames)
    cell = width / len(pcts)
    scale = (height - 34) / (0.42 + abs(g))
    parts = [f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {width} {height}" width="100%" '
             f'role="img" font-family="Onest, Inter, sans-serif" font-size="11">']
    order = ["pelvis", "hip", "knee", "ankle", "heel", "toe"]
    for i, pct in enumerate(pcts):
        j = list(PCT).index(pct)
        cx, cy = cell * i + cell * 0.45, 14 + 0.36 * scale
        parts.append(f'<line x1="{cell * i + 8:.1f}" x2="{cell * (i + 1) - 8:.1f}" y1="{cy - g * scale:.1f}" '
                     f'y2="{cy - g * scale:.1f}" stroke="#D9E0E7" stroke-width="1"/>')
        for c, col, w, op in (("Baseline", colors["Baseline"], 5, 0.55), (cond, colors[cond], 3.5, 1)):
            pts = frames[c]["points"]
            xy = [(cx + pts[n][j][0] * scale, cy - pts[n][j][1] * scale) for n in order]
            path = "M" + " L".join(f"{x:.1f},{y:.1f}" for x, y in xy[:4]) + \
                   f" M{xy[4][0]:.1f},{xy[4][1]:.1f} L{xy[5][0]:.1f},{xy[5][1]:.1f}"
            parts.append(f'<path d="{path}" fill="none" stroke="{col}" stroke-width="{w}" '
                         f'stroke-linecap="round" stroke-linejoin="round" opacity="{op}"/>')
        parts.append(f'<text x="{cell * i + cell / 2:.1f}" y="{height - 6}" text-anchor="middle" '
                     f'fill="#55657A">{pct}%</text>')
    parts.append("</svg>")
    return "".join(parts)
