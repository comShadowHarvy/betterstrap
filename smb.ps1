#Requires -RunAsAdministrator
<#
.SYNOPSIS
    Mounts network shares, creates directories, and sets up symbolic links on Windows.
    This script is the Windows equivalent of the user's provided Linux bash script.
.DESCRIPTION
    1. Checks for Administrator privileges.
    2. Defines network shares and local mount points.
    3. Creates local directories for mounting (e.g., C:\mnt\*, C:\share, %USERPROFILE%\temp).
    4. Persistently maps the network shares using 'net use'.
    5. Creates symbolic links in the user's home folder and C:\share for easy access.
#>

# --- Configuration ---
# Define the SMB share entries and their local mount points
# NOTE: Update your credentials below!
$entries = @(
    @{ Remote = "\\192.168.1.210\media";  Local = "C:\mnt\hass_media";  User = "me";              Password = "Jbean343343343" },
    @{ Remote = "\\192.168.1.210\config"; Local = "C:\mnt\hass_config"; User = "me";              Password = "Jbean343343343" },
    @{ Remote = "\\192.168.1.210\share";  Local = "C:\mnt\hass_share";  User = "me";              Password = "Jbean343343343" },
    @{ Remote = "\\192.168.1.47\USB-Share"; Local = "C:\mnt\usb_share";   User = $null;            Password = $null }, # Guest access
    @{ Remote = "\\192.168.1.47\USB-Share-2"; Local = "C:\mnt\usb_share_2"; User = $null;            Password = $null }, # Guest access
    @{ Remote = "\\192.168.1.47\ROM-Share"; Local = "C:\mnt\rom_share";   User = $null;            Password = $null }  # Guest access
)

# --- Script Body ---
Write-Host "Starting setup of network shares and symbolic links..."

# Create the base directories if they don't exist
$baseMountDir = "C:\mnt"
$shareDir = "C:\share"
if (-not (Test-Path -Path $baseMountDir)) {
    Write-Host "Creating base mount directory: $baseMountDir"
    New-Item -Path $baseMountDir -ItemType Directory | Out-Null
}
if (-not (Test-Path -Path $shareDir)) {
    Write-Host "Creating directory: $shareDir"
    New-Item -Path $shareDir -ItemType Directory | Out-Null
}

# Loop through each share entry
foreach ($entry in $entries) {
    $remotePath = $entry.Remote
    $localPath = $entry.Local
    $localDirName = Split-Path -Path $localPath -Leaf
    $homeLink = Join-Path -Path $env:USERPROFILE -ChildPath $localDirName

    # 1. Create the local mount point directory if it doesn't exist
    if (-not (Test-Path -Path $localPath)) {
        Write-Host "Creating directory: $localPath"
        New-Item -Path $localPath -ItemType Directory | Out-Null
    } else {
        Write-Host "Directory already exists: $localPath"
    }

    # 2. Map the network share using 'net use'
    Write-Host "Mapping network share: $remotePath"
    try {
        # Check if the path is already in use
        if (Test-Path -LiteralPath $localPath -PathType Container) {
             $mountStatus = Get-Item -LiteralPath $localPath
             if ($mountStatus.LinkType -eq 'Network') {
                Write-Host "$localPath is already a mapped drive. Skipping."
             }
        }

        if ($entry.User) {
            # Use credentials
            net use $localPath $remotePath /user:$($entry.User) $($entry.Password) /persistent:yes
        } else {
            # Guest access
            net use $localPath $remotePath /persistent:yes
        }
        Write-Host "Successfully mapped $remotePath to $localPath"
    } catch {
        Write-Error "Failed to map $remotePath. Error: $_"
        Write-Error "Please check your network connectivity, firewall rules, and credentials."
    }

    # 3. Create a symbolic link in the home directory
    if (-not (Test-Path -Path $homeLink)) {
        Write-Host "Creating symlink: $homeLink -> $localPath"
        New-Item -ItemType SymbolicLink -Path $homeLink -Target $localPath | Out-Null
    } else {
        Write-Host "Symlink already exists: $homeLink"
    }

    # 4. Create additional specific symlinks in C:\share
    if ($localPath -eq "C:\mnt\usb_share") {
        $customLinkPath = Join-Path -Path $shareDir -ChildPath "usb1"
        if (-not (Test-Path -Path $customLinkPath)) {
            Write-Host "Creating symlink: $customLinkPath -> $localPath"
            New-Item -ItemType SymbolicLink -Path $customLinkPath -Target $localPath | Out-Null
        } else {
            Write-Host "Symlink already exists: $customLinkPath"
        }
    } elseif ($localPath -eq "C:\mnt\usb_share_2") {
        $customLinkPath = Join-Path -Path $shareDir -ChildPath "usb2"
        if (-not (Test-Path -Path $customLinkPath)) {
            Write-Host "Creating symlink: $customLinkPath -> $localPath"
            New-Item -ItemType SymbolicLink -Path $customLinkPath -Target $localPath | Out-Null
        } else {
            Write-Host "Symlink already exists: $customLinkPath"
        }
    }
}

# --- NEW: Map C:\share\trans to %USERPROFILE%\temp ---
Write-Host "Setting up C:\share\trans link..."

# Ensure %USERPROFILE%\temp directory exists
$tempDir = Join-Path -Path $env:USERPROFILE -ChildPath "temp"
if (-not (Test-Path -Path $tempDir)) {
    Write-Host "Creating directory: $tempDir"
    New-Item -Path $tempDir -ItemType Directory | Out-Null
} else {
    Write-Host "Directory already exists: $tempDir"
}

# Define and create the symbolic link C:\share\trans -> %USERPROFILE%\temp
$customTransLinkName = Join-Path -Path $shareDir -ChildPath "trans"
if (-not (Test-Path -Path $customTransLinkName)) {
    Write-Host "Creating symlink: $customTransLinkName -> $tempDir"
    New-Item -ItemType SymbolicLink -Path $customTransLinkName -Target $tempDir | Out-Null
} else {
    Write-Host "Symlink already exists: $customTransLinkName"
}

Write-Host "`nAll tasks completed! Directories created, shares mapped, and symlinks established."