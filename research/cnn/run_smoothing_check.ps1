param(
    [Parameter(Mandatory=$true)][string]$Audio,
    [double]$Seconds = 0.4,
    [string]$Output = ('D:\chord-cnn-results\smoothing-' + (Get-Date -Format 'yyyyMMdd-HHmmss'))
)
$ErrorActionPreference = 'Stop'
$cnnPython = 'D:\chord-cnn-env\Scripts\python.exe'
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
    $windowText = $Seconds.ToString([System.Globalization.CultureInfo]::InvariantCulture)
    & $cnnPython (Join-Path $PSScriptRoot 'compare_smoothing.py') --audio $Audio --seconds $windowText --output $Output
    if ($LASTEXITCODE -ne 0) { throw "Smoothing comparison failed: $LASTEXITCODE" }
    Write-Host "Results: $Output"
}
finally {
    foreach ($key in $cnnPrevious.Keys) {
        [Environment]::SetEnvironmentVariable($key, $cnnPrevious[$key], 'Process')
    }
}
