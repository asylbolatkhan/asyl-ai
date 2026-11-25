"""Дәрігерге мәтіндік қорытынды / Текстовая сводка для врача.

Әдепкі — шаблон (офлайн, тек есептелген сандар). Опция — Claude API арқылы мәтінді жетілдіру:
модельге тек есептелген фактілер беріледі, сандарды өзгертпеу талап етіледі.
"""
from __future__ import annotations

import json
import os
import re

import numpy as np
import pandas as pd

from .i18n import cond_name, t
from .params import DISCRETE, GPS_MCID, ICF
from .params import name as pname

LLM_MODEL = "claude-opus-5-5"

W = {  # phrase fragments
    "kk": {
        "overview": "Жалпы сурет",
        "target": "Басты мақсат — ұршықтың созылуы",
        "other": "Басқа маңызды өзгерістер",
        "stability": "Қадамдардың тұрақтылығы",
        "compare": "Қай кері байланыс тиімдірек",
        "icf": "МКФ бойынша анықтамалық байланыс",
        "limits": "Шектеулер",
        "intro": "Пациент {subj} ({side}). Қалыпты жүрісте GPS = {gps:.1f}° ({n} цикл).",
        "gps_line": "{cond}: GPS {val:.1f}° (Δ {d:+.1f}°, {dirw}; {clin}).",
        "gps_better": "жақсарды", "gps_worse": "нашарлады",
        "clin_yes": "клиникалық маңызды шекарадан ({mcid}°) асады",
        "clin_no": "клиникалық маңызды шекарадан ({mcid}°) аз",
        "hip_better": "{cond}: ұршық {abs:.1f}°-қа толығырақ түзелді (ең аз бұрыш {b:.1f}° → {c:.1f}°; әсер {mag}).",
        "hip_worse": "{cond}: ұршықтың созылуы {abs:.1f}°-қа азайды ({b:.1f}° → {c:.1f}°; әсер {mag}).",
        "hip_peak": "Орташа қисық бойынша ұршықтың ең көп созылуы (цикл кезеңі және бұрышы): {parts}.",
        "hip_peak_part": "{cond} — {pct}%-да {val:.1f}°",
        "change_line": "{cond}: {param} — {b:.1f} → {c:.1f}{unit} (Δ {d:+.1f}, әсер {mag}, {dirw}).",
        "dir_better": "жақсарды", "dir_worse": "нашарлады", "dir_neutral": "бейтарап",
        "no_other": "Басқа параметрлерде статистикалық маңызды әрі айқын өзгеріс табылмады.",
        "unstable_line": "Тұрақсыз қадамдар: {parts}.",
        "unstable_part": "{cond} — {k}/{n}",
        "var_line": "Жүріс вариабельділігі (бұрыштардың орташа SD): {parts}. {verdict}",
        "var_more": "Кері байланыс кезінде қадамдар әртүрлірек — бала жаңа жүріс тәсілін іздеп жатқан болуы мүмкін.",
        "var_less": "Кері байланыс кезінде қадамдар біркелкірек.",
        "var_same": "Вариабельділік жағдайлар арасында ұқсас.",
        "cmp_hip": "Ұршықтың созылуы бойынша бұл пациентке {best} тиімдірек (Cliff's δ: Verbal {dv:+.2f}, VR {dr:+.2f}).",
        "cmp_none": "Ұршықтың созылуы бойынша екі кері байланыстың да әсері шамалы.",
        "cmp_hip_worse": "Бұл пациентте екі кері байланыс та ұршықтың созылуын жақсартпады (Cliff's δ: Verbal {dv:+.2f}, VR {dr:+.2f}) — нұсқаулықты немесе кері байланыс түрін қайта қарау қажет болуы мүмкін.",
        "cmp_gps": "Бірақ жалпы жүріс профилі (GPS) {cond} кезінде нашарлады — басқа буындардағы компенсацияға назар аудару ұсынылады.",
        "icf_b770": "{code}: {params}.",
        "icf_d450": "{code}: жалпы жүріс сапасы (GPS) және қадамдардың тұрақтылығы.",
        "limit_1": "Бір сессиядағы жедел әсер (тренажерде) — ұзақ мерзімді нәтижені көрсетпейді.",
        "limit_2": "Бір баланың циклдері өзара тәуелді, p-мәндер шамамен алынған.",
        "disclaimer": "Бұл диагноз немесе емдеу ұсынысы емес; шешімді дәрігер қабылдайды.",
    },
    "ru": {
        "overview": "Общая картина",
        "target": "Главная цель — разгибание бедра",
        "other": "Другие значимые изменения",
        "stability": "Стабильность шагов",
        "compare": "Какая обратная связь эффективнее",
        "icf": "Справочная связь с МКФ",
        "limits": "Ограничения",
        "intro": "Пациент {subj} ({side}). При обычной ходьбе GPS = {gps:.1f}° ({n} циклов).",
        "gps_line": "{cond}: GPS {val:.1f}° (Δ {d:+.1f}°, {dirw}; {clin}).",
        "gps_better": "улучшение", "gps_worse": "ухудшение",
        "clin_yes": "превышает порог клинической значимости ({mcid}°)",
        "clin_no": "ниже порога клинической значимости ({mcid}°)",
        "hip_better": "{cond}: бедро разгибается полнее на {abs:.1f}° (минимальный угол {b:.1f}° → {c:.1f}°; эффект {mag}).",
        "hip_worse": "{cond}: разгибание бедра уменьшилось на {abs:.1f}° ({b:.1f}° → {c:.1f}°; эффект {mag}).",
        "hip_peak": "Максимальное разгибание бедра по средней кривой (момент цикла и угол): {parts}.",
        "hip_peak_part": "{cond} — {val:.1f}° на {pct}%",
        "change_line": "{cond}: {param} — {b:.1f} → {c:.1f}{unit} (Δ {d:+.1f}, эффект {mag}, {dirw}).",
        "dir_better": "улучшение", "dir_worse": "ухудшение", "dir_neutral": "нейтрально",
        "no_other": "В других параметрах статистически значимых и выраженных изменений не найдено.",
        "unstable_line": "Нестабильные шаги: {parts}.",
        "unstable_part": "{cond} — {k}/{n}",
        "var_line": "Вариабельность походки (среднее SD углов): {parts}. {verdict}",
        "var_more": "При обратной связи шаги разнообразнее — ребёнок, возможно, ищет новый способ ходьбы.",
        "var_less": "При обратной связи шаги более однородны.",
        "var_same": "Вариабельность сходна во всех условиях.",
        "cmp_hip": "По разгибанию бедра этому пациенту больше подходит {best} (Cliff's δ: Verbal {dv:+.2f}, VR {dr:+.2f}).",
        "cmp_none": "По разгибанию бедра эффект обоих видов обратной связи мал.",
        "cmp_hip_worse": "У этого пациента ни один вид обратной связи не улучшил разгибание бедра (Cliff's δ: Verbal {dv:+.2f}, VR {dr:+.2f}) — возможно, стоит пересмотреть инструкцию или вид обратной связи.",
        "cmp_gps": "Однако общий профиль походки (GPS) ухудшился при {cond} — рекомендуется обратить внимание на компенсацию в других суставах.",
        "icf_b770": "{code}: {params}.",
        "icf_d450": "{code}: общее качество походки (GPS) и стабильность шагов.",
        "limit_1": "Немедленный эффект в одной сессии (на дорожке) — не отражает долгосрочный результат.",
        "limit_2": "Циклы одного ребёнка взаимозависимы, p-значения приблизительны.",
        "disclaimer": "Это не диагноз и не назначение лечения; решение принимает врач.",
    },
}


class Line(str):
    """A summary line that also remembers whether it reports an improvement ('better'/'worse'/None)."""

    kind: str | None

    def __new__(cls, text: str, kind: str | None = None):
        obj = super().__new__(cls, text)
        obj.kind = kind
        return obj


def _kind(direction: str, magnitude: str = "large") -> str | None:
    if magnitude == "negligible" or direction not in ("better", "worse"):
        return None
    return direction


def _lower(s: str) -> str:
    return s[:1].lower() + s[1:] if s and not s.startswith("VR") else s


def _row(cmp: pd.DataFrame, cond: str, param: str) -> pd.Series | None:
    if not len(cmp):
        return None
    r = cmp[(cmp.condition == cond) & (cmp.param == param)]
    return r.iloc[0] if len(r) else None


def build_facts(subject: str, info: dict, counts: dict, cmp: pd.DataFrame,
                hip_curve: dict, anomalies: pd.DataFrame, variability: pd.DataFrame) -> dict:
    """Machine-readable facts (also passed to the LLM)."""
    facts = {"subject": subject, "side": info["side"], "cycles": counts, "changes": [],
             "hip_curve": hip_curve, "unstable": {}, "variability": {}}
    for _, r in cmp[~cmp.all_missing].iterrows():
        facts["changes"].append({k: (None if isinstance(r[k], float) and not np.isfinite(r[k]) else
                                     (round(float(r[k]), 3) if isinstance(r[k], (float, np.floating)) else
                                      (bool(r[k]) if isinstance(r[k], (bool, np.bool_)) else r[k])))
                                 for k in ["condition", "param", "mean_base", "mean_cond", "delta",
                                           "cliffs", "magnitude", "p_holm", "significant", "direction",
                                           "n_base", "n_cond"]})
    for c in ["Baseline", "Verbal", "VR"]:
        a = anomalies[anomalies.condition == c] if len(anomalies) else anomalies
        facts["unstable"][c] = {"unstable": int(a.unstable.sum()) if len(a) else 0, "total": int(len(a))}
        v = variability[variability.condition == c]
        facts["variability"][c] = round(float(v.mean_sd.iloc[0]), 2) if len(v) else None
    return facts


def template_summary(facts: dict, lang: str) -> list[tuple[str, list[str]]]:
    w = W[lang]
    cmp = pd.DataFrame(facts["changes"])
    sections: list[tuple[str, list[str]]] = []
    side = t(f"side_{facts['side']}", lang)

    # 1. Overview (GPS)
    lines = []
    g_v = _row(cmp, "Verbal", "GPS_a")
    gps_b = g_v["mean_base"] if g_v is not None else np.nan
    lines.append(w["intro"].format(subj=facts["subject"], side=side, gps=gps_b, n=facts["cycles"]["Baseline"]))
    gps_worse_conds = []
    for c in ["Verbal", "VR"]:
        r = _row(cmp, c, "GPS_a")
        if r is None:
            continue
        clin = (w["clin_yes"] if abs(r["delta"]) >= GPS_MCID else w["clin_no"]).format(mcid=GPS_MCID)
        dirw = w["gps_better"] if r["delta"] < 0 else w["gps_worse"]
        if r["delta"] > 0 and r["magnitude"] in ("medium", "large"):
            gps_worse_conds.append(c)
        lines.append(Line(w["gps_line"].format(cond=cond_name(c, lang), val=r["mean_cond"], d=r["delta"],
                                               dirw=dirw, clin=clin),
                          _kind("better" if r["delta"] < 0 else "worse", r["magnitude"])))
    sections.append((w["overview"], lines))

    # 2. Hip extension
    lines = []
    hip_delta = {}
    for c in ["Verbal", "VR"]:
        r = _row(cmp, c, "aMinSagH")
        if r is None:
            continue
        hip_delta[c] = -r["cliffs"]  # positive = more extension (better)
        key = "hip_better" if r["delta"] < 0 else "hip_worse"
        lines.append(Line(w[key].format(cond=cond_name(c, lang), abs=abs(r["delta"]), b=r["mean_base"],
                                        c=r["mean_cond"], mag=t(f"mag_{r['magnitude']}", lang)),
                          _kind("better" if r["delta"] < 0 else "worse", r["magnitude"])))
    hc = facts.get("hip_curve") or {}
    if hc:
        parts = [w["hip_peak_part"].format(cond=t(f"condshort_{c}", lang), pct=v["pct"], val=v["value"])
                 for c, v in hc.items()]
        lines.append(w["hip_peak"].format(parts="; ".join(parts)))
    sections.append((w["target"], lines))

    # 3. Other significant changes
    lines = []
    if len(cmp):
        oth = cmp[(~cmp.param.isin(["GPS_a", "aMinSagH"])) & (cmp.significant.fillna(False).astype(bool))
                  & (cmp.magnitude.isin(["medium", "large"]))].copy()
        oth["abs"] = oth["cliffs"].abs()
        for _, r in oth.sort_values("abs", ascending=False).head(4).iterrows():
            lines.append(Line(w["change_line"].format(
                cond=cond_name(r["condition"], lang), param=pname(r["param"], lang), b=r["mean_base"],
                c=r["mean_cond"], unit=DISCRETE[r["param"]]["unit"].replace("% GC", "%"),
                d=r["delta"], mag=t(f"mag_{r['magnitude']}", lang), dirw=w[f"dir_{r['direction']}"]),
                _kind(r["direction"], r["magnitude"])))
    if not lines:
        lines.append(w["no_other"])
    sections.append((w["other"], lines))

    # 4. Stability
    lines = []
    parts = [w["unstable_part"].format(cond=t(f"condshort_{c}", lang), k=v["unstable"], n=v["total"])
             for c, v in facts["unstable"].items()]
    lines.append(w["unstable_line"].format(parts=", ".join(parts)))
    var = facts["variability"]
    if all(var.get(c) is not None for c in ["Baseline", "Verbal", "VR"]):
        vparts = ", ".join(f"{t(f'condshort_{c}', lang)} {var[c]:.1f}°" for c in ["Baseline", "Verbal", "VR"])
        fb = np.mean([var["Verbal"], var["VR"]])
        ratio = fb / var["Baseline"] if var["Baseline"] else 1
        verdict = w["var_more"] if ratio > 1.15 else (w["var_less"] if ratio < 0.87 else w["var_same"])
        lines.append(w["var_line"].format(parts=vparts, verdict=verdict))
    sections.append((w["stability"], lines))

    # 5. Which feedback
    lines = []
    if hip_delta:
        best = max(hip_delta, key=hip_delta.get)
        fmt = dict(dv=hip_delta.get("Verbal", 0), dr=hip_delta.get("VR", 0))
        if hip_delta[best] >= 0.147:
            lines.append(Line(w["cmp_hip"].format(best=_lower(cond_name(best, lang)), **fmt), "better"))
        elif all(v <= -0.147 for v in hip_delta.values()):
            lines.append(Line(w["cmp_hip_worse"].format(**fmt), "worse"))
        else:
            lines.append(w["cmp_none"])
    if gps_worse_conds:
        lines.append(Line(w["cmp_gps"].format(cond=", ".join(_lower(cond_name(c, lang)) for c in gps_worse_conds)),
                          "worse"))
    sections.append((w["compare"], lines))

    # 6. ICF
    changed_kin = []
    if len(cmp):
        sig = cmp[(cmp.significant.fillna(False).astype(bool)) & (cmp.param != "GPS_a")
                  & (cmp.magnitude != "negligible")]
        changed_kin = sorted({pname(p, lang, short=True) for p in sig.param})
    b770_params = ", ".join(changed_kin) if changed_kin else "—"
    sections.append((w["icf"], [
        w["icf_b770"].format(code=ICF["b770"][lang], params=b770_params),
        w["icf_d450"].format(code=ICF["d450"][lang]),
    ]))

    # 7. Limits
    sections.append((w["limits"], [w["limit_1"], w["limit_2"], Line("**" + w["disclaimer"] + "**", "note")]))
    return sections


def to_markdown(sections: list[tuple[str, list[str]]]) -> str:
    out = []
    for title, lines in sections:
        out.append(f"**{title}**")
        out.extend(f"- {ln}" for ln in lines)
        out.append("")
    return "\n".join(out)


OPENAI_MODEL = "gpt-5.4"
_NUM = re.compile(r"[-+−]?\d+(?:[.,]\d+)?")


def _numbers(text: str) -> set[str]:
    return {n.replace(",", ".").replace("−", "-").lstrip("+") for n in _NUM.findall(text)}


def numbers_grounded(output: str, *sources: str) -> tuple[bool, set[str]]:
    """Every number in the LLM output must already exist in the computed draft/facts."""
    allowed = set().union(*(_numbers(s) for s in sources))
    allowed |= {a.lstrip("-") for a in allowed} | {str(i) for i in range(0, 11)}
    extra = {n for n in _numbers(output) if n not in allowed and n.lstrip("-") not in allowed}
    return (not extra, extra)


CODE_TOKENS = re.compile(r"GPS_a|GVS_|aMinSagH|pctmZero|aSag|mSag|cliffs|p_holm|mean_base|mean_cond|\bdelta\b|magnitude")


def _llm_messages(facts: dict, template_md: str, lang: str) -> tuple[str, str]:
    language = "казахском (қазақ тілі)" if lang == "kk" else "русском"
    system = (
        "Ты — ассистент врача-реабилитолога по анализу походки детей с ДЦП. "
        "Ты НЕ ставишь диагноз и НЕ назначаешь лечение. "
        f"Перепиши черновик на {language} языке так, чтобы врачу было легко читать: короткие ясные предложения, "
        "до 180 слов, markdown: жирные только заголовки разделов, пункты списком. "
        "Строгие правила: используй ТОЛЬКО числа, которые есть в черновике, в том же виде (не добавляй новых, "
        "не пересчитывай, не меняй точность); называй показатели по-человечески, как в черновике, "
        "никогда не пиши технические коды переменных; сохрани разделы, связь с МКФ и финальное предупреждение."
    )
    user = "Черновик сводки:\n" + template_md
    return system, user


def openai_summary(facts: dict, template_md: str, lang: str, client=None, model: str = OPENAI_MODEL) -> str:
    """Rewrite the template with OpenAI. Raises if the call fails, invents numbers or leaks variable codes."""
    from openai import OpenAI

    system, user = _llm_messages(facts, template_md, lang)
    client = client or OpenAI(timeout=180, max_retries=3)
    resp = client.responses.create(model=model, instructions=system, input=user)
    text = (resp.output_text or "").strip()
    if not text:
        raise RuntimeError("empty response")
    ok, extra = numbers_grounded(text, template_md)
    if not ok:
        raise ValueError(f"ungrounded numbers: {sorted(extra)[:5]}")
    if CODE_TOKENS.search(text):
        raise ValueError(f"technical codes in text: {CODE_TOKENS.search(text).group(0)}")
    return text


def llm_available() -> bool:
    try:
        import anthropic  # noqa: F401
    except ImportError:
        return False
    return bool(os.environ.get("ANTHROPIC_API_KEY") or os.environ.get("ANTHROPIC_AUTH_TOKEN"))


def llm_summary(facts: dict, template_md: str, lang: str, client=None) -> str:
    """Rewrite the template summary with Claude. Raises on failure (caller falls back)."""
    import anthropic

    language = "казахском (қазақ тілі)" if lang == "kk" else "русском"
    system = (
        "Ты — ассистент врача-реабилитолога по анализу походки детей с ДЦП. "
        "Ты НЕ ставишь диагноз и НЕ назначаешь лечение. Используй только числа из переданных фактов, "
        "ничего не придумывай и не округляй иначе, чем в черновике. "
        f"Пиши на {language} языке, кратко (до 220 слов), структурно, в markdown с заголовками-жирным "
        "и маркированными пунктами. Сохрани разделы черновика и финальное предупреждение."
    )
    user = (
        "Факты (JSON):\n" + json.dumps(facts, ensure_ascii=False, default=str) +
        "\n\nЧерновик сводки:\n" + template_md +
        "\n\nСделай текст понятнее для врача, сохранив все числа."
    )
    client = client or anthropic.Anthropic()
    resp = client.beta.messages.create(
        model=LLM_MODEL,
        max_tokens=4000,
        betas=["server-side-fallback-2026-07-01"],
        fallbacks="default",
        output_config={"effort": "low"},
        system=system,
        messages=[{"role": "user", "content": user}],
    )
    if resp.stop_reason == "refusal":
        raise RuntimeError("refusal")
    text = "".join(b.text for b in resp.content if b.type == "text").strip()
    if not text:
        raise RuntimeError("empty response")
    return text
