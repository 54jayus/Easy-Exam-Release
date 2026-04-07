import os
import shutil
import subprocess
import sys
from pathlib import Path


def run_command(command, cwd=None):
    """Run a command and exit on error."""
    cmd_str = " ".join(command) if isinstance(command, list) else str(command)
    print(f"Executing: {cmd_str}")
    try:
        subprocess.check_call(command, cwd=cwd, shell=isinstance(command, str))
    except subprocess.CalledProcessError as exc:
        print(f"Error executing command: {exc}")
        sys.exit(1)


def resolve_python_executable():
    candidates = [
        os.environ.get("EXAM_PYTHON_PATH"),
        os.environ.get("VITE_PYTHON_PATH"),
        sys.executable,
        shutil.which("python"),
    ]

    for candidate in candidates:
        if not candidate:
            continue
        resolved = Path(candidate).expanduser()
        if resolved.exists():
            return str(resolved)

    raise FileNotFoundError(
        "Unable to resolve a Python executable for packaging. "
        "Set EXAM_PYTHON_PATH or VITE_PYTHON_PATH first."
    )


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

    python_executable = resolve_python_executable()
    print(f"Using Python executable: {python_executable}")

    pyinstaller_cmd = [
        python_executable,
        "-m",
        "PyInstaller",
        str(spec_file),
        "--distpath",
        str(python_dist_dir),
        "--workpath",
        str(python_build_dir),
        "--noconfirm",
        "--clean",
    ]
    run_command(pyinstaller_cmd, cwd=str(project_root))

    print("\n=== Step 2: Building Electron Frontend & Installer ===")
    run_command(["npm.cmd", "run", "electron:build"], cwd=str(frontend_dir))

    print("\n=== Packaging Complete! ===")
    print(f"Installer should be in: {release_dir}")


if __name__ == "__main__":
    package()
