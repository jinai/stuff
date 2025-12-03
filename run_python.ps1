param(
    [switch]$Silent,
    [switch]$SideBySide
)

# ============================================
# Logging setup
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
    if (-not $Silent) {
        Write-Host $Message -ForegroundColor $Color
    }
}

function Compute-SHA256 {
    param([string]$Path)
    try {
        return (Get-FileHash -Algorithm SHA256 -Path $Path).Hash
    }
    catch {
        Write-Error "Failed to compute SHA256 for $Path"
        Write-Log "ERROR: SHA256 failed for $Path"
        return $null
    }
}

# ============================================
# Normalize archive filenames to Uppercase-P
# ============================================
$scriptRoot = Split-Path -Parent $MyInvocation.MyCommand.Definition

$archivesRaw = Get-ChildItem $scriptRoot `
    -Include 'python*.zip','python*.tar.gz','Python*.zip','Python*.tar.gz' -File

foreach ($file in $archivesRaw) {
    if ($file.Name -cmatch '^python') {
        $newName = 'P' + $file.Name.Substring(1)
        Rename-Item -LiteralPath $file.FullName -NewName $newName
        Write-Status "Renamed $($file.Name) → $newName"
    }
}

# Refresh listing after renames
$archiveFiles = Get-ChildItem $scriptRoot `
    -Include 'Python*.zip','Python*.tar.gz' -File

if (-not $archiveFiles) {
    Write-Error "No Python*.zip or Python*.tar.gz archives found."
    exit 1
}

# ============================================
# Version parsing (NEW + OLD schemes)
# ============================================
function Parse-PythonArchive {
    param([System.IO.FileInfo]$File)

    $name = $File.Name

    # NEW scheme: Python3.12(.patch).zip
    if ($name -imatch '^Python(\d+)\.(\d+)(?:\.(\d+))?\.(tar\.gz|zip)$') {
        $major  = [int]$matches[1]
        $minor  = [int]$matches[2]
        $patch  = if ($matches[3]) { [int]$matches[3] } else { 0 }
        $format = $matches[4]
    }
    # OLD scheme: Python312(.patch).zip
    elseif ($name -imatch '^Python(\d{1})(\d{2})(?:\.(\d+))?\.(tar\.gz|zip)$') {
        $major  = [int]$matches[1]
        $minor  = [int]$matches[2]
        $patch  = if ($matches[3]) { [int]$matches[3] } else { 0 }
        $format = $matches[4]
    }
    else {
        return $null
    }

    # Sort key major.minor.patch
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
$parsedArchives = foreach ($f in $archiveFiles) {
    Parse-PythonArchive -File $f
}

$parsedArchives = $parsedArchives | Where-Object { $_ -ne $null }

if (-not $parsedArchives) {
    Write-Error "No valid Python archives found."
    exit 1
}

# ============================================
# Per-project version pinning via .python-version
# Searches current directory and ancestors
# ============================================
function Find-VersionFile {
    $path = (Get-Location).Path
    $root = [System.IO.Path]::GetPathRoot($path)

    while ($true) {
        $vf = Join-Path $path ".python-version"
        if (Test-Path $vf) {
            return $vf
        }

        if ($path -eq $root) {
            break
        }

        $path = Split-Path $path -Parent
    }

    return $null
}

$versionFile = Find-VersionFile
$requestedVersion = $null

if ($versionFile) {
    $requestedVersion = (Get-Content -LiteralPath $versionFile).Trim()
    Write-Status "Version pinned by .python-version → $requestedVersion"
}

# ============================================
# Choose correct version:
#   If pinned → find matching version
#   Else → latest version available
# ============================================
if ($requestedVersion) {

    $parts = $requestedVersion.Split('.')

    # Format: MAJOR.MINOR → choose highest patch
    if ($parts.Length -eq 2) {
        $reqMajor = [int]$parts[0]
        $reqMinor = [int]$parts[1]

        $latest = $parsedArchives |
            Where-Object { $_.Major -eq $reqMajor -and $_.Minor -eq $reqMinor } |
            Sort-Object Patch -Descending |
            Select-Object -First 1

        if (-not $latest) {
            Write-Error "Requested version $requestedVersion not available."
            exit 1
        }
    }
    # Format: MAJOR.MINOR.PATCH → require exact match
    elseif ($parts.Length -eq 3) {
        $reqMajor = [int]$parts[0]
        $reqMinor = [int]$parts[1]
        $reqPatch = [int]$parts[2]

        $latest = $parsedArchives |
            Where-Object { $_.VersionString -eq "$reqMajor.$reqMinor.$reqPatch" } |
            Select-Object -First 1

        if (-not $latest) {
            Write-Error "Requested version $requestedVersion not available."
            exit 1
        }
    }
    else {
        Write-Error ".python-version must be MAJOR.MINOR or MAJOR.MINOR.PATCH"
        exit 1
    }

}
else {
    # Default to newest archive available
    $latest = $parsedArchives |
        Sort-Object SortKey -Descending |
        Select-Object -First 1
}

$version     = $latest.VersionString
$archivePath = $latest.FilePath

# ============================================
# Installation folder (Always "PythonX.Y.Z")
# ============================================
$destFolderName = "Python$version"
$destPath       = Join-Path $basePath $destFolderName
$pythonExe      = Join-Path $destPath "python.exe"

$currentVerFile = Join-Path $basePath 'current_version.txt'
$lastKnownGood  = Join-Path $basePath 'last_known_good.txt'

# Ensure base directory exists
if (-not (Test-Path -LiteralPath $basePath)) {
    New-Item -ItemType Directory -Path $basePath | Out-Null
}

# ============================================
# SHA256 validation (optional)
# ============================================
$shaFile = $archivePath + '.sha256'

if (Test-Path -LiteralPath $shaFile) {
    Write-Status "Validating SHA256..."

    $line = Get-Content -LiteralPath $shaFile | Select-Object -First 1
    $expectedHash = ($line -split '\s+')[0]
    $actualHash   = Compute-SHA256 -Path $archivePath

    if ($actualHash -ne $expectedHash) {
        Write-Error "SHA256 mismatch for archive $($latest.FileName)"
        exit 1
    }
}

# ============================================
# Determine if extraction is required
# ============================================
$installedVersion = if (Test-Path -LiteralPath $currentVerFile) {
    (Get-Content -LiteralPath $currentVerFile).Trim()
}
else {
    ""
}

$shouldExtract =
    (-not (Test-Path -LiteralPath $destPath)) -or
    (-not (Test-Path -LiteralPath $pythonExe)) -or
    ($installedVersion -ne $version)

# ============================================
# Perform installation if needed
# ============================================
if ($shouldExtract) {

    Write-Status "Installing Python $version..." -Color Cyan

    # Save rollback reference if existing install is present
    if (Test-Path -LiteralPath $pythonExe) {
        Set-Content -LiteralPath $lastKnownGood -Value $installedVersion -Encoding ASCII
        Write-Status "Saved last-known-good version: $installedVersion"
    }

    # Remove older installs unless side-by-side mode is enabled
    if (-not $SideBySide) {
        $existingFolders = Get-ChildItem -LiteralPath $basePath -Directory |
            Where-Object { $_.Name -ne $destFolderName }

        foreach ($folder in $existingFolders) {
            Write-Status "Removing old install: $($folder.Name)"
            Remove-Item -LiteralPath $folder.FullName -Recurse -Force
        }
    }

    # Remove partial/broken previous extraction
    if (Test-Path -LiteralPath $destPath) {
        Remove-Item -LiteralPath $destPath -Recurse -Force
    }

    Write-Status "Extracting $($latest.FileName)..."

    try {
        tar -xf $archivePath -C $basePath
    }
    catch {
        Write-Error "Extraction failed — tar reported an error."
        exit 1
    }

    # Validate extraction
    if (-not (Test-Path -LiteralPath $pythonExe)) {
        Write-Error "Extraction failed — python.exe not found in extracted folder."

        if (Test-Path -LiteralPath $lastKnownGood) {
            $rollbackVersion = (Get-Content -LiteralPath $lastKnownGood).Trim()
            Write-Status "Rolling back to $rollbackVersion..." -Color Yellow
        }

        exit 1
    }

    # Update current version marker
    Set-Content -LiteralPath $currentVerFile -Value $version -Encoding ASCII
    Write-Status "Python $version installed successfully." -Color Green
}
else {
    Write-Status "Using existing Python $version."
}

# ============================================
# Run Python with forwarded arguments
# ============================================
Write-Status "Launching Python $version..."

& $pythonExe @args
$exitCode = $LASTEXITCODE

exit $exitCode
