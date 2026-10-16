Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"

function Write-Step {
    param([string]$Message)

    Write-Host ""
    Write-Host "[STEP] $Message" -ForegroundColor Cyan
}

function Write-Success {
    param([string]$Message)

    Write-Host "[ OK ] $Message" -ForegroundColor Green
}

function Assert-LastExitCode {
    param([string]$Message)

    if ($LASTEXITCODE -ne 0) {
        throw $Message
    }
}

function Assert-Command {
    param([string]$Name)

    if (-not (Get-Command $Name -ErrorAction SilentlyContinue)) {
        throw "Required command not found: $Name"
    }
}

function Get-RepositoryRoot {
    $value = git rev-parse --show-toplevel
    Assert-LastExitCode "Git repository not found."
    return $value.Trim()
}

function Enter-RepositoryRoot {
    $root = Get-RepositoryRoot
    Set-Location $root
    return $root
}

function Get-CurrentBranch {
    $value = git branch --show-current
    Assert-LastExitCode "Unable to determine the current branch."
    return $value.Trim()
}

function Assert-CurrentBranch {
    param([string]$Expected)

    $actual = Get-CurrentBranch

    if ($actual -ne $Expected) {
        throw "Expected branch '$Expected', found '$actual'."
    }
}

function Get-WorkingTreeChanges {
    $value = @(git status --porcelain)
    Assert-LastExitCode "Unable to inspect the working tree."
    return $value
}

function Assert-CleanWorkingTree {
    $changes = @(Get-WorkingTreeChanges)

    if ($changes.Count -gt 0) {
        $changes | ForEach-Object { Write-Host $_ }
        throw "The working tree is not clean."
    }

    Write-Success "The working tree is clean."
}

function Get-ProjectVersion {
    $code = "import tomllib; from pathlib import Path; print(tomllib.loads(Path('pyproject.toml').read_text(encoding='utf-8'))['project']['version'])"
    $value = python -c $code
    Assert-LastExitCode "Unable to read the project version."
    return $value.Trim()
}

function Assert-VersionFormat {
    param([string]$Version)

    if ($Version -notmatch '^\d+\.\d+\.\d+$') {
        throw "Invalid version format: $Version"
    }
}

function Remove-BuildArtifacts {
    Remove-Item .\dist -Recurse -Force -ErrorAction SilentlyContinue
    Remove-Item .\build -Recurse -Force -ErrorAction SilentlyContinue
    Remove-Item .\why_blame.egg-info -Recurse -Force -ErrorAction SilentlyContinue
    Write-Success "Build artifacts were removed."
}