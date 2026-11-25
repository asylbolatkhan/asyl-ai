"""Streamlit көмекші функциялары / Вспомогательные функции Streamlit."""
from __future__ import annotations

from pathlib import Path

import streamlit as st

from . import analysis, report, summary
from .analysis import changes_table, subject_label  # noqa: F401 — re-exported for views
from .i18n import LANGS, t


def lang() -> str:
    return st.session_state.get("lang", "kk")


def language_selector() -> str:
    """Sidebar selector; value is kept in a non-widget key so it survives page switches."""
    current = st.session_state.get("lang", "kk")

    def _on_change():
        v = st.session_state.get("_lang_widget")
        if v:  # segmented control can be deselected → keep the current language
            st.session_state["lang"] = v

    st.sidebar.segmented_control(t("language", current), list(LANGS), format_func=LANGS.get,
                                 default=current, key="_lang_widget", on_change=_on_change,
                                 label_visibility="collapsed")
    return st.session_state.get("lang", current)


@st.cache_data(show_spinner=False)
def analyze(subject: str, exclude_unstable: bool) -> dict:
    return analysis.analyze_subject(subject, exclude_unstable)


@st.cache_data(show_spinner=False)
def report_html(subject: str, lng: str, exclude_unstable: bool, summary_md: str) -> bytes:
    return report.patient_report(subject, lng, exclude_unstable, summary_md).encode("utf-8")


@st.cache_data(show_spinner=False)
def gait_component(subject: str, lng: str, template_version: float = 0.0) -> str:
    """template_version (file mtime) is only part of the cache key."""
    from . import data, gait_anim
    from .theme import COND_COLORS

    labels = {
        "title": t("gait_title", lng), "play": t("gait_play", lng), "pause": t("gait_pause", lng),
        "scrub": t("gait_scrub", lng), "aria": t("gait_aria", lng), "hip": t("gait_hip", lng),
        "pelvis": t("gait_pelvis", lng), "caption": t("gait_caption", lng), "toeOff": t("toe_off", lng),
        "conds": {c: t(f"condshort_{c}", lng) for c in data.CONDITIONS},
        "phases": {p: t(f"phase_{p}", lng) for p in
                   ("loading", "midstance", "terminal_stance", "preswing", "swing", "terminal_swing")},
    }
    info = data.subject_info(subject)
    return gait_anim.component_html(data.subject_kine(subject), float(info["LegLength"]), labels, COND_COLORS)


@st.cache_data(show_spinner=False)
def llm_text(facts_key: str, _facts: dict, template_md: str, lng: str) -> str:
    """Cached by facts_key (hash of facts) + template + language."""
    return summary.llm_summary(_facts, template_md, lng)


STATIC = Path(__file__).resolve().parent.parent / "static"


def sidebar_brand(lng: str) -> None:
    st.logo(str(STATIC / "logo.svg"), size="large", icon_image=str(STATIC / "mark.svg"))
    st.sidebar.caption(t("app_tagline", lng))


def disclaimer(lng: str) -> None:
    st.caption(t("disclaimer", lng))
