# update_version.ps1 - Manual version update script for Windows

# Get current version from hook logic
$BASE_TAG = "v0.2"
$N = (git rev-list --count "$BASE_TAG..HEAD")
$HASH = (git rev-parse --short HEAD)
$VERSION = "$BASE_TAG.$N-$HASH"

Write-Host "🔍 Current calculated version: $VERSION" -ForegroundColor Cyan

# Update VERSION file
Set-Content -Path "VERSION" -Value $VERSION
Write-Host "✅ Updated VERSION file" -ForegroundColor Green

# Update README files if they exist
$FILES = @("README.md", "src/README.md")
foreach ($FILE in $FILES) {
    if (Test-Path $FILE) {
        $content = Get-Content $FILE -Raw
        # Replace existing version or add at the beginning
        if ($content -match "^# CHESS TRAINER.*Versión:") {
            $content = $content -replace "^# CHESS TRAINER.*Versión:.*", "# CHESS TRAINER - Versión: $VERSION"
        }
        else {
            $content = "# CHESS TRAINER - Versión: $VERSION`n`n$content"
        }
        Set-Content -Path $FILE -Value $content -NoNewline
        Write-Host "✅ Updated $FILE with version: $VERSION" -ForegroundColor Green
    }
}

Write-Host "🚀 Version update complete!" -ForegroundColor Yellow
Write-Host "📝 Don't forget to commit these changes:" -ForegroundColor Cyan
Write-Host "    git add VERSION README.md" -ForegroundColor White
Write-Host "    git commit -m `"chore: update version to $VERSION`"" -ForegroundColor White
