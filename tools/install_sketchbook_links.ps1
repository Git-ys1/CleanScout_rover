param(
    [string]$RepoRoot = "",
    [string]$SketchbookLibraries = ""
)

if ([string]::IsNullOrWhiteSpace($RepoRoot)) {
    $RepoRoot = (Resolve-Path (Join-Path $PSScriptRoot "..")).Path
}

if ([string]::IsNullOrWhiteSpace($SketchbookLibraries)) {
    $SketchbookLibraries = Join-Path $env:USERPROFILE "Documents\Arduino\libraries"
}

function Resolve-ExactPath {
    param([string]$Path)

    return (Resolve-Path $Path).Path
}

function Get-LinkTargetPath {
    param([System.IO.FileSystemInfo]$Item)

    if (-not ($Item.Attributes -band [System.IO.FileAttributes]::ReparsePoint)) {
        return $null
    }

    $target = $Item.Target
    if ($null -eq $target) {
        return $null
    }

    if ($target -is [array]) {
        $target = $target[0]
    }

    try {
        return (Resolve-Path $target).Path
    } catch {
        return $null
    }
}

function Ensure-SketchbookLibrary {
    param(
        [hashtable]$Spec,
        [string]$LibrariesRoot
    )

    $sourcePath = Resolve-ExactPath $Spec.Source
    $targetPath = Join-Path $LibrariesRoot $Spec.Name

    if (Test-Path $targetPath) {
        $item = Get-Item $targetPath -Force
        $linkTarget = Get-LinkTargetPath $item

        if ($null -ne $linkTarget -and $linkTarget -eq $sourcePath) {
            Write-Host "Already linked: $targetPath -> $sourcePath"
            return
        }

        if (Test-Path (Join-Path $targetPath $Spec.Header)) {
            Write-Warning "Keeping existing sketchbook library: $targetPath"
            return
        }

        throw "Conflict: $targetPath exists and is not compatible with required library $($Spec.Name)."
    }

    New-Item -ItemType Junction -Path $targetPath -Target $sourcePath | Out-Null
    Write-Host "Linked: $targetPath -> $sourcePath"
}

$libraries = @(
    @{
        Name = "CleanScoutFan"
        Source = Join-Path $RepoRoot "libraries\CleanScoutFan"
        Header = "CleanScoutFan.h"
    },
    @{
        Name = "Tyler_1"
        Source = Join-Path $RepoRoot "libraries\Tyler_1"
        Header = "Tyler_1.h"
    },
    @{
        Name = "Adafruit-Motor-Shield-library-master"
        Source = Join-Path $RepoRoot "Adafruit-Motor-Shield-library-master"
        Header = "AFMotor.h"
    }
)

New-Item -ItemType Directory -Force $SketchbookLibraries | Out-Null

foreach ($library in $libraries) {
    if (-not (Test-Path $library.Source)) {
        throw "Required library source not found: $($library.Source)"
    }

    Ensure-SketchbookLibrary -Spec $library -LibrariesRoot $SketchbookLibraries
}

Write-Host "Sketchbook library setup finished."
