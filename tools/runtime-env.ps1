function Get-ProjectRoot {
    param(
        [string]$StartDir = $PSScriptRoot
    )

    return (Resolve-Path (Join-Path $StartDir "..")).Path
}

function Read-RuntimeConfig {
    param(
        [string]$ProjectRoot = (Get-ProjectRoot)
    )

    $config = [ordered]@{}
    $candidates = @(
        (Join-Path $ProjectRoot ".env.runtime.local"),
        (Join-Path $ProjectRoot ".env.runtime.example")
    )
    $configPath = $candidates | Where-Object { Test-Path $_ } | Select-Object -First 1
    if (-not $configPath) {
        return $config
    }

    foreach ($line in Get-Content $configPath -Encoding UTF8) {
        $trimmed = $line.Trim()
        if (-not $trimmed -or $trimmed.StartsWith('#')) { continue }
        $parts = $trimmed -split '=', 2
        if ($parts.Count -ne 2) { continue }
        $key = $parts[0].Trim()
        $value = $parts[1].Trim().Trim('"').Trim("'")
        if ($key) {
            $config[$key] = $value
        }
    }

    return $config
}

function Resolve-ProjectPythonCommand {
    param(
        [string[]]$PythonArgs,
        [string]$ProjectRoot = (Get-ProjectRoot)
    )

    $config = Read-RuntimeConfig -ProjectRoot $ProjectRoot
    $explicitPython = [string]($config["EXAM_PYTHON_EXE"])
    if ($explicitPython.Trim()) {
        return @{
            FilePath = $explicitPython.Trim()
            Arguments = @($PythonArgs)
            Description = "EXAM_PYTHON_EXE=$($explicitPython.Trim())"
        }
    }

    $mode = [string]($config["EXAM_PYTHON_MODE"])
    $condaEnv = [string]($config["EXAM_CONDA_ENV"])
    if ($mode.Trim().ToLower() -eq 'conda' -or $condaEnv.Trim()) {
        if (-not $condaEnv.Trim()) {
            throw "运行环境配置缺少 EXAM_CONDA_ENV"
        }
        $condaExe = [string]($config["EXAM_CONDA_EXE"])
        if (-not $condaExe.Trim()) {
            $condaExe = "conda"
        }
        return @{
            FilePath = $condaExe.Trim()
            Arguments = @("run", "--no-capture-output", "-n", $condaEnv.Trim(), "python") + @($PythonArgs)
            Description = "$($condaExe.Trim()) run -n $($condaEnv.Trim()) python"
        }
    }

    return @{
        FilePath = "python"
        Arguments = @($PythonArgs)
        Description = "python"
    }
}

function Invoke-ProjectPython {
    param(
        [string[]]$PythonArgs,
        [string]$ProjectRoot = (Get-ProjectRoot)
    )

    $command = Resolve-ProjectPythonCommand -PythonArgs $PythonArgs -ProjectRoot $ProjectRoot
    Write-Host "Using Python runtime: $($command.Description)"
    & $command.FilePath @($command.Arguments)
    if ($LASTEXITCODE -ne 0) {
        exit $LASTEXITCODE
    }
}
