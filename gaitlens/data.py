"""CSV деректерін оқу және біріктіру / Загрузка и объединение CSV-данных."""
from __future__ import annotations

import re
from functools import lru_cache
from pathlib import Path

import numpy as np
import pandas as pd

DATA_DIR = Path(__file__).resolve().parent.parent / "gait-cp-dataset"
CONDITIONS = ["Baseline", "Verbal", "VR"]
META_COLS = ["subject", "side", "weight", "height", "LegLength"]
DISCRETE_COLS = [
    "GPS_a", "GVS_aSagP", "GVS_aSagH", "GVS_aSagK", "GVS_aSagA",
    "aMinSagH", "pctmZeroStSagH",
]
SIGNALS = ["aSagP", "aSagH", "aSagK", "aSagA", "mSagH"]
PCT = np.arange(0, 101, 2)  # 0..100 % gait cycle, 51 points


def _read(path: Path) -> pd.DataFrame:
    df = pd.read_csv(path, sep=";", decimal=",", na_values=["NaN", "nan", ""])
    df["subject"] = df["subject"].astype(str).str.strip()
    df["side"] = df["side"].astype(str).str.strip().str.upper()
    return df.copy()


def subject_num(subject: str) -> int:
    m = re.search(r"_(\d+)$", subject)
    return int(m.group(1)) if m else 10**6


def signal_cols(signal: str) -> list[str]:
    return [f"{signal}_pct_GC_{p * 10}" for p in PCT]


@lru_cache(maxsize=1)
def load_all(data_dir: str | None = None) -> tuple[pd.DataFrame, pd.DataFrame]:
    """Return (discrete, kine). Both have `condition` and `cycle` columns.

    Row i of Discrete_* and Kinematics_* for one condition describe the same
    gait cycle (verified by subject/side equality at load time).
    """
    d = Path(data_dir) if data_dir else DATA_DIR
    disc_parts, kine_parts = [], []
    for cond in CONDITIONS:
        disc = _read(d / f"Discrete_Parameters_{cond}.csv")
        kine = _read(d / f"Kinematics_Kinetics_{cond}.csv")
        if len(disc) == len(kine) and (disc["subject"].values == kine["subject"].values).all():
            kine["cycle_id"] = np.arange(len(kine))
            disc["cycle_id"] = np.arange(len(disc))
        else:  # fallback: align by order within subject
            disc["cycle_id"] = disc.groupby("subject").cumcount()
            kine["cycle_id"] = kine.groupby("subject").cumcount()
        for df in (disc, kine):
            df["condition"] = cond
            df["cycle"] = df.groupby("subject").cumcount() + 1
        disc_parts.append(disc)
        kine_parts.append(kine.copy())
    discrete = pd.concat(disc_parts, ignore_index=True)
    kine = pd.concat(kine_parts, ignore_index=True)
    out = []
    for df in (discrete, kine):
        df = df.assign(
            condition=pd.Categorical(df["condition"], CONDITIONS, ordered=True),
            subj_num=df["subject"].map(subject_num),
        )
        out.append(df)
    return out[0], out[1]


def subjects() -> list[str]:
    discrete, _ = load_all()
    return sorted(discrete["subject"].unique(), key=subject_num)


def subject_info(subject: str) -> dict:
    discrete, _ = load_all()
    row = discrete[discrete["subject"] == subject].iloc[0]
    return {c: row[c] for c in META_COLS}


def cycle_counts(subject: str) -> dict[str, int]:
    discrete, _ = load_all()
    s = discrete[discrete["subject"] == subject]
    return {c: int((s["condition"] == c).sum()) for c in CONDITIONS}


def subject_discrete(subject: str) -> pd.DataFrame:
    discrete, _ = load_all()
    return discrete[discrete["subject"] == subject].copy()


def subject_kine(subject: str) -> pd.DataFrame:
    _, kine = load_all()
    return kine[kine["subject"] == subject].copy()


def curves(kine_subset: pd.DataFrame, signal: str) -> np.ndarray:
    """(n_cycles, 51) array of one signal."""
    return kine_subset[signal_cols(signal)].to_numpy(dtype=float)


def quality_report() -> pd.DataFrame:
    """Per subject: side, cycles per condition, missing values."""
    discrete, kine = load_all()
    rows = []
    for s in subjects():
        ds = discrete[discrete["subject"] == s]
        ks = kine[kine["subject"] == s]
        row = {"subject": s, "side": ds["side"].iloc[0]}
        for c in CONDITIONS:
            row[c] = int((ds["condition"] == c).sum())
        row["missing"] = int(ds[DISCRETE_COLS].isna().sum().sum() + ks.isna().sum().sum())
        rows.append(row)
    return pd.DataFrame(rows)
