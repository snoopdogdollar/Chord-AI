# Run inference only, using the environment and scratch space on D:.
$ErrorActionPreference = 'Stop'
$cnnPython = 'D:\chord-cnn-env\Scripts\python.exe'
if (-not (Test-Path -LiteralPath $cnnPython)) {
    throw "Missing CNN environment: $cnnPython"
}
$cnnSettings = @{
    TEMP = 'D:\chord-cnn-temp'
    TMP = 'D:\chord-cnn-temp'
    NUMBA_CACHE_DIR = 'D:\chord-cnn-temp\numba'
    PYTHONDONTWRITEBYTECODE = '1'
}
$cnnPrevious = @{}
try {
    foreach ($key in $cnnSettings.Keys) {
        $cnnPrevious[$key] = [Environment]::GetEnvironmentVariable($key, 'Process')
        [Environment]::SetEnvironmentVariable($key, $cnnSettings[$key], 'Process')
    }
    New-Item -ItemType Directory -Path 'D:\chord-cnn-temp\numba' -Force | Out-Null
    & $cnnPython (Join-Path $PSScriptRoot 'check_trained_bundle.py') --output 'D:\chord-cnn-results\rock_10_40'
    if ($LASTEXITCODE -ne 0) { throw "CPU check failed with exit code $LASTEXITCODE" }
}
finally {
    foreach ($key in $cnnPrevious.Keys) {
        [Environment]::SetEnvironmentVariable($key, $cnnPrevious[$key], 'Process')
    }
}
