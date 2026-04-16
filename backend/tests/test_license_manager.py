from __future__ import annotations

import datetime as dt

from backend.licensing.core import LicenseCert, LicenseManager


def test_license_manager_generate_and_verify_reg_code(monkeypatch) -> None:
    manager = LicenseManager(app_secret="secret", salt="salt")
    current_time = dt.datetime(2026, 4, 6, 12, 0, 0)

    class FixedDatetime(dt.datetime):
        @classmethod
        def now(cls, tz=None):
            return current_time

    monkeypatch.setattr("backend.licensing.core.dt.datetime", FixedDatetime)

    reg_code, expire_date = manager.generate_reg_code("MACHINE123", 30)

    monkeypatch.setattr(manager, "get_beijing_time", lambda: current_time)
    status = manager.verify_reg_code("MACHINE123", reg_code)

    assert expire_date == current_time + dt.timedelta(days=30)
    assert status.valid is True
    assert status.message == "OK"
    assert status.days_left == 31


def test_license_manager_verify_reg_code_rejects_invalid_formats(monkeypatch) -> None:
    manager = LicenseManager(app_secret="secret", salt="salt")
    monkeypatch.setattr(manager, "get_beijing_time", lambda: dt.datetime(2026, 4, 6, 12, 0, 0))

    no_dash = manager.verify_reg_code("MACHINE123", "invalid")
    bad_timestamp = manager.verify_reg_code("MACHINE123", "abc-def")

    assert no_dash.message == "注册码格式错误（缺少分隔符）"
    assert bad_timestamp.message == "注册码时间戳格式错误"


def test_license_manager_verify_reg_code_rejects_expired_and_tampered_codes(monkeypatch) -> None:
    manager = LicenseManager(app_secret="secret", salt="salt")
    current_time = dt.datetime(2026, 4, 6, 12, 0, 0)
    monkeypatch.setattr(manager, "get_beijing_time", lambda: current_time)

    expired_timestamp = int((current_time - dt.timedelta(days=1)).timestamp())
    expired = manager.verify_reg_code("MACHINE123", f"{expired_timestamp}-hash")

    valid_code, _ = manager.generate_reg_code("MACHINE123", 10)
    tampered = manager.verify_reg_code("MACHINE123", valid_code[:-1] + "X")

    assert expired.valid is False
    assert "注册码已过期" in expired.message
    assert expired.days_left == 0
    assert tampered.valid is False
    assert tampered.message == "注册码无效或已被篡改"


def test_license_manager_verify_cert_uses_saved_license(monkeypatch, tmp_path) -> None:
    path = tmp_path / "license.cert"
    LicenseCert(license_code="SAVED-CODE").save(path)
    manager = LicenseManager(app_secret="secret", salt="salt", cert_path=path)

    monkeypatch.setattr(manager, "get_machine_code", lambda: "MACHINE123")
    monkeypatch.setattr(manager, "verify_reg_code", lambda machine_code, reg_code: type("Status", (), {"valid": True, "message": reg_code, "days_left": 9, "expire_date": None})())

    status = manager.verify_cert()

    assert status.valid is True
    assert status.message == "SAVED-CODE"


def test_license_manager_load_cert_migrates_from_legacy_app_dir(monkeypatch, tmp_path) -> None:
    user_data_dir = tmp_path / "user-data"
    legacy_app_dir = tmp_path / "legacy-app"
    monkeypatch.setenv("EXAMFLOW_DATA_DIR", str(user_data_dir))
    monkeypatch.setenv("EXAMFLOW_APP_DIR", str(legacy_app_dir))
    monkeypatch.delenv("EXAMFLOW_CERT_DIR", raising=False)
    monkeypatch.delenv("EXAMDESK_CERT_DIR", raising=False)

    legacy_path = legacy_app_dir / "license.cert"
    LicenseCert(license_code="OLD-CODE", api_key="OLD-KEY").save(legacy_path)

    manager = LicenseManager(app_secret="secret", salt="salt")

    cert = manager.load_cert()

    assert cert == LicenseCert(license_code="OLD-CODE", api_key="OLD-KEY")
    assert (user_data_dir / "license.cert").read_text(encoding="utf-8").startswith("OLD-CODE")
