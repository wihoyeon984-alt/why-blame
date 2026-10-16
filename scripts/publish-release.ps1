param(
    [Parameter(Mandatory)]
    [string]$Version,

    [switch]$DryRun
)

Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"

. (Join-Path $PSScriptRoot "lib\common.ps1")

try {
    Assert-Command git
    Assert-Command gh
    Assert-Command python

    $root = Enter-RepositoryRoot
    $branch = Get-CurrentBranch
    $projectVersion = Get-ProjectVersion
    $tag = "v$Version"
    $releaseBranch = "release-v$Version"

    Write-Host "Repository:       $root"
    Write-Host "Current branch:   $branch"
    Write-Host "Project version:  $projectVersion"
    Write-Host "Requested version:$Version"
    Write-Host "Release tag:      $tag"
    Write-Host "Release branch:   $releaseBranch"
    Write-Host "Dry run:          $DryRun"

    Assert-VersionFormat $Version

    if ($branch -ne "main") {
        throw "Release publishing must start from main."
    }

    Assert-CleanWorkingTree

    git fetch origin --prune --tags
    Assert-LastExitCode "Unable to fetch origin."

    $localMain = (git rev-parse main).Trim()
    $remoteMain = (git rev-parse origin/main).Trim()

    if ($localMain -ne $remoteMain) {
        throw "Local main does not match origin/main."
    }

    if ($projectVersion -ne $Version) {
        throw "Project version '$projectVersion' does not match requested version '$Version'."
    }

    $changelogMarker = "## [$Version]"
    $readmeLabel = "why-blame v$Version"
    $readmeTarget = "releases/tag/v$Version"

    $changelogText = Get-Content `
        .\CHANGELOG.md `
        -Raw

    $readmeText = Get-Content `
        .\README.md `
        -Raw

    if (-not $changelogText.Contains($changelogMarker)) {
        throw "CHANGELOG entry is missing: $changelogMarker"
    }

    if (-not $readmeText.Contains($readmeLabel)) {
        throw "README release label is missing."
    }

    if (-not $readmeText.Contains($readmeTarget)) {
        throw "README release target is missing."
    }

    $localTag = git tag --list $tag

    if ($localTag) {
        throw "Local release tag already exists: $tag"
    }

    $remoteTag = git ls-remote `
        --tags `
        origin `
        "refs/tags/$tag"

    Assert-LastExitCode "Unable to inspect remote tags."

    if ($remoteTag) {
        throw "Remote release tag already exists: $tag"
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
                $_.tagName -eq $tag
            }
    )

    if ($matchingRelease.Count -gt 0) {
        throw "GitHub Release already exists: $tag"
    }

    Write-Success "Release publishing preflight passed."

    if ($DryRun) {
        Write-Host ""
        Write-Host "Planned actions:"
        Write-Host "1. Run full verification"
        Write-Host "2. Build wheel and source distribution"
        Write-Host "3. Validate package contents"
        Write-Host "4. Validate clean wheel installation"
        Write-Host "5. Generate SHA256SUMS.txt"
        Write-Host "6. Create and push annotated tag $tag"
        Write-Host "7. Create GitHub Release $tag"
        Write-Host "8. Verify exactly three Release assets"
        Write-Host "9. Remove build artifacts"
        Write-Host "10. Remove $releaseBranch if it exists"

        Write-Success "Publish dry run completed without changes."
        exit 0
    }

    throw "Non-dry-run publishing is not implemented yet."
}
catch {
    Write-Host ""
    Write-Host "[FAIL] $($_.Exception.Message)" `
        -ForegroundColor Red

    exit 1
}