param(
    [Parameter(ValueFromRemainingArguments = $true)]
    [string[]]$OpenSpecArgs
)

$repoRoot = Split-Path -Parent $MyInvocation.MyCommand.Path
$specRoot = Join-Path $repoRoot "docs\ai_chess_coach"

if (-not (Test-Path $specRoot)) {
    Write-Error "No se encontro la ruta esperada: $specRoot"
    exit 1
}

Push-Location $specRoot
try {
    & mamba run -n chess_trainer npx -y @fission-ai/openspec @OpenSpecArgs
    exit $LASTEXITCODE
}
finally {
    Pop-Location
}
