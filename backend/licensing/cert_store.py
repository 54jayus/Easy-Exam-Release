from __future__ import annotations

import os
import sys
from dataclasses import dataclass
from pathlib import Path


def get_repo_root() -> Path:
    return Path(__file__).resolve().parents[2]


def get_app_base_dir() -> Path:
    env_dir = os.getenv("EXAMFLOW_APP_DIR") or os.getenv("EXAMDESK_APP_DIR") or ""
    if env_dir.strip():
        return Path(env_dir).resolve()
    if getattr(sys, "frozen", False):
        return Path(sys.executable).resolve().parent
    return get_repo_root()


def get_data_base_dir() -> Path | None:
    env_dir = os.getenv("EXAMFLOW_DATA_DIR") or os.getenv("EXAMDESK_DATA_DIR") or ""
    if env_dir.strip():
        return Path(env_dir).resolve()
    return None


def get_default_cert_path() -> Path:
    env_dir = os.getenv("EXAMFLOW_CERT_DIR") or os.getenv("EXAMDESK_CERT_DIR") or ""
    if env_dir.strip():
        return Path(env_dir).resolve() / "license.cert"
    data_dir = get_data_base_dir()
    if data_dir is not None:
        return data_dir / "license.cert"
    return get_app_base_dir() / "license.cert"


def get_cert_candidate_paths(path: str | os.PathLike[str] | None = None, *, include_fallbacks: bool = True) -> list[Path]:
    if path is not None:
        return [Path(path)]

    candidates: list[Path] = [get_default_cert_path()]
    if include_fallbacks:
        try:
            legacy_app_path = get_app_base_dir() / "license.cert"
            if legacy_app_path not in candidates:
                candidates.append(legacy_app_path)
        except Exception:
            pass
        try:
            repo_path = get_repo_root() / "license.cert"
            if repo_path not in candidates:
                candidates.append(repo_path)
        except Exception:
            pass
        try:
            cwd_path = Path.cwd() / "license.cert"
            if cwd_path not in candidates:
                candidates.append(cwd_path)
        except Exception:
            pass
    return candidates


def find_existing_cert_path(path: str | os.PathLike[str] | None = None, *, include_fallbacks: bool = True) -> Path | None:
    for candidate in get_cert_candidate_paths(path, include_fallbacks=include_fallbacks):
        try:
            raw = candidate.read_text(encoding="utf-8")
            if raw.strip():
                return candidate
        except Exception:
            continue
    return None


@dataclass(frozen=True)
class LicenseCert:
    license_code: str = ""
    api_key: str = ""

    @staticmethod
    def load(path: str | os.PathLike[str] | None = None) -> "LicenseCert":
        candidates = get_cert_candidate_paths(path, include_fallbacks=path is None)

        raw = ""
        for p in candidates:
            try:
                raw = p.read_text(encoding="utf-8")
                if raw.strip():
                    break
            except Exception:
                continue
        if not raw.strip():
            return LicenseCert()

        lines = [line.strip() for line in raw.splitlines() if line.strip()]
        if not lines:
            return LicenseCert()

        license_code = lines[0]
        api_key = ""
        for line in lines[1:]:
            if line.startswith("API_KEY:"):
                api_key = line.split("API_KEY:", 1)[1].strip()
                break
        return LicenseCert(license_code=license_code, api_key=api_key)

    def save(self, path: str | os.PathLike[str] | None = None) -> None:
        p = Path(path) if path is not None else get_default_cert_path()
        p.parent.mkdir(parents=True, exist_ok=True)
        lines: list[str] = []
        if self.license_code:
            lines.append(self.license_code.strip())
        if self.api_key:
            lines.append(f"API_KEY:{self.api_key.strip()}")
        p.write_text("\n".join(lines) + ("\n" if lines else ""), encoding="utf-8")
