"""Жүріс жағдайын жіктеу / Классификация условия ходьбы.

Адал бағалау / Честная оценка:
- Бөлу ТЕК subject бойынша (LeaveOneGroupOut, groups=subject): бір баланың
  циклдері ешқашан train мен test-ке бірге түспейді.
- Белгілер әр баланың ӨЗ циклдеріне қатысты стандартталады (барлық жағдай бойынша,
  жағдай белгісін пайдаланбай) — модель баланы емес, жағдайды тануы үшін.
- Салыстыру: кездейсоқ деңгей (DummyClassifier).
"""
from __future__ import annotations

import json
import warnings
from pathlib import Path

import numpy as np
import pandas as pd
from sklearn.dummy import DummyClassifier
from sklearn.ensemble import RandomForestClassifier
from sklearn.impute import SimpleImputer
from sklearn.inspection import permutation_importance
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import accuracy_score, balanced_accuracy_score, confusion_matrix, f1_score
from sklearn.model_selection import GroupKFold, LeaveOneGroupOut
from sklearn.pipeline import make_pipeline
from sklearn.preprocessing import StandardScaler

from .data import CONDITIONS, DISCRETE_COLS, PCT, SIGNALS, curves, load_all

METRICS_PATH = Path(__file__).resolve().parent.parent / "models" / "metrics.json"
PHASES = {"ic": 0, "mst": 20, "tst": 40, "to": 60, "msw": 80}


def build_features() -> pd.DataFrame:
    """One row per gait cycle: discrete params + curve features."""
    discrete, kine = load_all()
    feats = discrete[["subject", "condition", "cycle"] + DISCRETE_COLS].reset_index(drop=True).copy()
    kine = kine.reset_index(drop=True)
    assert (feats["subject"].values == kine["subject"].values).all()
    cols = {}
    for sig in SIGNALS:
        arr = curves(kine, sig)
        with warnings.catch_warnings():  # all-NaN rows (missing hip moment) → NaN, imputed later
            warnings.simplefilter("ignore", RuntimeWarning)
            cols[f"{sig}_min"] = np.nanmin(arr, axis=1)
            cols[f"{sig}_max"] = np.nanmax(arr, axis=1)
            cols[f"{sig}_rom"] = cols[f"{sig}_max"] - cols[f"{sig}_min"]
            cols[f"{sig}_mean"] = np.nanmean(arr, axis=1)
            for ph, pct in PHASES.items():
                cols[f"{sig}_{ph}"] = arr[:, list(PCT).index(pct)]
    feats = pd.concat([feats, pd.DataFrame(cols)], axis=1)
    feats["condition"] = feats["condition"].astype(str)
    return feats


def feature_cols(feats: pd.DataFrame) -> list[str]:
    return [c for c in feats.columns if c not in ("subject", "condition", "cycle")]


def normalize_within_subject(feats: pd.DataFrame) -> pd.DataFrame:
    """z-score every feature within each subject over ALL its cycles (label-free)."""
    out = feats.copy()
    fc = feature_cols(feats)
    g = out.groupby("subject")[fc]
    mu, sd = g.transform("mean"), g.transform("std").replace(0, np.nan)
    out[fc] = (out[fc] - mu) / sd
    return out


def _models() -> dict:
    return {
        "dummy": DummyClassifier(strategy="stratified", random_state=0),
        "logreg": make_pipeline(SimpleImputer(strategy="median"), StandardScaler(),
                                LogisticRegression(max_iter=2000, class_weight="balanced", C=0.5)),
        "rf": make_pipeline(SimpleImputer(strategy="median"),
                            RandomForestClassifier(n_estimators=300, min_samples_leaf=3,
                                                   class_weight="balanced", random_state=0, n_jobs=-1)),
    }


def _labels(feats: pd.DataFrame, task: str) -> np.ndarray:
    if task == "binary":
        return np.where(feats["condition"] == "Baseline", "Baseline", "Feedback")
    return feats["condition"].to_numpy()


def evaluate(task: str = "3class", normalized: bool = True) -> dict:
    feats = build_features()
    if normalized:
        feats = normalize_within_subject(feats)
    fc = feature_cols(feats)
    X = feats[fc].to_numpy(float)
    y = _labels(feats, task)
    groups = feats["subject"].to_numpy()
    labels = ["Baseline", "Feedback"] if task == "binary" else CONDITIONS
    logo = LeaveOneGroupOut()
    results = {}
    for name, model in _models().items():
        pred = np.empty(len(y), dtype=object)
        per_subject = []
        per_subject_map = {}
        for tr, te in logo.split(X, y, groups):
            # Strict subject split check
            assert set(groups[tr]).isdisjoint(set(groups[te]))
            model.fit(X[tr], y[tr])
            pred[te] = model.predict(X[te])
            b = balanced_accuracy_score(y[te], pred[te])
            per_subject.append(b)
            per_subject_map[str(groups[te][0])] = float(b)
        results[name] = {
            "accuracy": float(accuracy_score(y, pred)),
            "balanced_accuracy": float(balanced_accuracy_score(y, pred)),
            "macro_f1": float(f1_score(y, pred, average="macro")),
            "per_subject_bacc_mean": float(np.mean(per_subject)),
            "per_subject_bacc_sd": float(np.std(per_subject)),
            "per_subject": per_subject_map,
            "confusion": confusion_matrix(y, pred, labels=labels).tolist(),
        }
    return {"task": task, "normalized": normalized, "labels": labels,
            "n_cycles": int(len(y)), "n_subjects": int(len(set(groups))),
            "cv": "LeaveOneGroupOut (subject)", "results": results}


def importance(task: str = "3class", top: int = 15) -> list[dict]:
    """Permutation importance of the RF model on held-out subjects (GroupKFold 5)."""
    feats = normalize_within_subject(build_features())
    fc = feature_cols(feats)
    X = feats[fc].to_numpy(float)
    y = _labels(feats, task)
    groups = feats["subject"].to_numpy()
    imp = np.zeros(len(fc))
    for tr, te in GroupKFold(n_splits=5).split(X, y, groups):
        assert set(groups[tr]).isdisjoint(set(groups[te]))
        m = _models()["rf"].fit(X[tr], y[tr])
        r = permutation_importance(m, X[te], y[te], scoring="balanced_accuracy",
                                   n_repeats=5, random_state=0, n_jobs=-1)
        imp += r.importances_mean / 5
    order = np.argsort(imp)[::-1][:top]
    return [{"feature": fc[i], "importance": float(imp[i])} for i in order]


def run_all() -> dict:
    out = {
        "3class": evaluate("3class", True),
        "binary": evaluate("binary", True),
        "3class_raw": evaluate("3class", False),
        "binary_raw": evaluate("binary", False),
        "importance_3class": importance("3class"),
        "importance_binary": importance("binary"),
    }
    METRICS_PATH.parent.mkdir(exist_ok=True)
    METRICS_PATH.write_text(json.dumps(out, indent=2, ensure_ascii=False), encoding="utf-8")
    return out


def load_metrics() -> dict | None:
    if METRICS_PATH.exists():
        return json.loads(METRICS_PATH.read_text(encoding="utf-8"))
    return None
