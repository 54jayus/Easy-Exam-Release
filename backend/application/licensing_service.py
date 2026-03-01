from __future__ import annotations

from dataclasses import replace
from datetime import datetime
from typing import Any

from backend.licensing import LicenseManager


def _dt_to_iso(v: Any) -> Any:
    if isinstance(v, datetime):
        return v.isoformat()
    return v


class LicensingService:
    def __init__(self, license_manager: LicenseManager):
        self._lm = license_manager

    def machine_code(self, _params: dict) -> Any:
        return {"machineCode": self._lm.get_machine_code()}

    def verify(self, _params: dict) -> Any:
        status = self._lm.verify_cert()
        return {
            "valid": status.valid,
            "expireDate": _dt_to_iso(status.expire_date),
            "daysLeft": status.days_left,
            "message": status.message,
        }

    def register(self, params: dict) -> Any:
        reg_code = params.get("code", "").strip()
        try:
            machine_code = self._lm.get_machine_code()
            status = self._lm.verify_reg_code(machine_code, reg_code)
            if status.valid:
                try:
                    existing_cert = self._lm.load_cert()
                    new_cert = replace(existing_cert, license_code=reg_code)
                    self._lm.save_cert(new_cert)
                except Exception as e:
                    return {
                        "valid": False,
                        "message": f"校验通过但保存证书失败: {str(e)}",
                        "expireDate": _dt_to_iso(status.expire_date),
                        "daysLeft": status.days_left,
                    }
            return {
                "valid": status.valid,
                "expireDate": _dt_to_iso(status.expire_date),
                "daysLeft": status.days_left,
                "message": status.message,
            }
        except Exception as e:
            return {"valid": False, "message": f"激活过程发生异常: {str(e)}", "daysLeft": 0}
