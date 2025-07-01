# PowerShell Script - Commit Version Updates
# Usage: .\commit_version.ps1

Write-Host "🔍 Checking for version updates..." -ForegroundColor Cyan

# Check if there are changes to version files
$versionFiles = @("VERSION", "README.md")
$hasChanges = $false

foreach ($file in $versionFiles) {
    if (Test-Path $file) {
        $status = git status --porcelain $file
        if ($status) {
            Write-Host "📝 Found changes in: $file" -ForegroundColor Yellow
            $hasChanges = $true
        }
    }
}

if ($hasChanges) {
    # Get current version
    $version = Get-Content VERSION -Raw
    $version = $version.Trim()
    
    Write-Host "🚀 Committing version update: $version" -ForegroundColor Green
    
    # Add and commit version files (only existing ones)
    git add VERSION README.md
    git commit -m "auto-update version to $version"
    
    Write-Host "✅ Version update committed successfully!" -ForegroundColor Green
}
else {
    Write-Host "✅ No version changes to commit" -ForegroundColor Green
}
