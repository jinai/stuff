param(
    [switch]$Silent,
    [switch]$VerboseMode,
    [switch]$SideBySide  # keep older versions instead of deleting them
)

# ============================================
# Logging
# ============================================
$basePath = Join-Path $env:LOCALAPPDATA 'PortablePython'
$logPath  = Join-Path $basePath 'log.txt'

function Write-Log {
    param([string]$Message)
    $ts = (Get-Date).ToString("yyyy-MM-dd HH:mm:ss")
    Add-Content -Encoding UTF8 -Path $logPath -Value "[$ts] $Message"
}

function Write-Status {
    param([string]$Message, [ConsoleColor]$Color = 'Gray')
    Write-Log $Message
    if (-not $Silent) { Write-Host $Message -ForegroundColor $Color }
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
# Normalize archive filenames to Uppercase P
# python3.12.1.tar.gz → Python3.12.1.tar.gz
# ============================================
$scriptRoot = Split-Path -Parent $MyInvocation.MyCommand.Definition

$archivesRaw = Get-ChildItem $scriptRoot -Include 'python*.zip','python*.tar.gz','Python*.zip','Python*.tar.gz' -File

foreach ($file in $archivesRaw) {
    if ($file.Name -cmatch '^python') {
        $newName = 'P' + $file.Name.Substring(1)
        Rename-Item -Path $file.FullName -NewName $newName
        Write-Status "Renamed $($file.Name) → $newName"
    }
}

# Refresh listing after rename
$archiveFiles = Get-ChildItem $scriptRoot -Include 'Python*.zip','Python*.tar.gz' -File

if (-not $archiveFiles) {
    Write-Error "No Python*.zip or Python*.tar.gz archives found."
    exit 1
}

# ============================================
# Version parsing — NEW + OLD SCHEMES
# Supports:
#   Python3.12(.patch).zip
#   Python312(.patch).tar.gz
# ============================================
function Parse-PythonArchive {
    param([System.IO.FileInfo]$File)

    $name = $File.Name

    # NEW scheme: Python3.12(.patch).tar.gz
    if ($name -imatch '^Python(\d+)\.(\d+)(?:\.(\d+))?\.(tar\.gz|zip)$') {
        $major = [int]$matches[1]
        $minor = [int]$matches[2]
        $patch = if ($matches[3]) { [int]$matches[3] } else { 0 }
        $format = $matches[4]
    }
    # OLD scheme: Python312(.patch).zip
    elseif ($name -imatch '^Python(\d{1})(\d{2})(?:\.(\d+))?\.(tar\.gz|zip)$') {
        $major = [int]$matches[1]
        $minor = [int]$matches[2]
        $patch = if ($matches[3]) { [int]$matches[3] } else { 0 }
        $format = $matches[4]
    }
    else { return $null }

    $sortKey = ($major * 1e6) + ($minor * 1e3) + $patch

    return [PSCustomObject]@{
        FilePath      = $File.FullName
        FileName      = $File.Name
        Major         = $major
        Minor         = $minor
        Patch         = $patch
        SortKey       = $sortKey
        VersionString = "$major.$minor.$patch"
        Format        = $format
    }
}

# ============================================
# Parse archives
# ============================================
$parsedArchives = foreach ($f in $archiveFiles) { Parse-PythonArchive $f }
$parsedArchives = $parsedArchives | Where-Object { $_ -ne $null }

if (-not $parsedArchives) {
    Write-Error "No valid Python archives found."
    exit 1
}

# ============================================
# Per-project version pinning via .python-version
# Searches current directory and parents
# ============================================
function Find-VersionFile {
    $p = (Get-Location).Path
    while ($p -ne [System.IO.Path]::GetPathRoot($p)) {
        $vf = Join-Path $p ".python-version"
        if (Test-Path $vf) { return $vf }
        $p = Split-Path $p -Parent
    }
    return $null
}

$versionFile = Find-VersionFile
$requestedVersion = $null

if ($versionFile) {
    $requestedVersion = (Get-Content $versionFile).Trim()
    Write-Status "Version pinned by .python-version → $requestedVersion"
}

# ============================================
# Choose correct version:
#   If pinned → find match
#   Else → latest available
# ============================================
if ($requestedVersion) {

    $parts = $requestedVersion.Split('.')

    if ($parts.Length -eq 2) {
        $reqMajor = [int]$parts[0]
        $reqMinor = [int]$parts[1]

        $matching = $parsedArchives |
            Where-Object { $_.Major -eq $reqMajor -and $_.Minor -eq $reqMinor } |
            Sort-Object Patch -Descending |
            Select-Object -First 1

        if (-not $matching) {
            Write-Error "Requested version $requestedVersion not available."
            exit 1
        }

        $latest = $matching
    }
    elseif ($parts.Length -eq 3) {
        $reqMajor = [int]$parts[0]
        $reqMinor = [int]$parts[1]
        $reqPatch = [int]$parts[2]

        $matching = $parsedArchives |
            Where-Object { $_.VersionString -eq "$reqMajor.$reqMinor.$reqPatch" } |
            Select-Object -First 1

        if (-not $matching) {
            Write-Error "Requested version $requestedVersion not available."
            exit 1
        }

        $latest = $matching
    }
    else {
        Write-Error ".python-version must contain either MAJOR.MINOR or MAJOR.MINOR.PATCH"
        exit 1
    }

} else {
    $latest = $parsedArchives | Sort-Object SortKey -Descending | Select-Object -First 1
}

$version     = $latest.VersionString
$archivePath = $latest.FilePath

# ============================================
# Installation folder (ALWAYS Uppercase Python)
# ============================================
$destFolderName = "Python$version"
$destPath       = Join-Path $basePath $destFolderName
$pythonExe      = Join-Path $destPath "python.exe"

$currentVerFile = Join-Path $basePath 'current_version.txt'
$lastKnownGood  = Join-Path $basePath 'last_known_good.txt'

# Ensure base folder exists
if (-not (Test-Path $basePath)) {
    New-Item -ItemType Directory -Path $basePath | Out-Null
}

# ============================================
# SHA256 validation (GNU-style)
# ============================================
$shaFile = $archivePath + '.sha256'
if (Test-Path $shaFile) {
    Write-Status "Validating SHA256..."

    $line = Get-Content $shaFile | Select-Object -First 1
    $expectedHash = ($line -split '\s+')[0]
    $actualHash = Compute-SHA256 $archivePath

    if ($actualHash -ne $expectedHash) {
        Write-Error "SHA256 mismatch!"
        exit 1
    }
}

# ============================================
# Should we extract?
# ============================================
$installed = if (Test-Path $currentVerFile) { (Get-Content $currentVerFile).Trim() } else { "" }

$shouldExtract =
    -not (Test-Path $destPath) -or
    -not (Test-Path $pythonExe) -or
    ($installed -ne $version)

# ============================================
# Install or reuse
# ============================================
if ($shouldExtract) {

    Write-Status "Installing Python $version..." -Color Cyan

    if (Test-Path $pythonExe) {
        Set-Content $lastKnownGood $installed
        Write-Status "Saved last-known-good version: $installed"
    }

    if (-not $SideBySide) {
        $older = Get-ChildItem $basePath -Directory |
            Where-Object { $_.Name -ne $destFolderName }
        foreach ($o in $older) {
            Write-Status "Removing old: $($o.Name)"
            Remove-Item -Recurse -Force $o.FullName
        }
    }

    if (Test-Path $destPath) {
        Remove-Item -Recurse -Force $destPath
    }

    Write-Status "Extracting $($latest.FileName)..."
    tar -xf $archivePath -C $basePath

    if (-not (Test-Path $pythonExe)) {
        Write-Error "Extraction failed — python.exe missing."
        exit 1
    }

    Set-Content $currentVerFile $version -Encoding ASCII
    Write-Status "Python $version installed." -Color Green

} else {
    Write-Status "Using existing Python $version."
}

# ============================================
# Run Python
# ============================================
& $pythonExe @args
exit $LASTEXITCODE
