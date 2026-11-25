"""Деректер, әдістеме, этика / Данные, методика, этика."""
import streamlit as st

from gaitlens import data
from gaitlens.i18n import t
from gaitlens.ui import disclaimer, lang

lng = lang()

TEXT = {
    "kk": {
        "methods": """
- **Деректерді оқу.** CSV: бөлгіш `;`, ондық бөлгіш `,`, бос мәндер `NaN`. 29 пациент, әрқайсысында бір жақ, бір жағдайда ~30 цикл.
- **Өзгерістер.** Әр параметр бойынша Verbal/VR мен Baseline салыстырылады: орташа ± SD, Δ, Δ%, Mann-Whitney U (Holm түзетуі), Cliff's delta (елеусіз < 0.147 ≤ шамалы < 0.33 ≤ орташа < 0.474 ≤ айқын). GPS үшін клиникалық маңызды шекара — 1.6° (Baker et al., 2012).
- **Қисықтар.** 5 сигнал × 51 нүкте (цикл 0–100%). Орташа ± SD; Baseline-нан ең үлкен айырма аралығы автоматты түрде табылады.
- **Тұрақсыз қадамдар (ЖИ).** Цикл қисықтары → баланың медианалық қадамынан RMS қашықтық → робаст z-score; IsolationForest қосымша тексереді. z > 2.5 және IsolationForest «аномалия» десе, немесе z > 3.5 болса — цикл тұрақсыз.
- **Жағдайды тану (ЖИ).** Логистикалық регрессия және Random Forest, 52 белгі (7 дискретті + 5 сигнал × 9), бағалау — Leave-One-Subject-Out.
- **Мәтіндік қорытынды (ЖИ).** Ережелерге негізделген генератор, тек есептелген сандарды қолданады. Қаласаңыз, Claude API мәтінді жетілдіреді (сандар өзгертілмейді).
- **Топтық талдау.** Бірлік — бала; Wilcoxon signed-rank + Holm.
""",
        "ethics": """
- Деректер ашық және толық иесіздендірілген (KU Leuven RDR).
- GaitLens **диагноз қоймайды және ем тағайындамайды** — тек дәрігерге анықтама береді.
- Нәтижелер бір сессиядағы жедел әсерді көрсетеді; ұзақ мерзімді әсер бағаланбайды.
- Бір баланың циклдері өзара тәуелді — пациент деңгейіндегі p-мәндер шамамен алынған.
- 29 пациент — шағын іріктеме; ML нәтижелерін жалпылауға сақ болу керек.
""",
        "sources": """
- **Деректер:** De Mulder T., Adams H., Dewit T., Molenaers G., Van Campenhout A., Desloovere K. (2024). *A Comparison of the Immediate Effects of Verbal and Virtual Reality Feedback on Gait in Children with Cerebral Palsy.* KU Leuven RDR. https://doi.org/10.48804/JUNNWW — лицензия **CC-BY-NC-SA-4.0**.
- **Мақала:** Children 2024, 11, 524. https://doi.org/10.3390/children11050524
- **Кітапханалар:** Streamlit, pandas, NumPy, SciPy, scikit-learn, Plotly (ашық лицензиялар).
- **ЖИ құралдары:** Claude Code (Anthropic) — код жазуға көмекші; Claude API (опция) — мәтінді жетілдіру.
- **МКФ:** WHO ICF — b770 (жүріс паттернінің функциялары), d450 (жүру).
""",
    },
    "ru": {
        "methods": """
- **Загрузка данных.** CSV: разделитель `;`, десятичный разделитель `,`, пропуски `NaN`. 29 пациентов, у каждого одна сторона, ~30 циклов на условие.
- **Изменения.** По каждому параметру Verbal/VR сравниваются с Baseline: среднее ± SD, Δ, Δ%, тест Манна-Уитни (поправка Холма), Cliff's delta (пренебрежимый < 0.147 ≤ малый < 0.33 ≤ средний < 0.474 ≤ выраженный). Порог клинической значимости GPS — 1.6° (Baker et al., 2012).
- **Кривые.** 5 сигналов × 51 точка (0–100% цикла). Среднее ± SD; участок наибольшего отличия от Baseline находится автоматически.
- **Нестабильные шаги (ИИ).** Кривые цикла → RMS-расстояние до медианного шага ребёнка → робастный z-score; IsolationForest как дополнительная проверка. Цикл нестабилен, если z > 2.5 и IsolationForest отметил аномалию, либо z > 3.5.
- **Распознавание условия (ИИ).** Логистическая регрессия и Random Forest, 52 признака (7 дискретных + 5 сигналов × 9), оценка — Leave-One-Subject-Out.
- **Текстовая сводка (ИИ).** Генератор на правилах, использует только рассчитанные числа. По желанию Claude API улучшает текст (числа не меняются).
- **Групповой анализ.** Единица — ребёнок; Wilcoxon signed-rank + Холм.
""",
        "ethics": """
- Данные открытые и полностью обезличенные (KU Leuven RDR).
- GaitLens **не ставит диагноз и не назначает лечение** — только справка для врача.
- Результаты отражают немедленный эффект в одной сессии; долгосрочный эффект не оценивается.
- Циклы одного ребёнка взаимозависимы — p-значения на уровне пациента приблизительны.
- 29 пациентов — малая выборка; обобщать результаты ML следует осторожно.
""",
        "sources": """
- **Данные:** De Mulder T., Adams H., Dewit T., Molenaers G., Van Campenhout A., Desloovere K. (2024). *A Comparison of the Immediate Effects of Verbal and Virtual Reality Feedback on Gait in Children with Cerebral Palsy.* KU Leuven RDR. https://doi.org/10.48804/JUNNWW — лицензия **CC-BY-NC-SA-4.0**.
- **Статья:** Children 2024, 11, 524. https://doi.org/10.3390/children11050524
- **Библиотеки:** Streamlit, pandas, NumPy, SciPy, scikit-learn, Plotly (открытые лицензии).
- **ИИ-инструменты:** Claude Code (Anthropic) — помощник при написании кода; Claude API (опция) — улучшение текста.
- **МКФ:** WHO ICF — b770 (функции стереотипа походки), d450 (ходьба).
""",
    },
}

st.title(f"{t('about_title', lng)}")
disclaimer(lng)

st.subheader(t("data_quality", lng))
st.caption(t("data_quality_help", lng))
q = data.quality_report()
q["side"] = q["side"].map(lambda s: t("side_" + s, lng))
q.columns = [t("col_subject", lng), t("col_side", lng), "Baseline", "Verbal", "VR", t("col_missing", lng)]
st.dataframe(q, hide_index=True, width="stretch")

st.subheader(t("methods", lng))
st.markdown(TEXT[lng]["methods"])
st.subheader(t("ethics", lng))
st.markdown(TEXT[lng]["ethics"])
st.subheader(t("sources", lng))
st.markdown(TEXT[lng]["sources"])
