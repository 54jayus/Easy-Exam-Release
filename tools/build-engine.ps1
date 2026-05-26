. (Join-Path $PSScriptRoot "runtime-env.ps1")

$projectRoot = Get-ProjectRoot -StartDir $PSScriptRoot
Set-Location $projectRoot

Invoke-ProjectPython -ProjectRoot $projectRoot -PythonArgs @(
    "-m",
    "PyInstaller",
    "--clean",
    "--noconfirm",
    "frontend/engine.spec"
)
