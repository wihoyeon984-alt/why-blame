param(
    [Parameter(Mandatory)]
    [string]$Title,

    [string]$Base = "main",

    [string]$BodyFile,

    [switch]$NoWait,

    [switch]$DryRun
)

Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"

. (Join-Path $PSScriptRoot "lib\common.ps1")

function Get-OpenPullRequestNumber {
    param(
        [string]$Head,
        [string]$BaseBranch
    )

    $json = gh pr list `
        --head $Head `
        --base $BaseBranch `
        --state open `
        --json number

    Assert-LastExitCode "Unable to list pull requests."

    $parsed = ConvertFrom-Json -InputObject $json
    $items = @($parsed)

    if ($items.Count -eq 0) {
        return $null
    }

    $numberProperty = (
        $items[0].PSObject.Properties["number"]
    )

    if ($null -eq $numberProperty) {
        return $null
    }

    return $numberProperty.Value
}

function New-DefaultBodyFile {
    param(
        [string]$Branch,
        [string]$BaseBranch
    )

    $path = Join-Path `
        $env:TEMP `
        "why-blame-pr-$PID.md"

    $commits = @(
        git log `
            --format="- %s" `
            "$BaseBranch..$Branch"
    )

    Assert-LastExitCode "Unable to list branch commits."

    $files = @(
        git diff `
            --name-only `
            "$BaseBranch...$Branch"
    )

    Assert-LastExitCode "Unable to list changed files."

    $lines = @(
        "## Summary"
        ""
        $Title
        ""
        "## Commits"
        ""
    )

    if ($commits.Count -eq 0) {
        $lines += "- No commits found."
    }
    else {
        $lines += $commits
    }

    $lines += @(
        ""
        "## Changed files"
        ""
    )

    if ($files.Count -eq 0) {
        $lines += "- No changed files found."
    }
    else {
        foreach ($file in $files) {
            $lines += "- $file"
        }
    }

    $lines += @(
        ""
        "## Validation"
        ""
        "- [x] Full verification passed"
        "- [x] Holdout v1 integrity passed"
        "- [x] Holdout v2 post-improvement scoring passed"
    )

    [System.IO.File]::WriteAllLines(
        $path,
        $lines,
        [System.Text.UTF8Encoding]::new($false)
    )

    return $path
}

try {
    Assert-Command git
    Assert-Command gh
    Assert-Command python

    Enter-RepositoryRoot | Out-Null

    $branch = Get-CurrentBranch

    if (-not $branch) {
        throw "Detached HEAD is not supported."
    }

    if ($branch -eq $Base) {
        throw "Current branch must not be the base branch."
    }

    if ($DryRun) {
        Write-Step "Dry run allows uncommitted changes"
        Write-Success "Working tree cleanliness check was skipped."
    }
    else {
        Assert-CleanWorkingTree
    }

    Write-Step "Running full verification"

    powershell `
        -NoProfile `
        -ExecutionPolicy Bypass `
        -File (Join-Path $PSScriptRoot "verify.ps1") `
        -Mode Full

    Assert-LastExitCode "Full verification failed."

    if ($DryRun) {
        Write-Host ""
        Write-Host "Dry run completed."
        Write-Host "Branch: $branch"
        Write-Host "Base:   $Base"
        Write-Host "Title:  $Title"

        Write-Success "No push or PR creation was performed."
        exit 0
    }

    Write-Step "Checking GitHub authentication"

    gh auth status

    Assert-LastExitCode "GitHub authentication failed."

    $existingPr = Get-OpenPullRequestNumber `
        -Head $branch `
        -BaseBranch $Base

    if ($existingPr) {
        Write-Success "Open PR already exists: #$existingPr"

        gh pr view $existingPr `
            --json number,title,state,url,mergeable,mergeStateStatus

        exit 0
    }

    Write-Step "Pushing branch"

    git push -u origin $branch

    Assert-LastExitCode "Branch push failed."

    $temporaryBody = $false

    if (-not $BodyFile) {
        $BodyFile = New-DefaultBodyFile `
            -Branch $branch `
            -BaseBranch $Base

        $temporaryBody = $true
    }

    try {
        Write-Step "Creating pull request"

        $url = gh pr create `
            --base $Base `
            --head $branch `
            --title $Title `
            --body-file $BodyFile

        Assert-LastExitCode "Pull request creation failed."

        Write-Host "PR URL: $url"
    }
    finally {
        if ($temporaryBody) {
            Remove-Item `
                $BodyFile `
                -Force `
                -ErrorAction SilentlyContinue
        }
    }

    $prNumber = Get-OpenPullRequestNumber `
        -Head $branch `
        -BaseBranch $Base

    if (-not $prNumber) {
        throw "Created pull request was not found."
    }

    if (-not $NoWait) {
        Write-Step "Waiting for check registration"

        $checksRegistered = $false

        for ($attempt = 1; $attempt -le 18; $attempt++) {
            $statusJson = gh pr view $prNumber `
                --json statusCheckRollup

            Assert-LastExitCode `
                "Unable to read pull request checks."

            $status = ConvertFrom-Json `
                -InputObject $statusJson

            $checkCount = @(
                $status.statusCheckRollup
            ).Count

            Write-Host "Check registration attempt ${attempt}/18: $checkCount checks"

            if ($checkCount -gt 0) {
                $checksRegistered = $true
                break
            }

            Start-Sleep -Seconds 10
        }

        if (-not $checksRegistered) {
            throw "Pull request checks were not registered."
        }

        Write-Step "Waiting for pull request checks"

        gh pr checks $prNumber `
            --watch `
            --interval 10

        Assert-LastExitCode "Pull request checks failed."
    }

    Write-Step "Reading pull request status"

    gh pr view $prNumber `
        --json number,title,state,url,mergeable,mergeStateStatus,statusCheckRollup

    Assert-LastExitCode "Unable to read pull request status."

    Write-Host ""
    Write-Success "Pull request workflow completed."
}
catch {
    Write-Host ""
    Write-Host "[FAIL] $($_.Exception.Message)" `
        -ForegroundColor Red

    exit 1
}