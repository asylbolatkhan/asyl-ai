"""Бір пациентті толық талдау (Streamlit-ке тәуелсіз) / Полный анализ пациента (без Streamlit)."""
from __future__ import annotations

import numpy as np
import pandas as pd

from . import anomalies, data, stats, summary
from .i18n import cond_name, t
from .params import DISCRETE
from .params import name as pname

HIP_EXT_WINDOW = (30, 70)  # terminal stance → pre-swing, % GC — where peak hip extension happens


def hip_extension_peaks(kine: pd.DataFrame) -> dict:
    """Per condition: when (% GC) and how much the mean hip curve reaches maximal extension."""
    out = {}
    for c, d in stats.curve_summary(kine, "aSagH").items():
        if d["n"] == 0 or np.isnan(d["mean"]).all():
            continue
        win = (data.PCT >= HIP_EXT_WINDOW[0]) & (data.PCT <= HIP_EXT_WINDOW[1])
        i = int(np.nanargmin(np.where(win, d["mean"], np.inf)))
        out[c] = {"pct": int(data.PCT[i]), "value": round(float(d["mean"][i]), 2)}
    return out


def analyze_subject(subject: str, exclude_unstable: bool = False) -> dict:
    disc = data.subject_discrete(subject)
    kine = data.subject_kine(subject)
    anom = anomalies.detect(kine)
    var = anomalies.variability(kine)
    if exclude_unstable and len(anom):
        bad = set(map(tuple, anom.loc[anom.unstable, ["condition", "cycle"]].to_numpy()))
        keep_d = [(c, n) not in bad for c, n in zip(disc["condition"].astype(str), disc["cycle"])]
        keep_k = [(c, n) not in bad for c, n in zip(kine["condition"].astype(str), kine["cycle"])]
        disc, kine = disc[keep_d], kine[keep_k]
    cmp = stats.compare_subject(disc)
    hip_curve = hip_extension_peaks(kine)
    counts = {c: int((disc["condition"] == c).sum()) for c in data.CONDITIONS}
    unstable = {c: int(anom.loc[anom.condition == c, "unstable"].sum()) for c in data.CONDITIONS}
    gps = {}
    for c in data.CONDITIONS:
        v = disc.loc[disc["condition"] == c, "GPS_a"]
        r = cmp[(cmp.condition == c) & (cmp.param == "GPS_a")]
        gps[c] = {"mean": float(v.mean()) if len(v) else np.nan,
                  "delta": float(r.delta.iloc[0]) if len(r) else None}
    facts = summary.build_facts(subject, data.subject_info(subject), counts, cmp, hip_curve, anom, var)
    return {"subject": subject, "disc": disc, "kine": kine, "anom": anom, "var": var, "cmp": cmp,
            "counts": counts, "unstable": unstable, "gps": gps, "facts": facts}


def subject_label(s: str, lng: str) -> str:
    info = data.subject_info(s)
    return f"{t('patient', lng)} {data.subject_num(s)} · {t('side_' + info['side'], lng)}"


def _fmt(v: float, nd: int = 2) -> str:
    return "—" if v is None or not np.isfinite(v) else f"{v:.{nd}f}"


def changes_table(cmp: pd.DataFrame, lng: str) -> pd.DataFrame:
    rows = []
    for _, r in cmp.iterrows():
        unit = DISCRETE[r.param]["unit"]
        if r.all_missing:
            assess = t("data_missing", lng)
        elif r.magnitude == "negligible" or not r.significant:
            assess = t("assess_none", lng)
        else:
            assess = t(f"assess_{r.direction}", lng)
        rows.append({
            t("col_param", lng): pname(r.param, lng, short=True),
            t("col_condition", lng): cond_name(r.condition, lng),
            t("col_base", lng): f"{_fmt(r.mean_base)} ± {_fmt(r.sd_base)} {unit}",
            t("col_cond", lng): f"{_fmt(r.mean_cond)} ± {_fmt(r.sd_cond)} {unit}",
            t("col_delta", lng): r.delta,
            t("col_delta_pct", lng): r.delta_pct,
            t("col_effect", lng): f"{_fmt(r.cliffs)} ({t('mag_' + r.magnitude, lng)})",
            t("col_p", lng): r.p_holm,
            t("col_n", lng): f"{r.n_base} / {r.n_cond}",
            t("col_assess", lng): assess,
        })
    return pd.DataFrame(rows)


def template_markdown(A: dict, lng: str) -> str:
    return summary.to_markdown(summary.template_summary(A["facts"], lng))
