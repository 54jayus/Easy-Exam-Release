import os
import shutil
import subprocess
import sys
from pathlib import Path
from typing import Iterable


def run_command(command, cwd=None):
    """Run a command and exit on error."""
    cmd_str = " ".join(command) if isinstance(command, list) else str(command)
    print(f"Executing: {cmd_str}")
    try:
        subprocess.check_call(command, cwd=cwd, shell=isinstance(command, str))
    except subprocess.CalledProcessError as exc:
        print(f"Error executing command: {exc}")
        sys.exit(1)


def load_runtime_config(project_root: Path) -> dict[str, str]:
    config: dict[str, str] = {}
    candidates = [
        project_root / ".env.runtime.local",
        project_root / ".env.runtime.example",
    ]
    env_path = next((path for path in candidates if path.exists()), None)
    if env_path is None:
        return config

    for raw_line in env_path.read_text(encoding="utf-8").splitlines():
        line = raw_line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, value = line.split("=", 1)
        key = key.strip()
        value = value.strip().strip("'\"")
        if key:
            config[key] = value
    return config


def resolve_python_command(project_root: Path, python_args: Iterable[str]) -> tuple[list[str], str]:
    config = load_runtime_config(project_root)
    explicit_python = config.get("EXAM_PYTHON_EXE", "").strip()
    if explicit_python:
        return [explicit_python, *python_args], f"EXAM_PYTHON_EXE={explicit_python}"

    mode = config.get("EXAM_PYTHON_MODE", "").strip().lower()
    conda_env = config.get("EXAM_CONDA_ENV", "").strip()
    if mode == "conda" or conda_env:
        if not conda_env:
            raise ValueError("运行环境配置缺少 EXAM_CONDA_ENV")
        conda_exe = config.get("EXAM_CONDA_EXE", "conda").strip() or "conda"
        return (
            [conda_exe, "run", "--no-capture-output", "-n", conda_env, "python", *python_args],
            f"{conda_exe} run -n {conda_env} python",
        )

    return ["python", *python_args], "python"


def package():
    project_root = Path.cwd()
    frontend_dir = project_root / "frontend"

    spec_file = frontend_dir / "engine.spec"
    python_dist_dir = frontend_dir / "python-dist"
    python_build_dir = frontend_dir / "build-python"
    release_dir = frontend_dir / "release_v6"

    print("=== Step 1: Building Python Backend ===")

    if python_dist_dir.exists():
        print(f"Cleaning {python_dist_dir}...")
        shutil.rmtree(python_dist_dir)
    if python_build_dir.exists():
        print(f"Cleaning {python_build_dir}...")
        shutil.rmtree(python_build_dir)
    if release_dir.exists():
        print(f"Cleaning Electron output directory: {release_dir}...")
        try:
            shutil.rmtree(release_dir)
        except OSError as exc:
            print(
                "Warning: Failed to clean release directory. "
                f"Please close running app instances and retry. Error: {exc}"
            )

    pyinstaller_cmd, python_desc = resolve_python_command(
        project_root,
        [
            "-m",
            "PyInstaller",
            str(spec_file),
            "--distpath",
            str(python_dist_dir),
            "--workpath",
            str(python_build_dir),
            "--noconfirm",
            "--clean",
        ],
    )
    print(f"Using Python runtime: {python_desc}")
    run_command(pyinstaller_cmd, cwd=str(project_root))

    print("\n=== Step 2: Building Electron Frontend & Installer ===")
    npm_cmd = "npm.cmd" if sys.platform == "win32" else "npm"
    run_command([npm_cmd, "run", "electron:build"], cwd=str(frontend_dir))

    print("\n=== Packaging Complete! ===")
    print(f"Installer should be in: {release_dir}")


if __name__ == "__main__":
    package()
