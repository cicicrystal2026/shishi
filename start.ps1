$ErrorActionPreference = 'Stop'
Set-Location -LiteralPath $PSScriptRoot
$taskNode = (Get-Command node -ErrorAction SilentlyContinue).Source
$taskBundledNode = Join-Path $env:USERPROFILE '.cache\codex-runtimes\codex-primary-runtime\dependencies\node\bin\node.exe'
if (Test-Path -LiteralPath $taskBundledNode) { $taskNode = $taskBundledNode }
if (-not $taskNode) { throw 'Node.js 24+ is required.' }
if (-not (Test-Path -LiteralPath 'node_modules\vite')) { throw 'Run npm ci first.' }
if (-not (Test-Path -LiteralPath 'dist\index.html')) { & $taskNode node_modules/vite/bin/vite.js build; if ($LASTEXITCODE -ne 0) { throw 'Build failed.' } }
Write-Host 'Shishi: http://127.0.0.1:4317'
& $taskNode --env-file-if-exists=.env apps/api/server.ts
