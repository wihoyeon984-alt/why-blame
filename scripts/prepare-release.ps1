param(
    [Parameter(Mandatory)]
    [string]$Version,

    [Parameter(Mandatory)]
    [string]$Summary,

    [switch]$DryRun
)

Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"

. (Join-Path $PSScriptRoot "lib\common.ps1")

function Test-GitReference {
    param([string]$Reference)

    git show-ref --verify --quiet $Reference

    return $LASTEXITCODE -eq 0
}

try {
    Assert-Command git
    Assert-Command python
    Assert-Command gh

    $root = Enter-RepositoryRoot
    $branch = Get-CurrentBranch
    $currentVersion = Get-ProjectVersion
    $releaseBranch = "release-v$Version"

    Write-Host "Repository:      $root"
    Write-Host "Current branch:  $branch"
    Write-Host "Current version: $currentVersion"
    Write-Host "New version:     $Version"
    Write-Host "Release branch:  $releaseBranch"
    Write-Host "Summary:         $Summary"
    Write-Host "Dry run:         $DryRun"

    Assert-VersionFormat $Version

    if ($branch -ne "main") {
        throw "Release preparation must start from main."
    }

    Assert-CleanWorkingTree

    git fetch origin --prune --tags
    Assert-LastExitCode "Unable to fetch origin."

    $localMain = (git rev-parse main).Trim()
    $remoteMain = (git rev-parse origin/main).Trim()

    if ($localMain -ne $remoteMain) {
        throw "Local main does not match origin/main."
    }

    python (Join-Path $PSScriptRoot "update_release_metadata.py") `
        --version $Version `
        --summary $Summary `
        --date "2000-01-01"

    $metadataExitCode = $LASTEXITCODE

    git restore -- `
        pyproject.toml `
        README.md `
        CHANGELOG.md

    if ($metadataExitCode -ne 0) {
        throw "Release metadata preflight failed."
    }

    if (Test-GitReference "refs/heads/$releaseBranch") {
        throw "Local release branch already exists."
    }

    if (
        Test-GitReference `
            "refs/remotes/origin/$releaseBranch"
    ) {
        throw "Remote release branch already exists."
    }

    $localTag = git tag --list "v$Version"

    if ($localTag) {
        throw "Local release tag already exists."
    }

    $remoteTag = git ls-remote `
        --tags `
        origin `
        "refs/tags/v$Version"

    Assert-LastExitCode "Unable to inspect remote tags."

    if ($remoteTag) {
        throw "Remote release tag already exists."
    }

    $releaseJson = gh release list `
        --limit 100 `
        --json tagName

    Assert-LastExitCode `
        "Unable to inspect GitHub Releases."

    $releases = @(
        ConvertFrom-Json -InputObject $releaseJson
    )

    $matchingRelease = @(
        $releases |
            Where-Object {
                $_.tagName -eq "v$Version"
            }
    )

    if ($matchingRelease.Count -gt 0) {
        throw "GitHub Release already exists."
    }

    Write-Success "Release preflight checks passed."

    if ($DryRun) {
        Write-Host ""
        Write-Host "Planned actions:"
        Write-Host "1. Create $releaseBranch"
        Write-Host "2. Update release metadata to $Version"
        Write-Host "3. Run full verification"
        Write-Host "4. Build wheel and source distribution"
        Write-Host "5. Validate release packages"
        Write-Host "6. Install the wheel in a clean environment"
        Write-Host "7. Commit, push, and open a release PR"

        Write-Success "Dry run completed without changes."
        exit 0
    }

    Write-Step "Creating release branch"

    git switch -c $releaseBranch

    Assert-LastExitCode `
        "Unable to create the release branch."

    Write-Step "Updating release metadata"

    python `
        (Join-Path $PSScriptRoot "update_release_metadata.py") `
        --version $Version `
        --summary $Summary

    Assert-LastExitCode `
        "Release metadata update failed."

    Write-Step "Running full verification"

    powershell `
        -NoProfile `
        -ExecutionPolicy Bypass `
        -File (Join-Path $PSScriptRoot "verify.ps1") `
        -Mode Full

    Assert-LastExitCode `
        "Full release verification failed."

    Write-Step "Building release packages"

    Remove-BuildArtifacts

    python -m build

    Assert-LastExitCode `
        "Release package build failed."

    Write-Step "Validating release packages"

    python `
        (Join-Path $PSScriptRoot "check_release_package.py") `
        --version $Version `
        --dist-dir .\dist

    Assert-LastExitCode `
        "Release package validation failed."

    Write-Step "Validating clean wheel installation"

    python `
        (Join-Path $PSScriptRoot "check_release_install.py") `
        --version $Version `
        --dist-dir .\dist

    Assert-LastExitCode `
        "Release installation validation failed."

    Write-Step "Cleaning build artifacts"

    Remove-BuildArtifacts

    Write-Step "Validating release change scope"

    $changedFiles = @(
        git status --porcelain |
            ForEach-Object {
                $_.Substring(3).Trim()
            }
    )

    $expectedFiles = @(
        "CHANGELOG.md"
        "README.md"
        "pyproject.toml"
    )

    $unexpectedFiles = @(
        $changedFiles |
            Where-Object {
                $_ -notin $expectedFiles
            }
    )

    $missingFiles = @(
        $expectedFiles |
            Where-Object {
                $_ -notin $changedFiles
            }
    )

    if ($unexpectedFiles.Count -gt 0) {
        throw "Unexpected release files: $unexpectedFiles"
    }

    if ($missingFiles.Count -gt 0) {
        throw "Missing release files: $missingFiles"
    }

    Write-Success "Release change scope is valid."

    Write-Step "Committing release metadata"

    git add `
        .\CHANGELOG.md `
        .\README.md `
        .\pyproject.toml

    Assert-LastExitCode `
        "Unable to stage release metadata."

    git diff --cached --check

    Assert-LastExitCode `
        "Staged release diff validation failed."

    git commit -m "Prepare v$Version release"

    Assert-LastExitCode `
        "Release preparation commit failed."

    Write-Step "Opening release pull request"

    powershell `
        -NoProfile `
        -ExecutionPolicy Bypass `
        -File (Join-Path $PSScriptRoot "open-pr.ps1") `
        -Title "Prepare v$Version release"

    Assert-LastExitCode `
        "Release pull request workflow failed."

    Write-Host ""
    Write-Success "Release v$Version preparation completed."
}
catch {
    Write-Host ""
    Write-Host "[FAIL] $($_.Exception.Message)" `
        -ForegroundColor Red

    exit 1
}