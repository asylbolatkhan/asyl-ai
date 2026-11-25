import numpy as np

from gaitlens import data


def test_load_shapes_and_types():
    disc, kine = data.load_all()
    assert len(disc) == len(kine) == 866 + 870 + 870
    for c in data.DISCRETE_COLS:
        assert disc[c].dtype.kind == "f", c  # decimal comma parsed into float
    assert set(disc["condition"].astype(str)) == set(data.CONDITIONS)


def test_subjects_natural_order():
    subs = data.subjects()
    assert len(subs) == 29
    assert subs[:3] == ["s61520_1", "s61520_2", "s61520_3"]
    assert subs[-1] == "s61520_29"


def test_one_side_per_subject():
    disc, _ = data.load_all()
    assert (disc.groupby("subject")["side"].nunique() == 1).all()


def test_cycle_counts():
    assert data.cycle_counts("s61520_7") == {"Baseline": 20, "Verbal": 30, "VR": 30}
    assert data.cycle_counts("s61520_4")["Baseline"] == 32


def test_missing_values_handled():
    disc, kine = data.load_all()
    na = disc[disc["pctmZeroStSagH"].isna()].groupby("subject").size().to_dict()
    # s22: hip moment missing in all 90 cycles; s3 / s19: one cycle each (empty field in CSV)
    assert na == {"s61520_22": 90, "s61520_3": 1, "s61520_19": 1}
    k22 = data.curves(data.subject_kine("s61520_22"), "mSagH")
    assert np.isnan(k22).all()
    # angles of the same subject are present
    assert not np.isnan(data.curves(data.subject_kine("s61520_22"), "aSagH")).any()


def test_discrete_and_kine_rows_aligned():
    disc, kine = data.load_all()
    assert (disc["subject"].values == kine["subject"].values).all()
    assert (disc["cycle"].values == kine["cycle"].values).all()
