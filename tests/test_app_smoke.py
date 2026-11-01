"""Streamlit entry-point smoke test."""
from pathlib import Path

from streamlit.testing.v1 import AppTest


ROOT = Path(__file__).resolve().parents[1]


def test_invoiceflow_dashboard_starts_without_exception():
    app = AppTest.from_file(str(ROOT / "app.py"), default_timeout=90).run()
    assert not app.exception, "; ".join(
        str(item.message) for item in app.exception
    )
    assert any(metric.label == "Invoices stored" for metric in app.metric)
    assert any(button.label == "Process invoices" for button in app.button)
