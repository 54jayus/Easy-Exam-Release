param(
    [Parameter(ValueFromRemainingArguments = $true)]
    [string[]]$SelfcheckArgs
)

. (Join-Path $PSScriptRoot "runtime-env.ps1")

$projectRoot = Get-ProjectRoot -StartDir $PSScriptRoot
Set-Location $projectRoot

$pythonArgs = @("-m", "backend.selfcheck")
if ($SelfcheckArgs) {
    $pythonArgs += $SelfcheckArgs
}

Invoke-ProjectPython -ProjectRoot $projectRoot -PythonArgs $pythonArgs
