"""Smoke tests for application configuration."""

from config.settings import APP_NAME, MAX_UPLOAD_MB


def test_default_app_name_is_invoiceflow():
    assert APP_NAME == "InvoiceFlow"


def test_upload_limit_is_positive():
    assert MAX_UPLOAD_MB > 0
