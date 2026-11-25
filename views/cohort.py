"""Барлық пациенттер бойынша шолу / Обзор по всем пациентам."""
import streamlit as st

from gaitlens import charts, stats
from gaitlens.data import DISCRETE_COLS
from gaitlens.i18n import cond_name, t
from gaitlens.params import DISCRETE
from gaitlens.params import name as pname
from gaitlens.summary import Line
from gaitlens.widgets import summary_html
from gaitlens.ui import disclaimer, lang

lng = lang()


@st.cache_data(show_spinner=False)
def _tests():
    return stats.cohort_tests()


@st.cache_data(show_spinner=False)
def _resp(p):
    return stats.responders(p)


st.title(f"{t('cohort_title', lng)}")
st.caption(t("cohort_intro", lng))
disclaimer(lng)

tests = _tests()

# ---------- Key findings (auto-generated) ----------
st.subheader(t("key_findings", lng))
groups = []
for p in ["aMinSagH", "GPS_a", "GVS_aSagP"]:
    items = []
    for b in ["Verbal", "VR"]:
        r = tests[(tests.param == p) & (tests.b == b) & (tests.a == "Baseline")].iloc[0]
        improved = r.n_better >= r.n / 2
        key = "finding_line" if improved else "finding_line_worse"
        items.append(Line(t(key, lng, cond=cond_name(b, lng), param=pname(p, lng, short=True),
                            n_better=int(r.n_better), n=int(r.n), diff=r.mean_diff, unit=DISCRETE[p]["unit"],
                            p=r.p_holm), "better" if improved else "worse"))
    groups.append((pname(p, lng), items))
vv = tests[(tests.param == "aMinSagH") & (tests.pair == "VR vs Verbal")].iloc[0]
groups.append(("VR vs Verbal", [Line(pname("aMinSagH", lng, short=True)
                                     + f": Δ {vv.mean_diff:+.2f}°, p={vv.p_holm:.3g}")]))
st.html(summary_html(groups, ""))

# ---------- Per-child chart ----------
param = st.selectbox(t("cohort_param", lng), [p for p in DISCRETE_COLS if DISCRETE[p]["better"] != 0],
                     index=5, format_func=lambda p: pname(p, lng))
resp = _resp(param)
c1, c2 = st.columns([3, 1])
with c1:
    st.markdown(f"**{t('per_child_delta', lng)}**")
    st.plotly_chart(charts.responders_figure(resp, param, lng), width="stretch")
with c2:
    st.markdown(f"**{t('best_feedback', lng)}**")
    vc = resp["best"].value_counts()
    for c in ["Verbal", "VR"]:
        st.metric(cond_name(c, lng), f"{int(vc.get(c, 0))} {t('children', lng)}")

# ---------- Tests table ----------
st.subheader(t("cohort_tests", lng))
show = tests.copy()
show["param"] = show["param"].map(lambda p: pname(p, lng, short=True))
show = show[["pair", "param", "n", "mean_a", "mean_b", "mean_diff", "p_holm", "n_better"]]
show.columns = [t("col_pair", lng), t("col_param", lng), "n", t("col_mean_a", lng), t("col_mean_b", lng),
                t("col_mean_diff", lng), t("col_p", lng), t("col_n_better", lng)]
st.dataframe(show, hide_index=True, width="stretch", column_config={
    t("col_mean_a", lng): st.column_config.NumberColumn(format="%.2f"),
    t("col_mean_b", lng): st.column_config.NumberColumn(format="%.2f"),
    t("col_mean_diff", lng): st.column_config.NumberColumn(format="%+.2f"),
    t("col_p", lng): st.column_config.NumberColumn(format="%.3g"),
    t("col_n_better", lng): st.column_config.NumberColumn(format="%d"),
})
st.caption(t("click_patient", lng))
