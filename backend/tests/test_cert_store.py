from __future__ import annotations

from backend.licensing.cert_store import LicenseCert


def test_license_cert_save_and_load_round_trip(tmp_path) -> None:
    path = tmp_path / "license.cert"
    cert = LicenseCert(license_code="ABC123", api_key="KEY456")

    cert.save(path)
    loaded = LicenseCert.load(path)

    assert loaded == cert


def test_license_cert_load_returns_empty_for_missing_file(tmp_path) -> None:
    loaded = LicenseCert.load(tmp_path / "missing.cert")

    assert loaded == LicenseCert()


def test_license_cert_load_parses_license_only_file(tmp_path) -> None:
    path = tmp_path / "license.cert"
    path.write_text("ONLY-LICENSE\n", encoding="utf-8")

    loaded = LicenseCert.load(path)

    assert loaded == LicenseCert(license_code="ONLY-LICENSE", api_key="")
