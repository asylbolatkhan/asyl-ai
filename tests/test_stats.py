import numpy as np
import pandas as pd
import pytest
from sklearn.model_selection import LeaveOneGroupOut

from gaitlens import analysis, anomalies, data, model, stats, summary
from gaitlens.i18n import TEXTS


def test_cliffs_delta_extremes():
    assert stats.cliffs_delta(np.array([1, 2, 3]), np.array([4, 5, 6])) == 1.0
    assert stats.cliffs_delta(np.array([4, 5, 6]), np.array([1, 2, 3])) == -1.0
    assert stats.cliffs_delta(np.array([1, 2]), np.array([1, 2])) == 0.0


def test_holm_monotone_and_bounded():
    adj = stats.holm(np.array([0.01, 0.04, 0.03, np.nan]))
    assert np.isnan(adj[3])
    assert np.allclose(adj[:3], [0.03, 0.06, 0.06])


def test_direction_hip_extension():
    base = np.array([10.0, 11, 12, 13, 14])
    cond = base - 5  # smaller minimal hip angle = more extension = better
    r = stats.compare_param(base, cond, "aMinSagH")
    assert r["direction"] == "better" and r["magnitude"] == "large"
    r = stats.compare_param(base, base + 5, "GPS_a")
    assert r["direction"] == "worse"


def test_compare_subject_handles_all_missing():
    cmp = stats.compare_subject(data.subject_discrete("s61520_22"))
    row = cmp[cmp.param == "pctmZeroStSagH"]
    assert row["all_missing"].all()
    assert len(stats.ranked_changes(cmp)) == len(cmp) - 2


def test_anomalies_rate_reasonable():
    a = anomalies.detect(data.subject_kine("s61520_1"))
    assert len(a) == sum(data.cycle_counts("s61520_1").values())
    assert a["unstable"].mean() < 0.25


def test_summary_both_languages_and_disclaimer():
    s = "s61520_22"
    k = data.subject_kine(s)
    cmp = stats.compare_subject(data.subject_discrete(s))
    f = summary.build_facts(s, data.subject_info(s), data.cycle_counts(s), cmp,
                            analysis.hip_extension_peaks(k), anomalies.detect(k), anomalies.variability(k))
    for lang, word in [("kk", "диагноз"), ("ru", "диагноз")]:
        md = summary.to_markdown(summary.template_summary(f, lang))
        assert word in md and "b770" in md and "d450" in md


def test_i18n_keys_match():
    assert set(TEXTS["kk"]) == set(TEXTS["ru"])


def test_subject_split_has_no_leakage():
    feats = model.normalize_within_subject(model.build_features())
    groups = feats["subject"].to_numpy()
    for tr, te in LeaveOneGroupOut().split(feats, groups=groups):
        assert set(groups[tr]).isdisjoint(set(groups[te]))


@pytest.mark.parametrize("lang", ["kk", "ru"])
def test_patient_report_standalone(lang):
    from gaitlens.report import patient_report
    html = patient_report("s61520_22", lang)
    assert html.startswith("<!doctype html>")
    assert "b770" in html and "d450" in html and "10.48804/JUNNWW" in html
    assert "диагноз" in html


def test_hip_peak_consistent_with_min_angle():
    """Peak-extension angle from mean curve moves in the same direction as aMinSagH."""
    A = analysis.analyze_subject("s61520_1")
    hp = A["facts"]["hip_curve"]
    cmp = A["cmp"]
    for c in ["Verbal", "VR"]:
        d = cmp[(cmp.condition == c) & (cmp.param == "aMinSagH")].delta.iloc[0]
        assert np.sign(hp[c]["value"] - hp["Baseline"]["value"]) == np.sign(d)
