#!/usr/bin/env pwsh

<#
.SYNOPSIS
Compares code coverage percent of local coverage.xml file to main branch
(Azure Pipeline API).

.PARAMETER wd
The working directory in which to search for current coverage.xml.

.PARAMETER org
Name of the Azure DevOps organization where the pipeline is hosted.

.PARAMETER project
Name of the Azure DevOps project to which the pipeline belongs.

.PARAMETER pipeline_name
Name of the desired pipeline within the project. This is to support projects
with multiple pipelines.
#>


# ---- SETUP -------------------------------------------------------------------


param(
    [string] $wd = (Get-Item (Split-Path $PSCommandPath -Parent)).Parent,
    [string] $org = "coderedcorp",
    [string] $project = "cr-github",
    [string] $pipeline_name = "wagtail-cache"
)

# Hide "UI" and progress bars.
$ProgressPreference = "SilentlyContinue"

# API setup.
$ApiBase = "https://dev.azure.com/$org/$project"


# ---- GET CODE COVERAGE FROM RECENT BUILD -------------------------------------

$mainBuildUrl = "$ApiBase/_apis/build/builds?branchName=refs/heads/main&api-version=5.1"
Write-Host "mainBuildUrl: $mainBuildUrl"

# Get list of all recent builds.
$mainBuildJson = (
    Invoke-WebRequest "$mainBuildUrl"
).Content | ConvertFrom-Json

# Get the latest matching build ID from the list of builds.
foreach ($build in $mainBuildJson.value) {
    if ($build.definition.name -eq $pipeline_name) {
        $mainLatestId = $build.id
        break
    }
}

$mainCoverageUrl = "$ApiBase/_apis/test/codecoverage?buildId=$mainLatestId&flags=7&api-version=7.1"
Write-Host "mainCoverageUrl: $mainCoverageUrl"

if($mainLatestId -eq $null) {
    Write-Host "No main coverage, build may have been cleaned up"
    exit 0
}

# Retrieve code coverage for this build ID.
$mainCoverageJson = (
    Invoke-WebRequest $mainCoverageUrl
).Content | ConvertFrom-Json
foreach ($cov in $mainCoverageJson.coverageData.coverageStats) {
    if ($cov.label -eq "Lines") {
        $mainlinerate = [math]::Round(($cov.covered / $cov.total) * 100, 2)
    }
}


# ---- GET COVERAGE FROM LOCAL RUN ---------------------------------------------


# Get current code coverage from coverage.xml file.
# Use the first one, if there are multiple i.e. from multiple runs.
$coveragePath = (Get-ChildItem -Recurse -Filter "coverage.xml" $wd)[0]
if (Test-Path -Path $coveragePath) {
    [xml]$BranchXML = Get-Content $coveragePath
}
else {
    Write-Host `
        "##vso[task.LogIssue type=warning;]No code coverage from this build. Is pytest configured to output code coverage?"
    exit 1
}
$branchlinerate = [math]::Round([decimal]$BranchXML.coverage.'line-rate' * 100, 2)


# ---- PRINT OUTPUT ------------------------------------------------------------


Write-Output ""
Write-Output "Main branch coverage rate:  $mainlinerate%"
Write-Output "This branch coverage rate:  $branchlinerate%"

if ($mainlinerate -eq 0) {
    $change = "Infinite"
}
else {
    $change = [math]::Abs($branchlinerate - $mainlinerate)
}

if ($branchlinerate -gt $mainlinerate) {
    Write-Host "Coverage increased by $change% 😀" -ForegroundColor Green
    exit 0
}
elseif ($branchlinerate -eq $mainlinerate) {
    Write-Host "Coverage has not changed." -ForegroundColor Green
    exit 0
}
elseif ($change -gt 2) {
    # Coverage measurements seem to be a bit flaky in azure pipelines and will
    # report changes within a few fractions of a percent even when there are no
    # changes. If coverage decreased by more than 2%, fail with error.
    Write-Host "##vso[task.LogIssue type=error;]Coverage decreased by $change% 😭"
    exit 1
}
else {
    # Write the error in a way that shows up as a warning in Azure Pipelines.
    Write-Host "##vso[task.LogIssue type=warning;]Coverage decreased by $change% 😭"
    exit 0
}
