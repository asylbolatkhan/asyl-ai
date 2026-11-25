"""Пациент картасы / Карточка пациента."""
import hashlib
import json

import numpy as np
import streamlit as st

import streamlit.components.v1 as components

from gaitlens import charts, data, gait_anim, model, summary, widgets
from gaitlens.data import CONDITIONS
from gaitlens.i18n import cond_name, t
from gaitlens.params import SIGNALS as SIG_META
from gaitlens.theme import TOKENS
from gaitlens.ui import analyze, changes_table, gait_component, lang, llm_text, report_html, subject_label

lng = lang()

# ---------- Sidebar ----------
subs = data.subjects()
default = st.session_state.get("subject", subs[0])
subject = st.sidebar.selectbox(t("select_patient", lng), subs, index=subs.index(default),
                               format_func=lambda s: subject_label(s, lng))
st.session_state["subject"] = subject
st.sidebar.markdown(f"**{t('options', lng)}**")
exclude = st.sidebar.checkbox(t("exclude_unstable", lng), value=False)
show_cycles = st.sidebar.checkbox(t("show_cycles", lng), value=False)
use_llm = False
if summary.llm_available():
    use_llm = st.sidebar.checkbox(t("use_llm", lng), value=False)

A = analyze(subject, exclude)
info = data.subject_info(subject)
cmp = A["cmp"]

# ---------- Header: patient + gait animation ----------
left, right = st.columns([1.25, 1], gap="large")
with left:
    st.html(widgets.hero_html(subject, info, lng))
    st.html(widgets.gps_html(A, lng))
    st.html(f'<p class="gl-note">{t("disclaimer", lng)}</p>')
with right:
    components.html(gait_component(subject, lng, gait_anim.COMPONENT.stat().st_mtime), height=590)

# ---------- AI summary ----------
sections = summary.template_summary(A["facts"], lng)
summary_md = summary.to_markdown(sections)
source_note = t("ai_summary_source_template", lng)
llm_md = None
if use_llm:
    key = hashlib.sha1(json.dumps(A["facts"], sort_keys=True, default=str).encode()).hexdigest()
    try:
        with st.spinner("Claude…"):
            llm_md = llm_text(key, A["facts"], summary_md, lng)
        summary_md = llm_md
        source_note = t("ai_summary_source_llm", lng, model=summary.LLM_MODEL)
    except Exception as e:  # noqa: BLE001 — any API failure falls back to the template
        st.warning(t("llm_failed", lng, err=type(e).__name__))

metrics = model.load_metrics()
if metrics:
    acc = metrics["binary"]["results"]["logreg"].get("per_subject", {}).get(subject)
    if acc is not None:
        source_note += " " + t("model_separability", lng, acc=acc)

st.subheader(t("ai_summary", lng))
if llm_md:
    st.markdown(llm_md)
    st.caption(source_note)
else:
    st.html(widgets.summary_html(sections, source_note))

# ---------- Tabs ----------
tab_c, tab_p, tab_t, tab_u = st.tabs([t("tab_curves", lng), t("tab_params", lng),
                                      t("tab_table", lng), t("tab_unstable", lng)])
with tab_c:
    st.caption(t("curves_help", lng))
    fig_curves = charts.curves_figure(A["kine"], lng, show_cycles=show_cycles)
    st.plotly_chart(fig_curves, width="stretch")

with tab_p:
    st.caption(t("params_help", lng))
    fig_disc = charts.discrete_figure(A["disc"], lng)
    st.plotly_chart(fig_disc, width="stretch")

with tab_t:
    st.caption(t("table_help", lng))
    tbl = changes_table(cmp, lng)
    assess_col = t("col_assess", lng)
    tone = {t("assess_better", lng): f"color:{TOKENS['better_text']};font-weight:600",
            t("assess_worse", lng): f"color:{TOKENS['worse_text']};font-weight:600"}
    styled = tbl.style.map(lambda v: tone.get(v, f"color:{TOKENS['muted']}"), subset=[assess_col])
    st.dataframe(
        styled, hide_index=True, width="stretch", height=36 * (len(tbl) + 1) + 3,
        column_config={
            t("col_delta", lng): st.column_config.NumberColumn(format="%+.2f"),
            t("col_delta_pct", lng): st.column_config.NumberColumn(format="%+.1f%%"),
            t("col_p", lng): st.column_config.NumberColumn(format="%.3g"),
        })

with tab_u:
    st.caption(t("unstable_help", lng))
    anom = A["anom"]
    bad = anom[anom.unstable]
    c1, c2 = st.columns([2, 1])
    with c1:
        ucond = st.radio(t("condition", lng), CONDITIONS, horizontal=True,
                         format_func=lambda c: cond_name(c, lng), key="ucond")
        full_kine = data.subject_kine(subject)
        sig_opts = [s for s in SIG_META if not np.isnan(data.curves(full_kine, s)).all()]
        usig = st.selectbox(t("signal", lng), sig_opts, format_func=lambda s: SIG_META[s][lng],
                            index=1, key="usig")
        st.plotly_chart(charts.unstable_figure(full_kine, anom, ucond, usig, lng), width="stretch")
    with c2:
        st.markdown(f"**{t('variability', lng)}**")
        st.plotly_chart(charts.variability_figure(A["var"], lng), width="stretch")
        st.caption(t("variability_help", lng))
        if bad.empty:
            st.success(t("unstable_none", lng))
        else:
            show = bad[["condition", "cycle", "robust_z"]].copy()
            show["condition"] = show["condition"].map(lambda c: cond_name(c, lng))
            show.columns = [t("condition", lng), "#", "z"]
            st.dataframe(show, hide_index=True, width="stretch",
                         column_config={"z": st.column_config.NumberColumn(format="%.1f")})

# ---------- Report ----------
st.download_button(t("download_report", lng), data=report_html(subject, lng, exclude, summary_md),
                   file_name=f"GaitLens_{subject}_{lng}.html", mime="text/html", type="primary")
