"""Exercise real Streamlit widgets against the committed offline data."""

from streamlit.testing.v1 import AppTest

from av_safety.data import ROOT


def test_all_tabs_and_filters():
    app = AppTest.from_file(ROOT / "app.py", default_timeout=30).run()
    assert not app.exception
    assert [t.label for t in app.tabs] == [
        "Rates",
        "Compare",
        "Experiment Planner",
        "Methods & Limitations",
    ]
    initial = app.dataframe[0].value
    app.sidebar.multiselect[0].set_value([2024]).run()
    assert not app.exception
    assert len(app.dataframe[0].value) == 1
    assert len(initial) == 5
    app.sidebar.multiselect[1].set_value([]).run()
    assert not app.exception
    assert any("No exposure" in item.value for item in app.info)


def test_driverless_and_zero_event_group():
    app = AppTest.from_file(ROOT / "app.py", default_timeout=30).run()
    app.sidebar.selectbox[0].set_value("driverless")
    app.sidebar.multiselect[1].set_value(["Zoox"]).run()
    assert not app.exception
    assert app.dataframe[0].value["rate"].isna().all()
