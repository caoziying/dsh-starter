[CmdletBinding()]
param()
$ErrorActionPreference = 'Stop'
$root = [System.IO.Path]::GetFullPath($PSScriptRoot)
$python = Join-Path $root 'harness\.venv\Scripts\python.exe'
if (-not (Test-Path -LiteralPath $python)) { throw 'Run setup.ps1 first' }
& $python (Join-Path $root 'harness\doctor.py')
exit $LASTEXITCODE
