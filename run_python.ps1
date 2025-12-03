param(
    [switch]$VerboseMode,
    [switch]$Silent
)

# Begin helper function
function Write-Status {
    param([string]$Message, [ConsoleColor]$Color = 'Gray')
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
        return $null
    }
}

# Root directory
$rootPath = Split-Path -Parent $MyInvocation.MyCommand.Definition

# Look for python*.zip or python*.tar.gz
$archives = Get-ChildItem -Path $rootPath -Include 'python*.tar.gz', 'python*.zip', 'python*.sha256' -File
$pythonArchives = $archives | Where-Object { $_.Name -match '^python.*\.(zip|tar\.gz)$' }

if (-not $pythonArchives) {
    Write-Error 'No python*.zip or python*.tar.gz archives found.'
    exit 1
}

# Parse version numbers from filenames
$parsedArchives = foreach ($archive in $pythonArchives) {
    if ($archive.Name -match '^python(\d{3})(?:\.(\d+))?\.(tar\.gz|zip)$') {
        $majorMinor = [int]$matches[1]
        $patch = if ($matches[2]) { [int]$matches[2] } else { 0 }
        $format = $matches[3]

        [PSCustomObject]@{
            FilePath      = $archive.FullName
            FileName      = $archive.Name
            BaseName      = $archive.BaseName
            MajorMinor    = $majorMinor
            Patch         = $patch
            VersionString = "$majorMinor.$patch"
            Format        = $format
        }
    }
}

if (-not $parsedArchives) {
    Write-Error 'No valid versioned python archives found.'
    exit 1
}

# Pick highest version
$latest = $parsedArchives |
    Sort-Object -Property MajorMinor, Patch -Descending |
    Select-Object -First 1

$versionString = $latest.VersionString
$archivePath = $latest.FilePath
$destPath = Join-Path $rootPath "python$($latest.MajorMinor)"
$initFlagPath = Join-Path $rootPath ".initialized_$versionString"

# Optional SHA256 integrity check
$shaFile = $archivePath + '.sha256'
if (Test-Path $shaFile) {
    Write-Status "[PortablePython] Validating checksum for $($latest.FileName)..."

    $expectedHash = (Get-Content $shaFile).Trim()
    $actualHash = Compute-SHA256 -Path $archivePath

    if ($actualHash -ne $expectedHash) {
        Write-Error "Checksum mismatch for $($latest.FileName). Expected: $expectedHash, Got: $actualHash"
        exit 1
    }
}

# Determine if extraction is needed
$alreadyInitialized = Test-Path -Path $initFlagPath
$pythonFolderExists = Test-Path -Path $destPath

$shouldExtract = -not ($alreadyInitialized -and $pythonFolderExists)

# Detect partial/broken extraction (missing python.exe)
$pythonExe = Join-Path $destPath 'python.exe'
if ($pythonFolderExists -and (-not (Test-Path $pythonExe))) {
    Write-Status "[PortablePython] Detected broken extraction, re-extracting..." -Color Yellow
    $shouldExtract = $true
}

# Cleanup old versions (init flags + folders)
$existingFlags = Get-ChildItem -Path $rootPath -Filter '.initialized_*' -File
foreach ($flag in $existingFlags) {
    if ($flag.Name -ne ".initialized_$versionString") {
        Write-Status "[PortablePython] Removing old init flag: $($flag.Name)"
        Remove-Item -Path $flag.FullName -Force
    }
}

$existingFolders = Get-ChildItem -Path $rootPath -Directory |
    Where-Object { $_.Name -match '^python\d{3}$' -and $_.Name -ne "python$($latest.MajorMinor)" }

foreach ($folder in $existingFolders) {
    Write-Status "[PortablePython] Removing older Python folder: $($folder.Name)"
    Remove-Item -Recurse -Force -Path $folder.FullName
}

# Extraction logic
if ($shouldExtract) {

    Write-Status "[PortablePython] Preparing Python $versionString ..." -Color Cyan

    if (Test-Path -Path $destPath) {
        Write-Status "[PortablePython] Removing old folder: $destPath"
        Remove-Item -Recurse -Force -Path $destPath
    }

    Write-Status "[PortablePython] Extracting $($latest.FileName) ..."

    tar -xf $archivePath -C $rootPath

    # Integrity check: must contain python.exe
    if (-not (Test-Path $pythonExe)) {
        Write-Error "Extraction failed: python.exe not found in $destPath"
        exit 1
    }

    # Mark successful extraction
    New-Item -ItemType File -Path $initFlagPath | Out-Null
    Write-Status "[PortablePython] Python $versionString is ready." -Color Green
}
else {
    Write-Status "[PortablePython] Using existing Python $versionString."
}

# Run python
& $pythonExe @args
exit $LASTEXITCODE
