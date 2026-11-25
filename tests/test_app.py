"""UI smoke tests: every page × language renders without exceptions."""
import pytest
from streamlit.testing.v1 import AppTest

PAGES = ["views/patient.py", "views/cohort.py", "views/model.py", "views/about.py"]


@pytest.mark.parametrize("lang", ["kk", "ru"])
@pytest.mark.parametrize("page", PAGES)
def test_page_renders(page, lang):
    at = AppTest.from_file("../app.py", default_timeout=120)
    at.session_state["lang"] = lang
    at.run()
    if page != PAGES[0]:
        at.switch_page(page)
        at.run()
    assert not at.exception, at.exception


@pytest.mark.parametrize("subject", ["s61520_7", "s61520_22", "s61520_3"])
@pytest.mark.parametrize("exclude", [False, True])
def test_patient_edge_cases(subject, exclude):
    at = AppTest.from_file("../app.py", default_timeout=120)
    at.session_state["subject"] = subject
    at.run()
    at.sidebar.checkbox[0].set_value(exclude).run()
    assert not at.exception, at.exception
    assert at.sidebar.selectbox[0].value == subject
