# Script para eliminar emojis de archivos Python y reemplazarlos con texto
param(
    [string]$FilePath = "src\scripts\smart_random_games_fetcher.py"
)

$content = Get-Content $FilePath -Raw -Encoding UTF8

# Lista de reemplazos de emojis a texto (simplificada)
$replacements = @{
    "✅"  = "[SUCCESS]"
    "❌"  = "[ERROR]"
    "⚠️" = "[WARNING]"
    "🚀" = "[START]"
    "📋" = "[PARAMS]"
    "📂" = "[LOADING]"
    "🔍" = "[DISCOVER]"
    "🎯" = "[TARGET]"
    "🎉" = "[SUCCESS]"
    "🚫" = "[SKIP]"
    "📁" = "[SAVED]"
    "📊" = "[SUMMARY]"
    "🎮" = "[SAMPLE]"
    "⏳"  = "[RATE_LIMIT]"
    "📈" = "[STATS]"
    "📝" = "[NOTE]"
    "📄" = "[FILE]"
    "📤" = "[EXPORT]"
    "🔄" = "[PROCESS]"
    "🔁" = "[REPEAT]"
    "📦" = "[PACKAGE]"
    "🏁" = "[FINISH]"
    "💾" = "[SAVE]"
    "⚡"  = "[FAST]"
    "🎲" = "[RANDOM]"
}

# Aplicar reemplazos
foreach ($emoji in $replacements.Keys) {
    $replacement = $replacements[$emoji]
    $content = $content -replace [regex]::Escape($emoji), $replacement
}

# Guardar el archivo
Set-Content -Path $FilePath -Value $content -Encoding UTF8

Write-Host "[SUCCESS] Emojis replaced in $FilePath"
