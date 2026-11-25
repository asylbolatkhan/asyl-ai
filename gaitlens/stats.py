"""Өзгерістерді статистикалық бағалау / Статистическая оценка изменений."""
from __future__ import annotations

import numpy as np
import pandas as pd
from scipy import stats as sps

from .data import CONDITIONS, DISCRETE_COLS, PCT, curves, load_all, subjects
from .params import DISCRETE, GPS_MCID

FEEDBACK = ["Verbal", "VR"]


def cliffs_delta(x: np.ndarray, y: np.ndarray) -> float:
    """P(y > x) - P(y < x): positive → y (feedback) larger than x (baseline)."""
    x, y = np.asarray(x), np.asarray(y)
    if len(x) == 0 or len(y) == 0:
        return np.nan
    diff = y[:, None] - x[None, :]
    return float((np.sign(diff)).mean())


def cohens_d(x: np.ndarray, y: np.ndarray) -> float:
    nx, ny = len(x), len(y)
    if nx < 2 or ny < 2:
        return np.nan
    sp = np.sqrt(((nx - 1) * np.var(x, ddof=1) + (ny - 1) * np.var(y, ddof=1)) / (nx + ny - 2))
    return float((np.mean(y) - np.mean(x)) / sp) if sp > 0 else np.nan


def magnitude(delta: float) -> str:
    """Cliff's delta thresholds (Romano et al., 2006)."""
    a = abs(delta) if np.isfinite(delta) else 0.0
    if a < 0.147:
        return "negligible"
    if a < 0.33:
        return "small"
    if a < 0.474:
        return "medium"
    return "large"


def holm(pvals: np.ndarray) -> np.ndarray:
    p = np.asarray(pvals, dtype=float)
    out = np.full_like(p, np.nan)
    ok = np.isfinite(p)
    pv = p[ok]
    m = len(pv)
    if m == 0:
        return out
    order = np.argsort(pv)
    adj = np.empty(m)
    running = 0.0
    for rank, idx in enumerate(order):
        running = max(running, (m - rank) * pv[idx])
        adj[idx] = min(1.0, running)
    out[ok] = adj
    return out


def compare_param(base: np.ndarray, cond: np.ndarray, param: str) -> dict:
    base = base[np.isfinite(base)]
    cond = cond[np.isfinite(cond)]
    res = {
        "n_base": len(base), "n_cond": len(cond),
        "mean_base": np.mean(base) if len(base) else np.nan,
        "sd_base": np.std(base, ddof=1) if len(base) > 1 else np.nan,
        "mean_cond": np.mean(cond) if len(cond) else np.nan,
        "sd_cond": np.std(cond, ddof=1) if len(cond) > 1 else np.nan,
    }
    res["delta"] = res["mean_cond"] - res["mean_base"]
    mb = res["mean_base"]
    res["delta_pct"] = 100 * res["delta"] / abs(mb) if np.isfinite(mb) and abs(mb) > 1e-9 else np.nan
    if len(base) >= 3 and len(cond) >= 3:
        res["p"] = float(sps.mannwhitneyu(base, cond, alternative="two-sided").pvalue)
    else:
        res["p"] = np.nan
    res["cliffs"] = cliffs_delta(base, cond)
    res["cohen_d"] = cohens_d(base, cond)
    res["magnitude"] = magnitude(res["cliffs"])
    better = DISCRETE.get(param, {}).get("better", 0)
    if better == 0 or not np.isfinite(res["delta"]):
        res["direction"] = "neutral"
    else:
        res["direction"] = "better" if np.sign(res["delta"]) == better else "worse"
    res["clinical"] = bool(param == "GPS_a" and np.isfinite(res["delta"]) and abs(res["delta"]) >= GPS_MCID)
    return res


def compare_subject(disc: pd.DataFrame, params: list[str] | None = None) -> pd.DataFrame:
    """All params × feedback conditions vs Baseline for one subject's discrete data."""
    params = params or DISCRETE_COLS
    rows = []
    base_df = disc[disc["condition"] == "Baseline"]
    for cond in FEEDBACK:
        cdf = disc[disc["condition"] == cond]
        for p in params:
            r = compare_param(base_df[p].to_numpy(float), cdf[p].to_numpy(float), p)
            r.update(param=p, condition=cond)
            rows.append(r)
    df = pd.DataFrame(rows)
    df["p_holm"] = holm(df["p"].to_numpy())
    df["significant"] = df["p_holm"] < 0.05
    df["all_missing"] = (df["n_base"] == 0) | (df["n_cond"] == 0)
    return df


def ranked_changes(cmp: pd.DataFrame) -> pd.DataFrame:
    """Most important changes first: significant, then by |Cliff's delta|."""
    df = cmp[~cmp["all_missing"]].copy()
    df["abs_cliffs"] = df["cliffs"].abs()
    df = df.sort_values(["significant", "abs_cliffs"], ascending=[False, False])
    return df


def curve_summary(kine_subj: pd.DataFrame, signal: str) -> dict[str, dict]:
    """Mean/SD curve per condition (NaN-safe)."""
    out = {}
    for cond in CONDITIONS:
        arr = curves(kine_subj[kine_subj["condition"] == cond], signal)
        arr = arr[~np.isnan(arr).all(axis=1)] if len(arr) else arr
        if len(arr) == 0:
            out[cond] = {"n": 0, "mean": np.full(len(PCT), np.nan), "sd": np.full(len(PCT), np.nan)}
            continue
        out[cond] = {"n": len(arr), "mean": np.nanmean(arr, axis=0), "sd": np.nanstd(arr, axis=0, ddof=1) if len(arr) > 1 else np.zeros(len(PCT))}
    return out


def curve_difference(kine_subj: pd.DataFrame, signal: str, cond: str,
                     window: tuple[int, int] = (0, 100)) -> dict | None:
    """Where in the gait cycle (within `window`, % GC) does `cond` differ most from Baseline?"""
    cs = curve_summary(kine_subj, signal)
    if cs["Baseline"]["n"] == 0 or cs[cond]["n"] == 0:
        return None
    diff = cs[cond]["mean"] - cs["Baseline"]["mean"]
    if np.isnan(diff).all():
        return None
    in_win = (PCT >= window[0]) & (PCT <= window[1])
    i = int(np.nanargmax(np.where(in_win, np.abs(diff), -np.inf)))
    peak = diff[i]
    thr = 0.5 * abs(peak)
    def ok(j):
        return in_win[j] and abs(diff[j]) >= thr and np.sign(diff[j]) == np.sign(peak)

    lo = i
    while lo > 0 and ok(lo - 1):
        lo -= 1
    hi = i
    while hi < len(diff) - 1 and ok(hi + 1):
        hi += 1
    pooled_sd = np.sqrt((cs["Baseline"]["sd"][i] ** 2 + cs[cond]["sd"][i] ** 2) / 2)
    return {
        "signal": signal, "condition": cond,
        "peak_pct": int(PCT[i]), "peak_diff": float(peak),
        "from_pct": int(PCT[lo]), "to_pct": int(PCT[hi]),
        "rms_diff": float(np.sqrt(np.nanmean(diff ** 2))),
        "effect": float(peak / pooled_sd) if pooled_sd > 0 else np.nan,
    }


def gait_phase(pct: float) -> str:
    """Approximate phase key (stance ≈ 0–60 %, swing ≈ 60–100 %)."""
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


# ---------- Cohort level ----------

def subject_means() -> pd.DataFrame:
    """Mean of each discrete parameter per subject × condition."""
    discrete, _ = load_all()
    return (discrete.groupby(["subject", "condition"], observed=True)[DISCRETE_COLS]
            .mean().reset_index())


def cohort_tests() -> pd.DataFrame:
    """Wilcoxon signed-rank on per-subject means (unit = child, n ≤ 29)."""
    sm = subject_means()
    rows = []
    pairs = [("Baseline", "Verbal"), ("Baseline", "VR"), ("Verbal", "VR")]
    for a, b in pairs:
        A = sm[sm.condition == a].set_index("subject")
        B = sm[sm.condition == b].set_index("subject")
        for p in DISCRETE_COLS:
            j = pd.concat([A[p], B[p]], axis=1, keys=["a", "b"]).dropna()
            d = j["b"] - j["a"]
            pval = float(sps.wilcoxon(d).pvalue) if len(d) >= 6 and (d != 0).any() else np.nan
            better = DISCRETE[p]["better"]
            n_better = int((np.sign(d) == better).sum()) if better else np.nan
            rows.append({"pair": f"{b} vs {a}", "a": a, "b": b, "param": p, "n": len(d),
                         "mean_a": j["a"].mean(), "mean_b": j["b"].mean(),
                         "mean_diff": d.mean(), "median_diff": d.median(), "p": pval,
                         "n_better": n_better})
    df = pd.DataFrame(rows)
    df["p_holm"] = np.nan
    for pair, g in df.groupby("pair"):
        df.loc[g.index, "p_holm"] = holm(g["p"].to_numpy())
    return df


def responders(param: str = "GPS_a") -> pd.DataFrame:
    """Per subject Δ (feedback − baseline) for one parameter and best condition."""
    sm = subject_means()
    w = sm.pivot(index="subject", columns="condition", values=param)
    w = w.reindex(subjects())
    out = pd.DataFrame({"subject": w.index,
                        "Baseline": w["Baseline"].values,
                        "d_Verbal": (w["Verbal"] - w["Baseline"]).values,
                        "d_VR": (w["VR"] - w["Baseline"]).values})
    better = DISCRETE[param]["better"] or -1
    score = out[["d_Verbal", "d_VR"]] * better
    out["best"] = np.where(score["d_VR"] > score["d_Verbal"], "VR", "Verbal")
    return out
