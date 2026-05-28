param(
    [Parameter(ValueFromRemainingArguments = $true)]
    [string[]]$PytestArgs
)

. (Join-Path $PSScriptRoot "runtime-env.ps1")

$projectRoot = Get-ProjectRoot -StartDir $PSScriptRoot
Set-Location $projectRoot

$pythonArgs = @("-m", "pytest")
if ($PytestArgs) {
    $pythonArgs += $PytestArgs
}

$command = Resolve-ProjectPythonCommand -ProjectRoot $projectRoot -PythonArgs $pythonArgs
Write-Host "Using Python runtime: $($command.Description)"
$process = Start-Process `
    -FilePath $command.FilePath `
    -ArgumentList @($command.Arguments) `
    -NoNewWindow `
    -Wait `
    -PassThru
if ($process.ExitCode -ne 0) {
    exit $process.ExitCode
}
