"""Plotly графиктері / Графики Plotly."""
from __future__ import annotations

import numpy as np
import pandas as pd
import plotly.graph_objects as go
import plotly.io as pio
from plotly.subplots import make_subplots

from .data import CONDITIONS, DISCRETE_COLS, PCT, SIGNALS, curves
from .i18n import cond_name, t
from .params import DISCRETE
from .params import SIGNALS as SIG_META
from .params import name as pname
from .stats import curve_summary
from .theme import COND_COLORS, TOKENS


def _rgba(hex_color: str, a: float) -> str:
    h = hex_color.lstrip("#")
    return f"rgba({int(h[0:2], 16)},{int(h[2:4], 16)},{int(h[4:6], 16)},{a})"


COLORS = dict(COND_COLORS)
FILL = {"Baseline": _rgba(COLORS["Baseline"], 0.20), "Verbal": _rgba(COLORS["Verbal"], 0.13),
        "VR": _rgba(COLORS["VR"], 0.14)}
TOE_OFF = 60

# Shared Plotly template: recessive hairline grid, ink text, Onest (local) with system fallbacks.
pio.templates["gaitlens"] = go.layout.Template(layout=dict(
    font=dict(family="Onest, Inter, Segoe UI, sans-serif", size=12.5, color=TOKENS["ink"]),
    paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
    colorway=[COLORS["Baseline"], COLORS["Verbal"], COLORS["VR"]],
    xaxis=dict(gridcolor="#E8EDF2", linecolor=TOKENS["line"], zeroline=False, ticks="",
               tickfont=dict(color=TOKENS["muted"]), title_font=dict(color=TOKENS["muted"], size=12)),
    yaxis=dict(gridcolor="#E8EDF2", linecolor=TOKENS["line"], zeroline=False, ticks="",
               tickfont=dict(color=TOKENS["muted"]), title_font=dict(color=TOKENS["muted"], size=12)),
    hoverlabel=dict(bgcolor="#FFFFFF", bordercolor=TOKENS["line"], font=dict(color=TOKENS["ink"])),
    legend=dict(font=dict(color=TOKENS["ink"])),
))
# user-triggered motion only: switching patient smoothly morphs the curves (applied to curve charts)
TRANSITION = dict(duration=350, easing="cubic-in-out")
pio.templates.default = "gaitlens"

_LAYOUT = dict(template="gaitlens", margin=dict(l=50, r=20, t=50, b=40), hovermode="x unified",
               legend=dict(orientation="h", yanchor="bottom", y=1.04, x=0))


def curves_figure(kine_subj: pd.DataFrame, lang: str, signals: list[str] | None = None,
                  show_cycles: bool = False, height: int = 820) -> go.Figure:
    signals = [s for s in (signals or SIGNALS) if not np.isnan(curves(kine_subj, s)).all()]
    ncols = 2 if len(signals) > 1 else 1
    nrows = int(np.ceil(len(signals) / ncols))
    titles = [f"{SIG_META[s][lang]} ({SIG_META[s]['unit']})" for s in signals]
    fig = make_subplots(rows=nrows, cols=ncols, subplot_titles=titles, vertical_spacing=0.09,
                        horizontal_spacing=0.08)
    for i, sig in enumerate(signals):
        r, c = i // ncols + 1, i % ncols + 1
        cs = curve_summary(kine_subj, sig)
        for cond in CONDITIONS:
            d = cs[cond]
            if d["n"] == 0 or np.isnan(d["mean"]).all():
                continue
            name = cond_name(cond, lang)
            if show_cycles:
                arr = curves(kine_subj[kine_subj["condition"] == cond], sig)
                for row in arr:
                    fig.add_trace(go.Scatter(x=PCT, y=row, mode="lines", line=dict(color=COLORS[cond], width=0.6),
                                             opacity=0.25, hoverinfo="skip", showlegend=False,
                                             legendgroup=cond), row=r, col=c)
            fig.add_trace(go.Scatter(x=np.r_[PCT, PCT[::-1]], y=np.r_[d["mean"] + d["sd"], (d["mean"] - d["sd"])[::-1]],
                                     fill="toself", fillcolor=FILL[cond], line=dict(width=0),
                                     hoverinfo="skip", showlegend=False, legendgroup=cond), row=r, col=c)
            fig.add_trace(go.Scatter(x=PCT, y=d["mean"], mode="lines", name=f"{name} (n={d['n']})",
                                     line=dict(color=COLORS[cond], width=2.4), legendgroup=cond,
                                     showlegend=(i == 0), hovertemplate="%{y:.1f}"), row=r, col=c)
        fig.add_vline(x=TOE_OFF, line=dict(color="#AAB5C3", dash="dot", width=1), row=r, col=c)
        fig.update_xaxes(title_text=t("gait_cycle_pct", lang) if r == nrows else None, range=[0, 100],
                         row=r, col=c)
    fig.update_layout(height=int(height * nrows / 3) if nrows < 3 else height, transition=TRANSITION, **_LAYOUT)
    return fig


def discrete_figure(disc_subj: pd.DataFrame, lang: str, params: list[str] | None = None) -> go.Figure:
    params = [p for p in (params or DISCRETE_COLS) if disc_subj[p].notna().any()]
    ncols = 4
    nrows = int(np.ceil(len(params) / ncols))
    titles = [f"{pname(p, lang, short=True)} ({DISCRETE[p]['unit']})" for p in params]
    fig = make_subplots(rows=nrows, cols=ncols, subplot_titles=titles, vertical_spacing=0.18,
                        horizontal_spacing=0.06)
    for i, p in enumerate(params):
        r, c = i // ncols + 1, i % ncols + 1
        for cond in CONDITIONS:
            v = disc_subj.loc[disc_subj["condition"] == cond, p].dropna()
            if v.empty:
                continue
            fig.add_trace(go.Box(y=v, name=t(f"condshort_{cond}", lang), marker_color=COLORS[cond],
                                 boxpoints="all", jitter=0.4, pointpos=0, marker=dict(size=4, opacity=0.6),
                                 line=dict(width=1.5), showlegend=False,
                                 hovertemplate="%{y:.2f}<extra>" + cond_name(cond, lang) + "</extra>"),
                          row=r, col=c)
    fig.update_layout(height=300 * nrows, **{**_LAYOUT, "hovermode": "closest"})
    return fig


def unstable_figure(kine_subj: pd.DataFrame, anom: pd.DataFrame, cond: str, signal: str, lang: str) -> go.Figure:
    sub = kine_subj[kine_subj["condition"] == cond]
    arr = curves(sub, signal)
    cyc = sub["cycle"].to_numpy()
    bad = set(anom[(anom.condition == cond) & anom.unstable].cycle)
    fig = go.Figure()
    shown = {"ok": False, "bad": False}
    for row, cnum in zip(arr, cyc):
        is_bad = cnum in bad
        key = "bad" if is_bad else "ok"
        fig.add_trace(go.Scatter(
            x=PCT, y=row, mode="lines",
            line=dict(color=TOKENS["worse"] if is_bad else COLORS[cond], width=2.2 if is_bad else 0.8,
                      dash="dash" if is_bad else "solid"),
            opacity=1 if is_bad else 0.35,
            name=t("unstable_cycles" if is_bad else "typical_cycles", lang),
            legendgroup=key, showlegend=not shown[key],
            hovertemplate=f"#{cnum}: " + "%{y:.1f}<extra></extra>"))
        shown[key] = True
    fig.add_vline(x=TOE_OFF, line=dict(color="#AAB5C3", dash="dot", width=1))
    fig.update_layout(height=420, title=f"{SIG_META[signal][lang]} — {cond_name(cond, lang)}",
                      xaxis_title=t("gait_cycle_pct", lang), yaxis_title=SIG_META[signal]["unit"],
                      **{**_LAYOUT, "hovermode": "closest",
                         "legend": dict(orientation="h", yanchor="top", y=-0.22, x=0)})
    return fig


def variability_figure(var: pd.DataFrame, lang: str) -> go.Figure:
    fig = go.Figure(go.Bar(
        x=[t(f"condshort_{c}", lang) for c in var.condition], y=var.mean_sd,
        marker_color=[COLORS[c] for c in var.condition], text=[f"{v:.1f}°" for v in var.mean_sd],
        textposition="outside"))
    fig.update_layout(height=280, yaxis_title="SD, °", **{**_LAYOUT, "hovermode": "closest",
                                                          "margin": dict(l=50, r=20, t=20, b=30)})
    return fig


def responders_figure(resp: pd.DataFrame, param: str, lang: str) -> go.Figure:
    better = DISCRETE[param]["better"]
    d = resp.copy()
    d["label"] = d["subject"].str.replace("s61520_", "#", regex=False)
    d = d.sort_values("d_VR")
    fig = go.Figure()
    for cond, col in [("Verbal", "d_Verbal"), ("VR", "d_VR")]:
        fig.add_trace(go.Bar(x=d["label"], y=d[col], name=cond_name(cond, lang), marker_color=COLORS[cond],
                             marker_cornerradius=3, hovertemplate="%{x}: %{y:+.2f}<extra>" + cond + "</extra>"))
    fig.add_hline(y=0, line=dict(color=TOKENS["ink"], width=1))
    note = {-1: "↓", 1: "↑", 0: ""}[better]
    fig.update_xaxes(type="category", categoryorder="array", categoryarray=list(d["label"]))
    fig.update_layout(barmode="group", height=420, bargap=0.25, bargroupgap=0.08,
                      yaxis_title=f"Δ {pname(param, lang, short=True)} ({DISCRETE[param]['unit']}) {note}",
                      **{**_LAYOUT, "hovermode": "closest"})
    return fig


def confusion_figure(cm: list[list[int]], labels: list[str], lang: str) -> go.Figure:
    cm = np.array(cm)
    pct = cm / cm.sum(axis=1, keepdims=True)
    text = [[f"{cm[i, j]}<br>{pct[i, j]:.0%}" for j in range(len(labels))] for i in range(len(labels))]
    fig = go.Figure(go.Heatmap(z=pct, x=labels, y=labels, text=text, texttemplate="%{text}",
                               colorscale=[[0, TOKENS["surface"]], [1, "#7E93E6"]], zmin=0, zmax=1, showscale=False,
                               textfont=dict(color=TOKENS["ink"], size=13), xgap=2, ygap=2))
    fig.update_layout(height=340, xaxis_title=t("pred_label", lang), yaxis_title=t("true_label", lang),
                      yaxis_autorange="reversed", **{**_LAYOUT, "hovermode": "closest"})
    return fig


def importance_figure(imp: list[dict], lang: str) -> go.Figure:
    d = pd.DataFrame(imp)[::-1]
    fig = go.Figure(go.Bar(x=d["importance"], y=d["feature"], orientation="h", marker_color=TOKENS["ink"],
                           marker_cornerradius=3, width=0.55))
    fig.update_layout(height=max(300, 26 * len(d)), xaxis_title="Δ balanced accuracy",
                      **{**_LAYOUT, "hovermode": "closest"})
    return fig


def model_bars_figure(metrics: dict, lang: str) -> go.Figure:
    """Small multiples (one per task); models in ink, the chance level (Dummy) in reference gray."""
    names = {"dummy": t("model_dummy", lang), "logreg": t("model_logreg", lang), "rf": t("model_rf", lang)}
    tasks = [("3class", t("task_3class", lang)), ("binary", t("task_binary", lang))]
    fig = make_subplots(rows=1, cols=2, subplot_titles=[ttl for _, ttl in tasks], shared_yaxes=True,
                        horizontal_spacing=0.06)
    for i, (key, _) in enumerate(tasks, start=1):
        res = metrics[key]["results"]
        models = list(res)
        fig.add_trace(go.Bar(
            x=[names[m].replace(" (", "<br>(").replace(" ", "<br>", 1) if "(" not in names[m] else
               names[m].replace(" (", "<br>(") for m in models], y=[res[m]["balanced_accuracy"] for m in models],
            marker_color=[COLORS["Baseline"] if m == "dummy" else TOKENS["ink"] for m in models],
            marker_cornerradius=4, width=0.5,
            error_y=dict(type="data", array=[res[m]["per_subject_bacc_sd"] for m in models], thickness=1,
                         color=TOKENS["muted"]),
            text=[f"{res[m]['balanced_accuracy']:.0%}" for m in models], textposition="inside",
            insidetextanchor="start", textfont=dict(color="#FFFFFF", size=14), showlegend=False,
            hovertemplate="%{x}: %{y:.1%}<extra></extra>"), row=1, col=i)
    fig.update_yaxes(range=[0, 1.12], tickformat=".0%")
    fig.update_xaxes(tickangle=0)
    fig.update_yaxes(title_text="Balanced accuracy", row=1, col=1)
    fig.update_layout(height=380, **{**_LAYOUT, "hovermode": "closest"})
    return fig
