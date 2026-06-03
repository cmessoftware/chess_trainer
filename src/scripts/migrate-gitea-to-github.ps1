param(
    [Parameter(Mandatory = $false)]
    [string]$GiteaBaseUrl,

    [Parameter(Mandatory = $false)]
    [string]$GiteaOwner,

    [Parameter(Mandatory = $false)]
    [string]$GiteaRepo,

    [Parameter(Mandatory = $false)]
    [string]$GiteaToken,

    [Parameter(Mandatory = $true)]
    [string]$GithubOwner,

    [Parameter(Mandatory = $true)]
    [string]$GithubRepo,

    [switch]$MigrateGitHistory,
    [switch]$MigrateIssues,
    [switch]$MigrateProject,
    [int]$GithubProjectNumber,
    [switch]$DryRun
)

Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"

function Write-Step {
    param([string]$Message)
    Write-Host "[STEP] $Message" -ForegroundColor Cyan
}

function Write-Info {
    param([string]$Message)
    Write-Host "[INFO] $Message" -ForegroundColor Gray
}

function Write-WarnLine {
    param([string]$Message)
    Write-Host "[WARN] $Message" -ForegroundColor Yellow
}

function Resolve-GiteaSettingsFromRemote {
    $remoteUrl = (& git remote get-url gitea 2>$null)
    if ([string]::IsNullOrWhiteSpace($remoteUrl)) {
        throw "Remote 'gitea' not found and required Gitea parameters were not provided."
    }

    $owner = $null
    $repo = $null
    $baseUrl = $null
    $token = $null

    if ($remoteUrl -match '^(https?)://([^/@:]+)(:([^@/]+))?@([^/]+)/(.*)$') {
        $scheme = $Matches[1]
        $token = $Matches[4]
        $remoteHost = $Matches[5]
        $path = $Matches[6]
        $baseUrl = "${scheme}://$remoteHost"

        if ($path -match '^([^/]+)/([^/]+?)(\.git)?$') {
            $owner = $Matches[1]
            $repo = $Matches[2]
        }
    }
    elseif ($remoteUrl -match '^(https?)://([^/]+)/(.*)$') {
        $scheme = $Matches[1]
        $remoteHost = $Matches[2]
        $path = $Matches[3]
        $baseUrl = "${scheme}://$remoteHost"

        if ($path -match '^([^/]+)/([^/]+?)(\.git)?$') {
            $owner = $Matches[1]
            $repo = $Matches[2]
        }
    }

    return @{
        baseUrl = $baseUrl
        owner   = $owner
        repo    = $repo
        token   = $token
    }
}

function Test-CommandAvailable {
    param([string]$Name)
    if (-not (Get-Command $Name -ErrorAction SilentlyContinue)) {
        throw "Command '$Name' is required but was not found in PATH."
    }
}

function Invoke-GiteaGet {
    param(
        [string]$PathAndQuery
    )

    $base = $GiteaBaseUrl.TrimEnd('/')
    $url = "$base/api/v1/$PathAndQuery"
    if ([string]::IsNullOrWhiteSpace($GiteaToken)) {
        return Invoke-RestMethod -Method Get -Uri $url
    }

    $headers = @{ Authorization = "token $GiteaToken" }
    return Invoke-RestMethod -Method Get -Uri $url -Headers $headers
}

function Get-GiteaPaged {
    param(
        [string]$Path,
        [string]$ExtraQuery = ""
    )

    $page = 1
    $limit = 50
    $all = @()

    while ($true) {
        $sep = "?"
        if ($Path.Contains('?')) { $sep = "&" }
        $query = "$Path${sep}page=$page&limit=$limit"
        if ($ExtraQuery) {
            $query = "$query&$ExtraQuery"
        }

        $chunk = Invoke-GiteaGet -PathAndQuery $query
        if ($null -eq $chunk) { break }

        if ($chunk -is [System.Array]) {
            $all += $chunk
            if ($chunk.Count -lt $limit) { break }
        }
        else {
            $all += @($chunk)
            break
        }

        $page += 1
    }

    return $all
}

function Invoke-Gh {
    param(
        [string[]]$GhCommandParts,
        [switch]$AllowFailure
    )

    $cmd = "gh " + ($GhCommandParts -join ' ')
    if ($DryRun) {
        Write-Info "DRY-RUN: $cmd"
        return $null
    }

    try {
        return & gh @GhCommandParts
    }
    catch {
        if ($AllowFailure) {
            Write-WarnLine "Command failed (ignored): $cmd"
            return $null
        }
        throw
    }
}

function Test-GhAuth {
    $status = Invoke-Gh -GhCommandParts @("auth", "status") -AllowFailure
    if ($null -eq $status -and -not $DryRun) {
        throw "GitHub CLI is not authenticated. Run: gh auth login"
    }
}

function Update-GithubRemote {
    param([string]$RepoSlug)

    $remoteName = "github"
    $remoteUrl = "https://github.com/$RepoSlug.git"

    $existing = git remote
    if ($existing -contains $remoteName) {
        Write-Info "Remote '$remoteName' already exists."
    }
    else {
        if ($DryRun) {
            Write-Info "DRY-RUN: git remote add $remoteName $remoteUrl"
        }
        else {
            git remote add $remoteName $remoteUrl | Out-Null
        }
    }
}

function Start-GitHistoryMigration {
    param([string]$RepoSlug)

    Write-Step "Migrating git history (branches + tags) to GitHub repo $RepoSlug"
    Update-GithubRemote -RepoSlug $RepoSlug

    if ($DryRun) {
        Write-Info "DRY-RUN: git fetch --all --tags"
        Write-Info "DRY-RUN: git push github --all"
        Write-Info "DRY-RUN: git push github --tags"
        return
    }

    git fetch --all --tags | Out-Null
    git push github --all
    git push github --tags
}

function Sync-Labels {
    param(
        [string]$RepoSlug,
        [array]$Issues
    )

    Write-Step "Ensuring labels in GitHub"

    $labels = @{}
    foreach ($issue in $Issues) {
        if ($issue.labels) {
            foreach ($lbl in $issue.labels) {
                $name = [string]$lbl.name
                if (-not $labels.ContainsKey($name)) {
                    $color = ([string]$lbl.color).TrimStart('#')
                    if ([string]::IsNullOrWhiteSpace($color)) { $color = "999999" }
                    if ($color.Length -ne 6) { $color = "999999" }
                    $labels[$name] = @{ color = $color; description = [string]$lbl.description }
                }
            }
        }
    }

    foreach ($name in $labels.Keys) {
        $meta = $labels[$name]
        $ghCommandParts = @(
            "label", "create", $name,
            "--repo", $RepoSlug,
            "--color", $meta.color
        )
        if ($meta.description) {
            $ghCommandParts += @("--description", $meta.description)
        }
        Invoke-Gh -GhCommandParts $ghCommandParts -AllowFailure | Out-Null
    }
}

function Sync-Milestones {
    param(
        [string]$RepoSlug,
        [array]$Issues
    )

    Write-Step "Ensuring milestones in GitHub"

    $titles = New-Object System.Collections.Generic.HashSet[string]
    foreach ($issue in $Issues) {
        if ($issue.milestone -and $issue.milestone.title) {
            [void]$titles.Add([string]$issue.milestone.title)
        }
    }

    foreach ($title in $titles) {
        $ghCommandParts = @("api", "repos/$RepoSlug/milestones", "-X", "POST", "-f", "title=$title")
        Invoke-Gh -GhCommandParts $ghCommandParts -AllowFailure | Out-Null
    }
}

function Get-MilestoneMap {
    param([string]$RepoSlug)

    $json = Invoke-Gh -GhCommandParts @("api", "repos/$RepoSlug/milestones?state=all&per_page=100")
    if ($null -eq $json) { return @{} }

    $list = $json | ConvertFrom-Json
    $map = @{}
    foreach ($m in $list) {
        $map[[string]$m.title] = [int]$m.number
    }
    return $map
}

function Convert-IssueBody {
    param($Issue)

    $srcUrl = "$($GiteaBaseUrl.TrimEnd('/'))/$GiteaOwner/$GiteaRepo/issues/$($Issue.number)"
    $header = "Migrated from Gitea issue #$($Issue.number)`nOriginal: $srcUrl`n"
    $body = [string]$Issue.body
    if ([string]::IsNullOrWhiteSpace($body)) {
        return "$header`n"
    }
    return "$header`n---`n$body"
}

function Get-StatusOptionId {
    param(
        [array]$Options,
        [string]$TargetName
    )

    foreach ($opt in $Options) {
        if ([string]$opt.name -eq $TargetName) {
            return [string]$opt.id
        }
    }
    return $null
}

function Resolve-ProjectStatus {
    param($GiteaIssue)

    if ([string]$GiteaIssue.state -eq "closed") {
        return "Done"
    }

    $labelNames = @()
    if ($GiteaIssue.labels) {
        $labelNames = $GiteaIssue.labels | ForEach-Object { ([string]$_.name).ToLowerInvariant() }
    }

    if ($labelNames -contains "in progress" -or $labelNames -contains "in-progress" -or $labelNames -contains "doing" -or $labelNames -contains "wip") {
        return "In Progress"
    }

    return "Todo"
}

function Add-IssueToProject {
    param(
        [string]$RepoSlug,
        [int]$ProjectNumber,
        [string]$IssueUrl,
        [string]$StatusName
    )

    $projectViewJson = Invoke-Gh -GhCommandParts @("project", "view", "$ProjectNumber", "--owner", $GithubOwner, "--format", "json")
    if ($null -eq $projectViewJson) { return }
    $project = $projectViewJson | ConvertFrom-Json
    $projectId = [string]$project.id

    $fieldListJson = Invoke-Gh -GhCommandParts @("project", "field-list", "$ProjectNumber", "--owner", $GithubOwner, "--format", "json")
    if ($null -eq $fieldListJson) { return }
    $fields = $fieldListJson | ConvertFrom-Json

    $statusField = $fields.fields | Where-Object { $_.name -eq "Status" } | Select-Object -First 1
    if ($null -eq $statusField) {
        Write-WarnLine "Project Status field not found. Item added without status update."
        Invoke-Gh -GhCommandParts @("project", "item-add", "$ProjectNumber", "--owner", $GithubOwner, "--url", $IssueUrl) -AllowFailure | Out-Null
        return
    }

    $addJson = Invoke-Gh -GhCommandParts @("project", "item-add", "$ProjectNumber", "--owner", $GithubOwner, "--url", $IssueUrl, "--format", "json")
    if ($null -eq $addJson) { return }
    $item = $addJson | ConvertFrom-Json
    $itemId = [string]$item.id

    $optionId = Get-StatusOptionId -Options $statusField.options -TargetName $StatusName
    if ($null -eq $optionId) {
        Write-WarnLine "Status option '$StatusName' not found in project."
        return
    }

    Invoke-Gh -GhCommandParts @(
        "project", "item-edit",
        "--id", $itemId,
        "--project-id", $projectId,
        "--field-id", ([string]$statusField.id),
        "--single-select-option-id", $optionId
    ) -AllowFailure | Out-Null
}

function Start-IssuesAndCommentsMigration {
    param(
        [string]$RepoSlug,
        [switch]$IncludeProject,
        [int]$ProjectNumber
    )

    Write-Step "Fetching Gitea issues"
    $issues = Get-GiteaPaged -Path "repos/$GiteaOwner/$GiteaRepo/issues" -ExtraQuery "state=all&sort=created&direction=asc"

    # Gitea can include PR-like objects in same endpoint; exclude if pull_request exists.
    $issues = $issues | Where-Object { -not $_.pull_request }

    Write-Info "Issues fetched: $($issues.Count)"

    Sync-Labels -RepoSlug $RepoSlug -Issues $issues
    Sync-Milestones -RepoSlug $RepoSlug -Issues $issues
    $milestoneMap = Get-MilestoneMap -RepoSlug $RepoSlug

    $issueMap = @{}

    foreach ($issue in $issues) {
        $title = [string]$issue.title
        $body = Convert-IssueBody -Issue $issue

        $tmpBody = [System.IO.Path]::GetTempFileName()
        [System.IO.File]::WriteAllText($tmpBody, $body)

        $ghCommandParts = @("issue", "create", "--repo", $RepoSlug, "--title", $title, "--body-file", $tmpBody)

        if ($issue.labels) {
            foreach ($lbl in $issue.labels) {
                $ghCommandParts += @("--label", [string]$lbl.name)
            }
        }

        if ($issue.milestone -and $issue.milestone.title) {
            $msTitle = [string]$issue.milestone.title
            if ($milestoneMap.ContainsKey($msTitle)) {
                $ghCommandParts += @("--milestone", $msTitle)
            }
        }

        $created = Invoke-Gh -GhCommandParts $ghCommandParts

        Remove-Item $tmpBody -Force -ErrorAction SilentlyContinue

        $createdUrl = [string]$created
        $ghNumber = $null
        if ($createdUrl -match "/issues/(\d+)$") {
            $ghNumber = [int]$Matches[1]
            $issueMap[[int]$issue.number] = @{ githubNumber = $ghNumber; githubUrl = $createdUrl }
        }
        else {
            Write-WarnLine "Could not parse created issue number for Gitea issue #$($issue.number)"
            continue
        }

        $comments = Get-GiteaPaged -Path "repos/$GiteaOwner/$GiteaRepo/issues/$($issue.number)/comments"
        foreach ($comment in $comments) {
            $commentBody = [string]$comment.body
            if (-not [string]::IsNullOrWhiteSpace($commentBody)) {
                $commentText = "[Migrated comment from Gitea]`n`n$commentBody"
                $tmpComment = [System.IO.Path]::GetTempFileName()
                [System.IO.File]::WriteAllText($tmpComment, $commentText)
                Invoke-Gh -GhCommandParts @("issue", "comment", "$ghNumber", "--repo", $RepoSlug, "--body-file", $tmpComment) -AllowFailure | Out-Null
                Remove-Item $tmpComment -Force -ErrorAction SilentlyContinue
            }
        }

        if ([string]$issue.state -eq "closed") {
            Invoke-Gh -GhCommandParts @("issue", "close", "$ghNumber", "--repo", $RepoSlug) -AllowFailure | Out-Null
        }

        if ($IncludeProject -and $ProjectNumber -gt 0) {
            $statusName = Resolve-ProjectStatus -GiteaIssue $issue
            Add-IssueToProject -RepoSlug $RepoSlug -ProjectNumber $ProjectNumber -IssueUrl $createdUrl -StatusName $statusName
        }
    }

    $mapPath = Join-Path (Get-Location) "migration_issue_map.json"
    $serializableMap = @{}
    foreach ($k in $issueMap.Keys) {
        $serializableMap[[string]$k] = $issueMap[$k]
    }
    $serializableMap | ConvertTo-Json -Depth 5 | Set-Content -Path $mapPath -Encoding UTF8
    Write-Info "Issue map exported: $mapPath"
}

# ---------------------------------------------------------
# Main
# ---------------------------------------------------------

$resolved = Resolve-GiteaSettingsFromRemote

if ([string]::IsNullOrWhiteSpace($GiteaBaseUrl)) { $GiteaBaseUrl = [string]$resolved.baseUrl }
if ([string]::IsNullOrWhiteSpace($GiteaOwner)) { $GiteaOwner = [string]$resolved.owner }
if ([string]::IsNullOrWhiteSpace($GiteaRepo)) { $GiteaRepo = [string]$resolved.repo }
if ([string]::IsNullOrWhiteSpace($GiteaToken)) { $GiteaToken = [string]$resolved.token }

if ([string]::IsNullOrWhiteSpace($GiteaBaseUrl) -or [string]::IsNullOrWhiteSpace($GiteaOwner) -or [string]::IsNullOrWhiteSpace($GiteaRepo)) {
    throw "Could not resolve Gitea base URL/owner/repo. Provide -GiteaBaseUrl, -GiteaOwner and -GiteaRepo explicitly."
}

if ($MigrateIssues -and [string]::IsNullOrWhiteSpace($GiteaToken)) {
    Write-WarnLine "Gitea token not provided. Continuing without token (works only for public repositories)."
}

Test-CommandAvailable -Name "gh"
Test-CommandAvailable -Name "git"
Test-GhAuth

$repoSlug = "$GithubOwner/$GithubRepo"

if (-not $MigrateGitHistory -and -not $MigrateIssues -and -not $MigrateProject) {
    throw "Choose at least one operation: -MigrateGitHistory or -MigrateIssues (with optional -MigrateProject)."
}

if ($MigrateProject -and $GithubProjectNumber -le 0) {
    throw "When using -MigrateProject, provide -GithubProjectNumber <number>."
}

if ($MigrateGitHistory) {
    Start-GitHistoryMigration -RepoSlug $repoSlug
}

if ($MigrateIssues) {
    Start-IssuesAndCommentsMigration -RepoSlug $repoSlug -IncludeProject:$MigrateProject -ProjectNumber $GithubProjectNumber
}

Write-Host "Migration workflow finished." -ForegroundColor Green
