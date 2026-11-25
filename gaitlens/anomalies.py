"""Тұрақсыз қадамдарды анықтау / Выявление нестабильных шагов.

Әдіс / Метод:
1. Әр бала × жағдай ішінде 4 бұрыш қисығы (+ момент, бар болса) бір векторға біріктіріледі,
   әр сигнал баланың өз SD-іне бөлінеді (масштабты теңестіру).
2. Әр циклдің медианалық қисықтан RMS қашықтығы → робаст z-score (MAD).
3. IsolationForest қосымша тексеру ретінде.
Цикл «тұрақсыз» болып белгіленеді, егер robust z > Z_THR және IsolationForest те аномалия десе
немесе z > Z_STRONG болса.
"""
from __future__ import annotations

import numpy as np
import pandas as pd
from sklearn.ensemble import IsolationForest

from .data import CONDITIONS, SIGNALS, curves

Z_THR = 2.5
Z_STRONG = 3.5
ANGLE_SIGNALS = ["aSagP", "aSagH", "aSagK", "aSagA"]


def _feature_matrix(kine_subj: pd.DataFrame) -> tuple[np.ndarray, list[str]]:
    used, blocks = [], []
    for sig in SIGNALS:
        arr = curves(kine_subj, sig)
        if np.isnan(arr).all():
            continue
        sd = np.nanstd(arr)
        blocks.append(arr / (sd if sd > 0 else 1.0))
        used.append(sig)
    return np.hstack(blocks), used


def detect(kine_subj: pd.DataFrame) -> pd.DataFrame:
    """Return per-cycle table: condition, cycle, distance, robust_z, iso_flag, unstable."""
    X_all, _ = _feature_matrix(kine_subj)
    rows = []
    for cond in CONDITIONS:
        mask = (kine_subj["condition"] == cond).to_numpy()
        X = X_all[mask]
        cyc = kine_subj.loc[mask, "cycle"].to_numpy()
        if len(X) == 0:
            continue
        # Fill isolated missing values with per-column median of this condition
        col_med = np.nanmedian(X, axis=0)
        X = np.where(np.isnan(X), col_med, X)
        med = np.median(X, axis=0)
        dist = np.sqrt(np.mean((X - med) ** 2, axis=1))
        mad = np.median(np.abs(dist - np.median(dist))) * 1.4826
        z = (dist - np.median(dist)) / mad if mad > 0 else np.zeros_like(dist)
        if len(X) >= 8:
            iso = IsolationForest(n_estimators=200, contamination="auto", random_state=0).fit(X)
            iso_flag = iso.predict(X) == -1
        else:
            iso_flag = np.zeros(len(X), bool)
        unstable = ((z > Z_THR) & iso_flag) | (z > Z_STRONG)
        for c, d, zz, f, u in zip(cyc, dist, z, iso_flag, unstable):
            rows.append({"condition": cond, "cycle": int(c), "distance": float(d),
                         "robust_z": float(zz), "iso_flag": bool(f), "unstable": bool(u)})
    return pd.DataFrame(rows)


def variability(kine_subj: pd.DataFrame) -> pd.DataFrame:
    """Mean across-cycle SD (°) of joint-angle curves per condition: lower = more consistent."""
    rows = []
    for cond in CONDITIONS:
        sub = kine_subj[kine_subj["condition"] == cond]
        row = {"condition": cond}
        sds = []
        for sig in ANGLE_SIGNALS:
            arr = curves(sub, sig)
            v = float(np.nanmean(np.nanstd(arr, axis=0, ddof=1))) if len(arr) > 1 else np.nan
            row[sig] = v
            sds.append(v)
        row["mean_sd"] = float(np.nanmean(sds))
        rows.append(row)
    return pd.DataFrame(rows)
