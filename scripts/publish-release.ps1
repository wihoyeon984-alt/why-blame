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

    Write-Step "Validating package contents"

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

    Write-Step "Generating release checksums"

    python `
        (Join-Path $PSScriptRoot "create_release_checksums.py") `
        --version $Version `
        --dist-dir .\dist

    Assert-LastExitCode `
        "Release checksum generation failed."

    $wheelFiles = @(
        Get-ChildItem `
            ".\dist\why_blame-$Version-*.whl" `
            -File
    )

    $sdistFiles = @(
        Get-ChildItem `
            ".\dist\why_blame-$Version.tar.gz" `
            -File
    )

    $checksumPath = Join-Path `
        (Resolve-Path .\dist).Path `
        "SHA256SUMS.txt"

    if ($wheelFiles.Count -ne 1) {
        throw "Expected exactly one release wheel."
    }

    if ($sdistFiles.Count -ne 1) {
        throw "Expected exactly one source distribution."
    }

    if (-not (Test-Path $checksumPath)) {
        throw "SHA256SUMS.txt was not created."
    }

    Write-Step "Creating annotated release tag"

    git tag -a $tag -m "why-blame $tag"

    Assert-LastExitCode `
        "Unable to create the release tag."

    $tagCommit = (git rev-list -n 1 $tag).Trim()
    $mainCommit = (git rev-parse HEAD).Trim()

    if ($tagCommit -ne $mainCommit) {
        git tag -d $tag | Out-Null
        throw "Release tag does not point to current main."
    }

    Write-Step "Pushing release tag"

    git push origin $tag

    Assert-LastExitCode `
        "Unable to push the release tag."

    $notesPath = Join-Path `
        $env:TEMP `
        "why-blame-$tag-notes-$PID.md"

    $notesLines = @(
        "## Why-Blame $tag"
        ""
        "See CHANGELOG.md for the complete release notes."
        ""
        "### Validation"
        ""
        "- Full verification passed."
        "- HTTP ResourceWarning count is zero."
        "- Holdout v1 integrity verification passed."
        "- Holdout v2 post-improvement scoring passed."
        "- Wheel installation and CLI execution were verified."
    )

    [System.IO.File]::WriteAllLines(
        $notesPath,
        $notesLines,
        [System.Text.UTF8Encoding]::new($false)
    )

    try {
        Write-Step "Creating GitHub Release"

        gh release create $tag `
            $wheelFiles[0].FullName `
            $sdistFiles[0].FullName `
            $checksumPath `
            --title "why-blame $tag" `
            --notes-file $notesPath `
            --verify-tag

        Assert-LastExitCode `
            "GitHub Release creation failed."
    }
    finally {
        Remove-Item `
            $notesPath `
            -Force `
            -ErrorAction SilentlyContinue
    }

    Write-Step "Validating GitHub Release"

    $releaseJson = gh release view $tag `
        --json tagName,name,isDraft,isPrerelease,assets

    Assert-LastExitCode `
        "Unable to inspect the created GitHub Release."

    $release = ConvertFrom-Json `
        -InputObject $releaseJson

    if ($release.tagName -ne $tag) {
        throw "Published Release tag is incorrect."
    }

    if ($release.isDraft) {
        throw "Published Release is unexpectedly a draft."
    }

    if ($release.isPrerelease) {
        throw "Published Release is unexpectedly a prerelease."
    }

    $assetNames = @(
        $release.assets |
            ForEach-Object {
                $_.name
            }
    )

    $expectedAssets = @(
        "SHA256SUMS.txt"
        $wheelFiles[0].Name
        $sdistFiles[0].Name
    )

    foreach ($expectedAsset in $expectedAssets) {
        if ($expectedAsset -notin $assetNames) {
            throw "Missing Release asset: $expectedAsset"
        }
    }

    if ($assetNames.Count -ne 3) {
        throw "Expected exactly three Release assets."
    }

    Write-Success "GitHub Release assets are valid."

    Write-Step "Removing build artifacts"

    Remove-BuildArtifacts

    if (git branch --list $releaseBranch) {
        git branch -d $releaseBranch

        Assert-LastExitCode `
            "Unable to delete the local release branch."
    }

    if (
        git branch -r `
            --list "origin/$releaseBranch"
    ) {
        git push origin --delete $releaseBranch

        Assert-LastExitCode `
            "Unable to delete the remote release branch."
    }

    git fetch origin --prune

    Assert-LastExitCode `
        "Unable to prune remote branches."

    Write-Host ""
    Write-Success "Release $tag was published successfully."
}
catch {
    Write-Host ""
    Write-Host "[FAIL] $($_.Exception.Message)" `
        -ForegroundColor Red

    exit 1
}