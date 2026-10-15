$ErrorActionPreference = 'Stop'
Set-Location -LiteralPath $PSScriptRoot
if (!(Test-Path -LiteralPath '.venv/Scripts/python.exe')) {
    $taskPython = Join-Path $env:USERPROFILE '.cache/codex-runtimes/codex-primary-runtime/dependencies/python/python.exe'
    if (!(Test-Path -LiteralPath $taskPython)) { $taskPython = 'python' }
    & $taskPython -m venv .venv
    if ($LASTEXITCODE -ne 0) { throw 'Python 3.12 or newer is required.' }
    $taskRequirements = 'requirements.txt'
    if (Test-Path -LiteralPath 'requirements-lock.txt') { $taskRequirements = 'requirements-lock.txt' }
    & '.venv/Scripts/python.exe' -m pip install -r $taskRequirements
    if ($LASTEXITCODE -ne 0) { throw 'Dependency installation failed.' }
}
if (!(Test-Path -LiteralPath 'models/individual_rf.joblib')) {
    & '.venv/Scripts/python.exe' tools/download_data.py
    if ($LASTEXITCODE -ne 0) { throw 'Original data snapshot is required to rebuild models.' }
    & '.venv/Scripts/python.exe' tools/build_demo.py
    if ($LASTEXITCODE -ne 0) { throw 'Model preparation failed.' }
    & '.venv/Scripts/python.exe' tools/rebuild_models.py
    if ($LASTEXITCODE -ne 0) { throw 'Benchmark reproduction failed.' }
}
& '.venv/Scripts/python.exe' app/server.py
