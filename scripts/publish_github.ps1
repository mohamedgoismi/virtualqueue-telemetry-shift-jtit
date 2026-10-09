# Requires an EXISTING GitHub public repository and local Git authentication.
# Usage: .\scripts\publish_github.ps1 -GitHubUser YOUR_ACCOUNT
param(
    [Parameter(Mandatory=$true)] [string]$GitHubUser,
    [string]$Repository = 'virtualqueue-telemetry-shift-jtit'
)
$ErrorActionPreference = 'Stop'
Set-Location (Split-Path -Parent $PSScriptRoot)
$remote = 'https://github.com/' + $GitHubUser + '/' + $Repository + '.git'
Write-Host 'Repository: ' $remote
Write-Host 'Please review CITATION.cff, AUTHORS.md and LICENSE before publishing.'
$answer = Read-Host 'Confirm publication of the current directory? Type YES'
if ($answer -cne 'YES') { Write-Host 'Cancelled'; exit 1 }
if (-not (Test-Path '.git')) { git init }
git branch -M main
git add .
git diff --cached --quiet
if ($LASTEXITCODE -ne 0) { git commit -m 'Initial synthetic FIFO research software release candidate' }
git remote get-url origin 2>$null
if ($LASTEXITCODE -ne 0) { git remote add origin $remote } else { git remote set-url origin $remote }
git push -u origin main
Write-Host ('Published at https://github.com/' + $GitHubUser + '/' + $Repository)
Write-Host 'Now enable this repository in Zenodo BEFORE publishing GitHub release v0.1.0.'
