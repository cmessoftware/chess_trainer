param(
    [Parameter(Mandatory = $true)]
    [string]$ProjectUrl,

    [Parameter(Mandatory = $true)]
    [string]$Issues,

    [switch]$DryRun
)

$ErrorActionPreference = 'Stop'

function Write-Info {
    param([string]$Message)
    Write-Host $Message -ForegroundColor Cyan
}

function Write-Step {
    param([string]$Message)
    Write-Host $Message -ForegroundColor Blue
}

function Write-Success {
    param([string]$Message)
    Write-Host $Message -ForegroundColor Green
}

function Write-WarningLine {
    param([string]$Message)
    Write-Host $Message -ForegroundColor Yellow
}

function Write-Fail {
    param([string]$Message)
    Write-Host $Message -ForegroundColor Red
}

function Import-DotEnv {
    param(
        [string]$Path = (Join-Path $PSScriptRoot '.env')
    )

    if (-not (Test-Path $Path)) {
        return
    }

    Get-Content $Path | ForEach-Object {
        $line = $_.Trim()

        if (-not $line -or $line.StartsWith('#')) {
            return
        }

        $separatorIndex = $line.IndexOf('=')
        if ($separatorIndex -lt 1) {
            return
        }

        $name = $line.Substring(0, $separatorIndex).Trim()
        $value = $line.Substring($separatorIndex + 1).Trim()

        if ($value.StartsWith('"') -and $value.EndsWith('"') -and $value.Length -ge 2) {
            $value = $value.Substring(1, $value.Length - 2)
        }

        if (-not [string]::IsNullOrWhiteSpace($name) -and [string]::IsNullOrEmpty([System.Environment]::GetEnvironmentVariable($name, 'Process'))) {
            [System.Environment]::SetEnvironmentVariable($name, $value, 'Process')
        }
    }
}

function Get-GiteaRepoInfo {
    param([string]$Url)

    $uri = [Uri]$Url
    $segments = $uri.AbsolutePath.Trim('/') -split '/'

    if ($segments.Count -lt 2) {
        throw "No pude extraer owner/repo desde la URL: $Url"
    }

    # Soporta URL de repo (/owner/repo) y URL de proyecto (/owner/repo/projects/{id}).
    if ($segments.Count -ge 4 -and $segments[2] -eq 'projects') {
        $owner = $segments[0]
        $repo = $segments[1]
    }
    else {
        $owner = $segments[$segments.Count - 2]
        $repo = $segments[$segments.Count - 1]
    }

    if ($repo.EndsWith('.git')) {
        $repo = $repo.Substring(0, $repo.Length - 4)
    }

    [pscustomobject]@{
        BaseUrl = $uri.GetLeftPart([System.UriPartial]::Authority)
        Owner   = $owner
        Repo    = $repo
    }
}

function Expand-IssueList {
    param([string]$Value)

    $result = New-Object System.Collections.Generic.List[int]
    $parts = $Value -split '[+,]'

    foreach ($part in $parts) {
        $token = $part.Trim()
        if (-not $token) {
            continue
        }

        if ($token -match '^(\d+)\.\.(\d+)$') {
            $start = [int]$Matches[1]
            $end = [int]$Matches[2]

            if ($start -gt $end) {
                throw "Rango inválido: $token"
            }

            for ($number = $start; $number -le $end; $number++) {
                if (-not $result.Contains($number)) {
                    [void]$result.Add($number)
                }
            }

            continue
        }

        if ($token -match '^\d+$') {
            $number = [int]$token
            if (-not $result.Contains($number)) {
                [void]$result.Add($number)
            }
            continue
        }

        throw "No pude interpretar el token de issue: $token"
    }

    return $result
}

Import-DotEnv

$token = [System.Environment]::GetEnvironmentVariable('GITEA_TOKEN', 'Process')
if ([string]::IsNullOrWhiteSpace($token)) {
    throw 'GITEA_TOKEN no encontrado en .env o en el entorno del proceso.'
}

$repoInfo = Get-GiteaRepoInfo -Url $ProjectUrl
$issueNumbers = Expand-IssueList -Value $Issues

if ($issueNumbers.Count -eq 0) {
    throw 'No se encontraron issues para cerrar.'
}

$apiBase = "$($repoInfo.BaseUrl)/api/v1"
$headers = @{ Authorization = "token $token" }

Write-Step "Cerrando $($issueNumbers.Count) issues en $($repoInfo.Owner)/$($repoInfo.Repo)"
Write-Info "Base API: $apiBase"

foreach ($issueNumber in $issueNumbers) {
    $endpoint = "$apiBase/repos/$($repoInfo.Owner)/$($repoInfo.Repo)/issues/$issueNumber"

    if ($DryRun) {
        Write-WarningLine "[DRY RUN] Cerraría issue #$issueNumber"
        continue
    }

    try {
        Invoke-RestMethod -Method Patch -Uri $endpoint -Headers $headers -ContentType 'application/json' -Body '{"state":"closed"}' | Out-Null
        Write-Success "Issue #$issueNumber cerrada"
    }
    catch {
        Write-Fail "Error cerrando issue #${issueNumber}: $($_.Exception.Message)"
    }
}

Write-Success 'Proceso completado.'