from __future__ import annotations

from dataclasses import dataclass, replace
from datetime import datetime

from backend.application.licensing_service import LicensingService


@dataclass
class FakeStatus:
    valid: bool
    expire_date: datetime | None = None
    message: str = ""
    days_left: int | None = None


@dataclass
class FakeCert:
    license_code: str = ""


class FakeLicenseManager:
    def __init__(self) -> None:
        self.saved_cert = None
        self.verify_reg_code_result = FakeStatus(valid=True, expire_date=datetime(2026, 6, 1), message="OK", days_left=30)

    def get_machine_code(self) -> str:
        return "MACHINE-CODE"

    def verify_cert(self) -> FakeStatus:
        return FakeStatus(valid=True, expire_date=datetime(2026, 5, 1), message="valid", days_left=10)

    def verify_reg_code(self, machine_code: str, reg_code: str) -> FakeStatus:
        assert machine_code == "MACHINE-CODE"
        assert reg_code == "ABC123"
        return self.verify_reg_code_result

    def load_cert(self) -> FakeCert:
        return FakeCert(license_code="OLD")

    def save_cert(self, cert: FakeCert) -> None:
        self.saved_cert = cert


def test_licensing_service_machine_code_and_verify() -> None:
    service = LicensingService(FakeLicenseManager())

    assert service.machine_code({}) == {"machineCode": "MACHINE-CODE"}
    assert service.verify({}) == {
        "valid": True,
        "expireDate": "2026-05-01T00:00:00",
        "daysLeft": 10,
        "message": "valid",
    }


def test_licensing_service_register_saves_updated_cert_on_success() -> None:
    manager = FakeLicenseManager()
    service = LicensingService(manager)

    result = service.register({"code": "  ABC123  "})

    assert result == {
        "valid": True,
        "expireDate": "2026-06-01T00:00:00",
        "daysLeft": 30,
        "message": "OK",
    }
    assert manager.saved_cert == FakeCert(license_code="ABC123")


def test_licensing_service_register_reports_save_failure() -> None:
    manager = FakeLicenseManager()

    def fail_save(cert: FakeCert) -> None:
        raise RuntimeError("disk full")

    manager.save_cert = fail_save  # type: ignore[assignment]
    service = LicensingService(manager)

    result = service.register({"code": "ABC123"})

    assert result == {
        "valid": False,
        "message": "校验通过但保存证书失败: disk full",
        "expireDate": "2026-06-01T00:00:00",
        "daysLeft": 30,
    }
