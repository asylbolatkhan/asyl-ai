"""GaitLens — іске қосу / запуск:  streamlit run app.py"""
import streamlit as st

from gaitlens import theme
from gaitlens.i18n import t
from gaitlens.ui import language_selector, sidebar_brand

st.set_page_config(page_title="GaitLens", page_icon=":material/directions_walk:", layout="wide")
theme.inject()

sidebar_brand(st.session_state.get("lang", "kk"))
lng = language_selector()

pages = [
    st.Page("views/patient.py", title=t("nav_patient", lng), icon=":material/person:", default=True),
    st.Page("views/cohort.py", title=t("nav_cohort", lng), icon=":material/groups:", url_path="cohort"),
    st.Page("views/model.py", title=t("nav_model", lng), icon=":material/model_training:", url_path="model"),
    st.Page("views/about.py", title=t("nav_about", lng), icon=":material/menu_book:", url_path="about"),
]
st.navigation(pages).run()
