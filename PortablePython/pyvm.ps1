#!/usr/bin/env pwsh
<#
    pyvm.ps1 — Portable Python Version Manager
    Side-by-side installs, project & global version selection,
    archive auto-install, python/pythonw execution engine,
    listing commands, and patch auto-upgrade.
#>

param(
    [string]$GlobalVersion,    # for: pyvm --global X.Y.Z
    [switch]$List,             # for: pyvm --list
    [switch]$Versions,         # for: pyvm --versions
    [switch]$Windowed,         # for: pyvm --windowed
    [Parameter(ValueFromRemainingArguments = $true)]
    [string[]]$Args            # script + args
)

# ============================================
# GLOBAL CONFIGURATION
# ============================================
$BasePath      = Join-Path $env:LOCALAPPDATA 'PortablePython'
$InstallsPath  = $BasePath
$ArchivePath1  = Split-Path -Parent $MyInvocation.MyCommand.Definition
$ArchivePath2  = Join-Path $BasePath 'archives'

# Ensure required folders exist
foreach ($p in @($BasePath, $ArchivePath2)) {
    if (-not (Test-Path $p)) {
        New-Item -ItemType Directory -Path $p | Out-Null
    }
}

$GlobalVersionFile = Join-Path $BasePath '.global-python-version'
$LogFile           = Join-Path $BasePath 'pyvm.log'

# ============================================
# LOGGING HELPER
# ============================================
function Log {
    param([string]$Message)
    $ts = (Get-Date).ToString('yyyy-MM-dd HH:mm:ss')
    Add-Content -LiteralPath $LogFile -Value "[$ts] $Message"
}

# ============================================
# UI OUTPUT (Write-Host for end user)
# ============================================
function Say {
    param(
        [string]$Msg,
        [string]$Color = 'Gray'
    )
    Log $Msg
    Write-Host $Msg -ForegroundColor $Color
}

# ============================================
# VERSION OBJECT CREATION
# ============================================
function Make-VersionObject {
    param(
        [string]$Version,   # e.g. '3.13.1'
        [string]$Path,      # install or archive full path
        [string]$Type       # 'installed' or 'archive'
    )

    # Version sort key: major.minor.patch = big sortable int
    $parts = $Version.Split('.') | ForEach-Object { [int]$_ }
    $sortKey = ($parts[0] * 1e6) + ($parts[1] * 1e3) + $parts[2]

    return [PSCustomObject]@{
        Version = $Version
        Path    = $Path
        Type    = $Type
        SortKey = $sortKey
    }
}

# ============================================
# NORMALIZE VERSION STRING
# Input:  '3.13' → @(3,13,0)
#         '3.13.1' → @(3,13,1)
# ============================================
function Normalize-Version {
    param([string]$v)

    if (-not $v) { return $null }

    $parts = $v.Split('.')
    if ($parts.Count -lt 2 -or $parts.Count -gt 3) {
        return $null
    }

    $major = [int]$parts[0]
    $minor = [int]$parts[1]
    $patch = if ($parts.Count -eq 3) { [int]$parts[2] } else { 0 }

    return @($major, $minor, $patch)
}

# ============================================
# PARSE ARCHIVE FILENAMES → VERSION OBJECT
#
# Supported:
#   Python3.13.1.zip
#   Python3.13.1.tar.gz
#   python3.13.1.tar.gz → renamed to Python3.13.1
#   Python312.zip
#   Python312.1.zip
# ============================================
function Parse-ArchiveFilename {
    param(
        [string]$Name,
        [string]$FullPath
    )

    # Normalize python → Python
    if ($Name -cmatch '^python') {
        $Name = 'P' + $Name.Substring(1)
    }

    # Pattern: Python3.13.1.zip or Python3.13.1.tar.gz
    if ($Name -imatch '^Python(\d+)\.(\d+)\.(\d+)\.(zip|tar\.gz)$') {
        $v = "$($matches[1]).$($matches[2]).$($matches[3])"
        return Make-VersionObject -Version $v -Path $FullPath -Type 'archive'
    }

    # Old-style: Python312.zip or Python312.1.zip
    if ($Name -imatch '^Python(\d{1})(\d{2})(?:\.(\d+))?\.(zip|tar\.gz)$') {
        $major = [int]$matches[1]
        $minor = [int]$matches[2]
        $patch = if ($matches[3]) { [int]$matches[3] } else { 0 }
        $v = "$major.$minor.$patch"
        return Make-VersionObject -Version $v -Path $FullPath -Type 'archive'
    }

    return $null
}

# ============================================
# PARSE INSTALLED FOLDER NAME → VERSION OBJECT
# Folders: Python3.13.0
# ============================================
function Parse-InstalledFolder {
    param(
        [string]$Name,
        [string]$FullPath
    )

    if ($Name -imatch '^Python(\d+)\.(\d+)\.(\d+)$') {
        $v = "$($matches[1]).$($matches[2]).$($matches[3])"
        return Make-VersionObject -Version $v -Path $FullPath -Type 'installed'
    }

    return $null
}

# ============================================
# FIND NEAREST .python-version IN PARENT TREE
# ============================================
function Find-ProjectVersionFile {
    $path = (Get-Location).Path
    $root = [System.IO.Path]::GetPathRoot($path)

    while ($true) {
        $test = Join-Path $path '.python-version'
        if (Test-Path $test) {
            return $test
        }

        if ($path -eq $root) {
            break
        }

        $path = Split-Path $path -Parent
    }

    return $null
}

# ============================================
# FIND ARCHIVES (IN LOCAL FOLDER + CENTRAL ARCHIVE)
# ============================================
function Find-Archives {

    $archives = @()

    $localPattern   = Join-Path $ArchivePath1 '*'
    $centralPattern = Join-Path $ArchivePath2 '*'

    $localFiles = @()
    $centralFiles = @()

    if (Test-Path $localPattern) {
        $localFiles = Get-ChildItem -Path $localPattern -File |
            Where-Object { $_.Name -imatch '^Python.*\.(zip|tar\.gz)$' -or $_.Name -imatch '^python.*\.(zip|tar\.gz)$' }
    }

    if (Test-Path $centralPattern) {
        $centralFiles = Get-ChildItem -Path $centralPattern -File |
            Where-Object { $_.Name -imatch '^Python.*\.(zip|tar\.gz)$' -or $_.Name -imatch '^python.*\.(zip|tar\.gz)$' }
    }

    foreach ($f in @($localFiles + $centralFiles)) {

        # Normalize python → Python
        if ($f.Name -cmatch '^python') {
            $newName = 'P' + $f.Name.Substring(1)
            $newFull = Join-Path $f.DirectoryName $newName
            Rename-Item -LiteralPath $f.FullName -NewName $newName
            $f = Get-Item -LiteralPath $newFull
        }

        $parsed = Parse-ArchiveFilename -Name $f.Name -FullPath $f.FullName
        if ($parsed) {
            $archives += $parsed
        }
    }

    return $archives
}

# ============================================
# FIND INSTALLED VERSIONS
# ============================================
function Find-Installed {

    $installed = @()

    if (-not (Test-Path $InstallsPath)) {
        return $installed
    }

    $folders = Get-ChildItem -Path $InstallsPath -Directory |
        Where-Object { $_.Name -imatch '^Python\d+\.\d+\.\d+$' }

    foreach ($folder in $folders) {
        $parsed = Parse-InstalledFolder -Name $folder.Name -FullPath $folder.FullName
        if ($parsed) {
            $installed += $parsed
        }
    }

    return $installed
}

# ============================================
# FIND HIGHEST PATCH VERSION MATCHING MAJOR.MINOR
# Searches both installed + archives
# ============================================
function Find-HighestPatchMatching {
    param(
        [int]$Major,
        [int]$Minor,
        [array]$InstalledVersions,
        [array]$ArchiveVersions
    )

    $matches = @()

    foreach ($v in $InstalledVersions + $ArchiveVersions) {
        $parts = $v.Version.Split('.') | ForEach-Object { [int]$_ }
        if ($parts[0] -eq $Major -and $parts[1] -eq $Minor) {
            $matches += $v
        }
    }

    if ($matches.Count -eq 0) {
        return $null
    }

    return ($matches | Sort-Object SortKey -Descending)[0]
}

# ============================================
# VERSION SELECTION LOGIC
# PRIORITY:
#   1) Project version (.python-version)
#   2) Global version
#   3) Latest installed
#   4) Latest archive (to install)
# ============================================
function Select-Version {
    param(
        [array]$Installed,
        [array]$Archives,
        [array]$ProjectVersionNorm,
        [array]$GlobalVersionNorm
    )

    # ----------------------------------------
    # 1. PROJECT VERSION
    # ----------------------------------------
    if ($ProjectVersionNorm) {

        $major = $ProjectVersionNorm[0]
        $minor = $ProjectVersionNorm[1]
        $patch = $ProjectVersionNorm[2]

        if ($patch -gt 0) {
            # Exact patch requested
            $exactInstalled = $Installed | Where-Object { $_.Version -eq "$major.$minor.$patch" }
            if ($exactInstalled) { return $exactInstalled[0] }

            $exactArchive = $Archives | Where-Object { $_.Version -eq "$major.$minor.$patch" }
            if ($exactArchive) { return $exactArchive[0] }

            throw "Requested version $major.$minor.$patch not installed and no archive found."
        }

        # MAJOR.MINOR only → auto-upgrade to highest patch
        $best = Find-HighestPatchMatching -Major $major -Minor $minor -Installed $Installed -Archive $Archives
        if ($best) { return $best }

        throw "Requested Python $major.$minor not installed and no archive found."
    }

    # ----------------------------------------
    # 2. GLOBAL VERSION
    # ----------------------------------------
    if ($GlobalVersionNorm) {

        $major = $GlobalVersionNorm[0]
        $minor = $GlobalVersionNorm[1]
        $patch = $GlobalVersionNorm[2]

        if ($patch -gt 0) {
            $exactInstalled = $Installed | Where-Object { $_.Version -eq "$major.$minor.$patch" }
            if ($exactInstalled) { return $exactInstalled[0] }

            $exactArchive = $Archives | Where-Object { $_.Version -eq "$major.$minor.$patch" }
            if ($exactArchive) { return $exactArchive[0] }

            throw "Requested global Python $major.$minor.$patch not installed and no archive found."
        }

        $best = Find-HighestPatchMatching -Major $major -Minor $minor -Installed $Installed -Archive $Archives
        if ($best) { return $best }

        throw "Requested global Python $major.$minor not installed and no archive found."
    }

    # ----------------------------------------
    # 3. NO PROJECT OR GLOBAL → USE LATEST INSTALLED
    # ----------------------------------------
    if ($Installed.Count -gt 0) {
        return ($Installed | Sort-Object SortKey -Descending)[0]
    }

    # ----------------------------------------
    # 4. NO INSTALLED → USE LATEST ARCHIVE
    # ----------------------------------------
    if ($Archives.Count -gt 0) {
        return ($Archives | Sort-Object SortKey -Descending)[0]
    }

    throw 'No Python versions installed and no archives available.'
}

# ============================================
# ENSURE A PYTHON VERSION IS INSTALLED
#
# If Selected.Type = 'installed' → return as-is.
# If Selected.Type = 'archive'   → extract it.
# ============================================
function Ensure-Installed {
    param(
        [PSCustomObject]$Selected,
        [string]$InstallsPath
    )

    if ($Selected.Type -eq 'installed') {
        return $Selected
    }

    $version  = $Selected.Version
    $destName = "Python$version"
    $destPath = Join-Path $InstallsPath $destName

    # ----------------------------------------
    # If folder exists but broken → delete it
    # ----------------------------------------
    if (Test-Path $destPath) {
        $pythonExe = Join-Path $destPath 'python.exe'
        if (Test-Path $pythonExe) {
            return Make-VersionObject -Version $version -Path $destPath -Type 'installed'
        }

        Say "Removing incomplete install: $destName" -Color Yellow
        Remove-Item -LiteralPath $destPath -Recurse -Force
    }

    # ----------------------------------------
    # Extract archive
    # ----------------------------------------
    Say "Installing Python $version..." -Color Cyan
    Log "Extracting archive: $($Selected.Path)"

    try {
        tar -xf $Selected.Path -C $InstallsPath
    }
    catch {
        Say "ERROR: Extraction failed for $($Selected.Path)" -Color Red
        exit 1
    }

    # ----------------------------------------
    # Validate installation
    # ----------------------------------------
    $pythonExe = Join-Path $destPath 'python.exe'
    if (-not (Test-Path $pythonExe)) {
        Say "ERROR: python.exe missing after extraction ($destPath)" -Color Red
        exit 1
    }

    Say "Installed Python $version" -Color Green
    return Make-VersionObject -Version $version -Path $destPath -Type 'installed'
}

# ============================================
# COMMAND: --global X.Y.Z
# Sets the global default version
# ============================================
if ($GlobalVersion) {
    Set-Content -LiteralPath $GlobalVersionFile -Value $GlobalVersion -Encoding ASCII
    Say "Set global Python version to $GlobalVersion" -Color Green
    exit 0
}

# ============================================
# COMMAND: --list
# List installed versions only
# ============================================
if ($List) {
    $sorted = $Installed | Sort-Object SortKey -Descending

    if ($sorted.Count -eq 0) {
        Write-Output 'No Python versions installed.'
        exit 0
    }

    Write-Output 'Installed Python versions:'
    foreach ($v in $sorted) {
        Write-Output "  $($v.Version)"
    }

    exit 0
}

# ============================================
# COMMAND: --versions
# List installed + available archives
# ============================================
if ($Versions) {

    $sortedInstalled = $Installed | Sort-Object SortKey -Descending
    $sortedArchives  = $Archives  | Sort-Object SortKey -Descending

    Write-Output 'Installed:'
    if ($sortedInstalled.Count -eq 0) {
        Write-Output '  (none)'
    }
    else {
        foreach ($v in $sortedInstalled) {
            Write-Output "  $($v.Version)"
        }
    }

    Write-Output ''
    Write-Output 'Available archives:'

    if ($sortedArchives.Count -eq 0) {
        Write-Output '  (none)'
        exit 0
    }

    foreach ($a in $sortedArchives) {

        # Newer patch marker (*)
        $aParts = $a.Version.Split('.') | ForEach-Object { [int]$_ }
        $aMajor = $aParts[0]
        $aMinor = $aParts[1]
        $aPatch = $aParts[2]

        $installedMatch = $Installed |
            Where-Object {
                $i = $_.Version.Split('.') | ForEach-Object { [int]$_ }
                ($i[0] -eq $aMajor) -and ($i[1] -eq $aMinor)
            } |
            Sort-Object SortKey -Descending |
            Select-Object -First 1

        $mark = ''
        if ($installedMatch) {
            $iParts = $installedMatch.Version.Split('.') | ForEach-Object { [int]$_ }
            if ($aPatch -gt $iParts[2]) {
                $mark = ' *'
            }
        }

        Write-Output "  $($a.Version)$mark"
    }

    exit 0
}

# ============================================
# EXECUTION ENGINE
# Select python.exe or pythonw.exe
# Run scripts or REPL
# Forward arguments
# ============================================

function Invoke-Python {
    param(
        [PSCustomObject]$Selected,
        [switch]$Windowed,
        [string[]]$Args
    )

    $pythonExe  = Join-Path $Selected.Path 'python.exe'
    $pythonWExe = Join-Path $Selected.Path 'pythonw.exe'

    if (-not (Test-Path $pythonExe)) {
        Say "ERROR: python.exe not found in $($Selected.Path)" -Color Red
        exit 1
    }

    # ----------------------------------------
    # Select the preferred interpreter
    # ----------------------------------------
    $exeToRun = $pythonExe   # default

    # 1) If first arg is a .pyw script → use pythonw
    if ($Args.Count -gt 0) {
        $first = $Args[0]
        if ($first -is [string] -and $first -match '\.pyw$') {
            $exeToRun = $pythonWExe
        }
    }

    # 2) --windowed forces pythonw.exe
    if ($Windowed) {
        $exeToRun = $pythonWExe
        # Remove --windowed from args
        $Args = $Args | Where-Object { $_ -ne '--windowed' }
    }

    # Validate pythonw if selected
    if (($exeToRun -eq $pythonWExe) -and (-not (Test-Path $pythonWExe))) {
        Say "ERROR: pythonw.exe not found in $($Selected.Path)" -Color Red
        exit 1
    }

    # ----------------------------------------
    # Interactive REPL if no script provided
    # ----------------------------------------
    $noScript = ($Args.Count -eq 0) -or ([string]::IsNullOrWhiteSpace($Args[0]))

    if ($noScript) {
        Say "Launching Python $($Selected.Version) (interactive REPL)..." -Color Cyan
        & $exeToRun
        exit $LASTEXITCODE
    }

    # ----------------------------------------
    # Run script normally
    # ----------------------------------------
    Say "Launching Python $($Selected.Version)..." -Color Cyan
    & $exeToRun @Args
    exit $LASTEXITCODE
}

# ============================================
# MAIN LOGIC
# ============================================

# Read project version
$ProjectVersion = $null
$pvFile = Find-ProjectVersionFile
if ($pvFile) {
    $ProjectVersion = (Get-Content -LiteralPath $pvFile).Trim()
}
$ProjectVersionNorm = Normalize-Version $ProjectVersion

# Read global version
$GlobalVersionValue = $null
if (Test-Path $GlobalVersionFile) {
    $GlobalVersionValue = (Get-Content -LiteralPath $GlobalVersionFile).Trim()
}
$GlobalVersionNorm = Normalize-Version $GlobalVersionValue

# Discover installed + archives
$Installed = Find-Installed
$Archives  = Find-Archives

# Select the correct version (project → global → installed → archive)
try {
    $Selected = Select-Version `
        -Installed $Installed `
        -Archives  $Archives `
        -ProjectVersionNorm $ProjectVersionNorm `
        -GlobalVersionNorm  $GlobalVersionNorm
}
catch {
    Say $_ -Color Red
    exit 1
}

# Ensure version is installed (extract if from archive)
$Selected = Ensure-Installed -Selected $Selected -InstallsPath $InstallsPath

# Execute Python (script or REPL)
Invoke-Python -Selected $Selected -Windowed:$Windowed -Args $Args
