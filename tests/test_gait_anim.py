import json

import numpy as np
import pytest

from gaitlens import data, gait_anim
from gaitlens.theme import COND_COLORS


@pytest.mark.parametrize("subject", ["s61520_1", "s61520_7", "s61520_22"])
def test_frames_complete_and_rigid(subject):
    f = gait_anim.figure_frames(data.subject_kine(subject))
    assert set(f) == {"Baseline", "Verbal", "VR"}
    for c, fr in f.items():
        P = {k: np.asarray(v) for k, v in fr["points"].items()}
        assert all(v.shape == (51, 2) for v in P.values())
        assert all(np.isfinite(v).all() for v in P.values())
        thigh = np.linalg.norm(P["knee"] - P["hip"], axis=1)
        shank = np.linalg.norm(P["ankle"] - P["knee"], axis=1)
        foot = np.linalg.norm(P["toe"] - P["heel"], axis=1)
        assert np.allclose(thigh, 0.5, atol=1e-3) and np.allclose(shank, 0.5, atol=1e-3)
        assert np.allclose(foot, gait_anim.FOOT_RATIO, atol=1e-3)


def test_neutral_pose_is_standing():
    pts = gait_anim.leg_points([0], [0], [0], [0])
    assert np.allclose(pts["ankle"][0], [0, -1])
    assert np.allclose(pts["toe"][0, 1], -1)  # foot flat on the ground


def test_component_html_embeds_data():
    html = gait_anim.component_html(data.subject_kine("s61520_22"), 0.72,
                                    {"title": "x", "phases": {}, "conds": {}}, COND_COLORS)
    assert "/*__DATA__*/null" not in html
    payload = html.split("const D = ", 1)[1].split(";\n", 1)[0]
    d = json.loads(payload)
    assert d["initial"] == "VR" and len(d["pct"]) == 51 and d["ground"] < -0.9


def test_filmstrip_svg():
    svg = gait_anim.filmstrip_svg(data.subject_kine("s61520_1"), "VR", COND_COLORS)
    assert svg.startswith("<svg") and svg.count("<path") == 10
