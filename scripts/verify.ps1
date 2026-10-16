param(
    [ValidateSet("Quick", "Full")]
    [string]$Mode = "Full"
)

Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"

. (Join-Path $PSScriptRoot "lib\common.ps1")

function Test-PowerShellSyntax {
    Write-Step "Checking PowerShell syntax"

    $files = @(
        Get-ChildItem -Path $PSScriptRoot -Filter "*.ps1" -File
        Get-ChildItem -Path "$PSScriptRoot\lib" -Filter "*.ps1" -File
    )

    foreach ($file in $files) {
        $tokens = $null
        $errors = $null

        [System.Management.Automation.Language.Parser]::ParseFile(
            $file.FullName,
            [ref]$tokens,
            [ref]$errors
        ) | Out-Null

        if ($errors.Count -gt 0) {
            throw "PowerShell syntax failed: $($file.Name)"
        }
    }

    Write-Success "$($files.Count) PowerShell files passed."
}

function Test-Diff {
    Write-Step "Checking Git diff"

    git diff --check
    Assert-LastExitCode "git diff --check failed."

    Write-Success "Git diff check passed."
}

function Test-UnitSuite {
    Write-Step "Running unit tests"

    python -m unittest discover -v
    Assert-LastExitCode "Unit tests failed."

    Write-Success "Unit tests passed."
}

function Test-Holdout {
    Write-Step "Checking Holdout v1"

    python .\benchmark\holdout\verify_v1_integrity.py
    Assert-LastExitCode "Holdout v1 verification failed."

    Write-Step "Checking Holdout v2 post-improvement"

    python .\benchmark\holdout_v2\score_post_improvement.py
    Assert-LastExitCode "Post-improvement scoring failed."

    Write-Success "Holdout checks passed."
}

try {
    Assert-Command git
    Assert-Command python

    $root = Enter-RepositoryRoot
    $branch = Get-CurrentBranch
    $version = Get-ProjectVersion

    Write-Host "Repository: $root"
    Write-Host "Branch:     $branch"
    Write-Host "Version:    $version"
    Write-Host "Mode:       $Mode"

    Assert-VersionFormat $version

    Test-Diff
    Test-PowerShellSyntax

    if ($Mode -eq "Full") {
        Test-UnitSuite
        Test-Holdout
    }

    Write-Host ""
    Write-Success "$Mode verification completed."
}
catch {
    Write-Host ""
    Write-Host "[FAIL] $($_.Exception.Message)" -ForegroundColor Red
    exit 1
}