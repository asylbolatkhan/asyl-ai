"""ЖИ модель және сапа / ИИ-модель и качество."""
import pandas as pd
import streamlit as st

from gaitlens import charts, model
from gaitlens.i18n import t
from gaitlens.ui import disclaimer, lang

lng = lang()

st.title(f"{t('model_title', lng)}")
st.write(t("model_intro", lng))
st.info(t("model_split", lng))
st.caption(t("model_norm", lng))

metrics = model.load_metrics()
if not metrics:
    st.warning(t("metrics_missing", lng))
    st.stop()

st.plotly_chart(charts.model_bars_figure(metrics, lng), width="stretch")
st.success(t("model_honest", lng))

names = {"dummy": t("model_dummy", lng), "logreg": t("model_logreg", lng), "rf": t("model_rf", lng)}
rows = []
for key, task_label in [("3class", "task_3class"), ("binary", "task_binary"),
                        ("3class_raw", "task_3class"), ("binary_raw", "task_binary")]:
    m = metrics[key]
    norm = t("normalized" if m["normalized"] else "raw", lng)
    for name, r in m["results"].items():
        rows.append({
            t("col_task", lng): t(task_label, lng), t("col_features", lng): norm,
            t("col_model", lng): names[name],
            t("col_acc", lng): r["accuracy"], t("col_bacc", lng): r["balanced_accuracy"],
            t("col_f1", lng): r["macro_f1"],
            t("col_per_subj", lng): f"{r['per_subject_bacc_mean']:.2f} ± {r['per_subject_bacc_sd']:.2f}",
        })
fmt = st.column_config.NumberColumn(format="%.3f")
st.dataframe(pd.DataFrame(rows), hide_index=True, width="stretch",
             column_config={t("col_acc", lng): fmt, t("col_bacc", lng): fmt, t("col_f1", lng): fmt})
st.caption(f"{metrics['3class']['n_cycles']} cycles · {metrics['3class']['n_subjects']} subjects · "
           f"CV: {metrics['3class']['cv']}")

c1, c2 = st.columns(2)
with c1:
    task = st.radio(t("col_task", lng), ["3class", "binary"], horizontal=True,
                    format_func=lambda k: t(f"task_{k}", lng), label_visibility="collapsed")
    st.markdown(f"**{t('confusion', lng)}**")
    m = metrics[task]
    st.plotly_chart(charts.confusion_figure(m["results"]["logreg"]["confusion"], m["labels"], lng),
                    width="stretch")
with c2:
    st.markdown(f"**{t('importance', lng)}**")
    st.plotly_chart(charts.importance_figure(metrics[f"importance_{task}"], lng), width="stretch")
    st.caption(t("feat_help", lng))
disclaimer(lng)
