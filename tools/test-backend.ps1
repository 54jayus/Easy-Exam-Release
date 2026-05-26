param(
    [Parameter(ValueFromRemainingArguments = $true)]
    [string[]]$PytestArgs
)

. (Join-Path $PSScriptRoot "runtime-env.ps1")

$projectRoot = Get-ProjectRoot -StartDir $PSScriptRoot
Set-Location $projectRoot

$args = @("-m", "pytest")
if ($PytestArgs) {
    $args += $PytestArgs
}

Invoke-ProjectPython -ProjectRoot $projectRoot -PythonArgs $args
