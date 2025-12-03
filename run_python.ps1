param(
    [switch]$Silent,
    [switch]$VerboseMode,
    [switch]$SideBySide  # keep older versions instead of deleting them
)

# ============================================
# Logging helpers
# ============================================
$logPath = Join-Path $env:LOCALAPPDATA "PortablePython\log.txt"
function Write-Log {
    param([string]$Message)
    $timestamp = (Get-Date).ToString("yyyy-MM-dd HH:mm:ss")
    Add-Content -Encoding UTF8 -Path $logPath -Value "[$timestamp] $Message"
}

function Write-Status {
    param([string]$Message, [ConsoleColor]$Color = 'Gray')

    Write-Log $Message
    if (-not $Silent) {
        Write-Host $Message -ForegroundColor $Color
    }
}

function Compute-SHA256 {
    param([string]$Path)
    try { return (Get-FileHash -Algorithm SHA256 -Path $Path).Hash }
    catch {
        Write-Error "Failed to compute SHA256 for $Path"
        Write-Log "ERROR: SHA256 failed for $Path"
        return $null
    }
}

# ============================================
# Version parsing — supports old + new schemes
# ============================================
function Parse-PythonArchive {
    param([System.IO.FileInfo]$File)

    $name = $File.Name

    # NEW style: python3.12(.patch)-(arch).tar.gz
    if ($name -match '^python(\d+)\.(\d+)(?:\.(\d+))?(?:-(x64|arm64))?\.(tar\.gz|zip)$') {
        $major  = [int]$matches[1]
        $minor  = [int]$matches[2]
        $patch  = if ($matches[3]) { [int]$matches[3] } else { 0 }
        $arch   = if ($matches[4]) { $matches[4] } else { $env:PROCESSOR_ARCHITECTURE }
        $format = $matches[5]
    }
    # OLD style: python312(.patch)-(arch).zip
    elseif ($name -match '^python(\d{1})(\d{2})(?:\.(\d+))?(?:-(x64|arm64))?\.(tar\.gz|zip)$') {
        $major  = [int]$matches[1]
        $minor  = [int]$matches[2]
        $patch  = if ($matches[3]) { [int]$matches[3] } else { 0 }
        $arch   = if ($matches[4]) { $matches[4] } else { $env:PROCESSOR_ARCHITECTURE }
        $format = $matches[5]
    }
    else {
        return $null
    }

    # Normalize architecture into x64 or arm64
    if ($arch -match 'AMD64|x86_64|x64') { $arch = 'x64' }
    elseif ($arch -match 'ARM64|aarch64') { $arch = 'arm64' }

    # Numeric sort key: major.minor.patch.arch
    $archKey = if ($arch -eq 'x64') { 1 } else { 0 }
    $sortKey = ($major * 1e8) + ($minor * 1e4) + ($patch * 10) + $archKey

    return [PSCustomObject]@{
        FilePath      = $File.FullName
        FileName      = $File.Name
        BaseName      = $File.BaseName
        Major         = $major
        Minor         = $minor
        Patch         = $patch
        Arch          = $arch
        SortKey       = $sortKey
        VersionString = "$major.$minor.$patch-$arch"
        Format        = $format
    }
}

# ============================================
# Locate archives
# ============================================
$scriptRoot = Split-Path -Parent $MyInvocation.MyCommand.Definition

$archiveFiles = Get-ChildItem $scriptRoot `
    -Include 'python*.zip', 'python*.tar.gz' -File

if (-not $archiveFiles) {
    Write-Error "No python*.zip or python*.tar.gz archives found."
    exit 1
}

# Parse versions
$parsedArchives = foreach ($file in $archiveFiles) { Parse-PythonArchive $file }
$parsedArchives = $parsedArchives | Where-Object { $_ -ne $null }

if (-not $parsedArchives) {
    Write-Error "No valid Python version archives found."
    exit 1
}

# Choose newest version matching current architecture
$archWanted = if ($env:PROCESSOR_ARCHITECTURE -match 'ARM64') { 'arm64' } else { 'x64' }

$latest = $parsedArchives |
    Where-Object { $_.Arch -eq $archWanted } |
    Sort-Object SortKey -Descending |
    Select-Object -First 1

if (-not $latest) {
    Write-Error "No archives found matching architecture $archWanted."
    exit 1
}

$version = $latest.VersionString
$archivePath = $latest.FilePath

# ============================================
# Local AppData installation target
# ============================================
$basePath = Join-Path $env:LOCALAPPDATA 'PortablePython'
$destPath = Join-Path $basePath $version
$pythonExe = Join-Path $destPath 'python.exe'

$currentVerFile = Join-Path $basePath 'current_version.txt'
$lastKnownGood = Join-Path $basePath 'last_known_good.txt'

# Ensure base folder exists
if (-not (Test-Path $basePath)) {
    New-Item -ItemType Directory -Path $basePath | Out-Null
}

# ============================================
# SHA256 verification (GNU format)
# ============================================
$shaFile = $archivePath + '.sha256'
if (Test-Path $shaFile) {
    Write-Status "[PortablePython] Validating SHA256..."

    $line = Get-Content $shaFile | Select-Object -First 1
    $expectedHash = ($line -split '\s+')[0]
    $actualHash = Compute-SHA256 $archivePath

    if ($actualHash -ne $expectedHash) {
        Write-Error "SHA256 mismatch for $($latest.FileName)"
        exit 1
    }
}

# ============================================
# Determine if extraction is needed
# ============================================
$hasFolder = Test-Path $destPath
$hasExe = Test-Path $pythonExe
$installedVersion = if (Test-Path $currentVerFile) { (Get-Content $currentVerFile).Trim() } else { '' }

$shouldExtract =
    -not $hasFolder -or
    -not $hasExe -or
    ($installedVersion -ne $version)

if ($shouldExtract) {

    Write-Status "[PortablePython] Installing Python $version..." -Color Cyan

    # Save rollback state
    if ($hasExe) {
        Set-Content $lastKnownGood $installedVersion
        Write-Status "Saved last known good version: $installedVersion"
    }

    # Remove old installs if not side-by-side
    if (-not $SideBySide) {
        $folders = Get-ChildItem -Directory $basePath |
            Where-Object { $_.Name -ne $version -and $_.Name -ne 'PortablePython' }
        foreach ($f in $folders) {
            Write-Status "Removing older: $($f.Name)"
            Remove-Item -Recurse -Force $f.FullName
        }
    }

    if ($hasFolder) {
        Remove-Item -Recurse -Force $destPath
    }

    Write-Status "Extracting $($latest.FileName)..."
    tar -xf $archivePath -C $basePath

    if (-not (Test-Path $pythonExe)) {
        Write-Error "Extraction failed — python.exe missing."
        if (Test-Path $lastKnownGood) {
            $rollback = Get-Content $lastKnownGood
            Write-Status "Rolling back to $rollback..." -Color Yellow
        }
        exit 1
    }

    Set-Content $currentVerFile $version -Encoding ASCII
    Write-Status "Python $version installed." -Color Green
}
else {
    Write-Status "Using existing Python $version."
}

# ============================================
# Run Python
# ============================================
& $pythonExe @args
exit $LASTEXITCODE
