from pathlib import Path


def test_app_uses_streamlit_compatible_controls() -> None:
    app_source = Path("app.py").read_text()

    assert "st.segmented_control" not in app_source
