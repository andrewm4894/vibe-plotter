import pytest

from app.models import AppError
from app.utils import validate_csv_url


def test_validate_csv_url_blocks_non_http():
    with pytest.raises(AppError):
        validate_csv_url("file:///tmp/data.csv")


def test_validate_csv_url_blocks_localhost():
    with pytest.raises(AppError):
        validate_csv_url("http://localhost/data.csv")


def test_validate_csv_url_allowlist():
    with pytest.raises(AppError):
        validate_csv_url("https://example.com/data.csv", allowed_hosts={"allowed.com"})

    validate_csv_url("https://allowed.com/data.csv", allowed_hosts={"allowed.com"})
