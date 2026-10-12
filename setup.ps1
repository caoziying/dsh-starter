[CmdletBinding()]
param(
    [ValidateSet('DeepSeek', 'School', 'Ollama')]
    [string]$Provider = 'DeepSeek',
    [string]$Model = '',
    [ValidateRange(4096, 131072)]
    [int]$ContextWindow = 8192
)

$ErrorActionPreference = 'Stop'
$root = [System.IO.Path]::GetFullPath($PSScriptRoot)
$pythonCommand = Get-Command python -ErrorAction Stop
$pythonVersion = & $pythonCommand.Source -c "import sys; print(f'{sys.version_info.major}.{sys.version_info.minor}')"
if ($LASTEXITCODE -ne 0 -or $pythonVersion -notin @('3.11', '3.12', '3.13')) {
    throw "Python 3.11–3.13 is required; found $pythonVersion"
}

switch ($Provider) {
    'DeepSeek' {
        if (-not $Model) { $Model = 'deepseek-v4-flash' }
        $mode = 'deepseek'
        if (-not $PSBoundParameters.ContainsKey('ContextWindow')) { $ContextWindow = 32768 }
    }
    'School' {
        if (-not $Model) { throw 'School provider requires -Model <gateway-model-id>' }
        $mode = 'school'
        if (-not $PSBoundParameters.ContainsKey('ContextWindow')) { $ContextWindow = 32768 }
    }
    'Ollama' {
        if (-not $Model) { throw 'Ollama provider requires -Model <installed-model-name>' }
        $mode = 'ollama'
    }
}

$venv = Join-Path $root 'harness\.venv'
$venvPython = Join-Path $venv 'Scripts\python.exe'
if (-not (Test-Path -LiteralPath $venvPython)) {
    & $pythonCommand.Source -m venv $venv
    if ($LASTEXITCODE -ne 0) { throw 'Failed to create Python virtual environment' }
}
& $venvPython -m pip install --disable-pip-version-check -r (Join-Path $root 'harness\requirements.txt')
if ($LASTEXITCODE -ne 0) { throw 'Python dependency installation failed' }

$secrets = Join-Path $root 'harness\config\secrets.env'
if (-not (Test-Path -LiteralPath $secrets)) {
    Copy-Item -LiteralPath (Join-Path $root 'harness\config\secrets.env.example') -Destination $secrets
}

$providerConfig = [ordered]@{
    provider = $mode
    model = $Model
    context_window = $ContextWindow
    max_output_tokens = [Math]::Min(4096, [int]($ContextWindow / 2))
}
$providerConfig | ConvertTo-Json -Depth 4 | Set-Content -LiteralPath (Join-Path $root 'harness\config\provider.json') -Encoding UTF8

Write-Host "Configured $Provider / $Model." -ForegroundColor Green
if ($mode -ne 'ollama') {
    Write-Host "Fill in $secrets, then run doctor.ps1 and start.ps1."
} else {
    Write-Host 'Ensure Ollama is running and the named model is downloaded; then run doctor.ps1 and start.ps1.'
}
