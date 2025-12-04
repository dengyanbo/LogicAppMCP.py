import os
from pathlib import Path

import certifi

from app.cert_utils import ensure_requests_ca_bundle


def test_ensure_requests_ca_bundle_resets_missing_paths(monkeypatch, tmp_path):
    bogus_path = tmp_path / "missing.crt"
    monkeypatch.setenv("SSL_CERT_FILE", str(bogus_path))
    monkeypatch.setenv("REQUESTS_CA_BUNDLE", str(bogus_path))

    bundle = ensure_requests_ca_bundle()

    assert bundle == Path(certifi.where())
    assert os.environ["SSL_CERT_FILE"] == str(bundle)
    assert os.environ["REQUESTS_CA_BUNDLE"] == str(bundle)


def test_ensure_requests_ca_bundle_keeps_existing_file(monkeypatch, tmp_path):
    valid_path = tmp_path / "custom.crt"
    valid_path.write_text("dummy cert")
    monkeypatch.setenv("SSL_CERT_FILE", str(valid_path))

    bundle = ensure_requests_ca_bundle()

    assert bundle == valid_path
    assert os.environ["SSL_CERT_FILE"] == str(valid_path)
