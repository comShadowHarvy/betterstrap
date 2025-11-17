# ============================================================================
# Windows OpenSSH Server Setup Script
# ============================================================================
# Purpose: Install and configure OpenSSH Server on Windows for remote access
# Usage: Run as Administrator in PowerShell
# ============================================================================

$ErrorActionPreference = "Stop"

# Colors
function Write-Header { param($msg) Write-Host "`n========================================" -ForegroundColor Cyan; Write-Host $msg -ForegroundColor Cyan; Write-Host "========================================`n" -ForegroundColor Cyan }
function Write-Info { param($msg) Write-Host "[INFO] $msg" -ForegroundColor Blue }
function Write-Success { param($msg) Write-Host "[OK] $msg" -ForegroundColor Green }
function Write-Warning { param($msg) Write-Host "[WARN] $msg" -ForegroundColor Yellow }
function Write-Error { param($msg) Write-Host "[ERROR] $msg" -ForegroundColor Red }

Write-Header "Windows OpenSSH Server Setup"

# Check if running as Administrator
$isAdmin = ([Security.Principal.WindowsPrincipal] [Security.Principal.WindowsIdentity]::GetCurrent()).IsInRole([Security.Principal.WindowsBuiltInRole]::Administrator)

if (-not $isAdmin) {
    Write-Error "This script must be run as Administrator!"
    Write-Info "Right-click PowerShell and select 'Run as Administrator', then run this script again."
    exit 1
}

Write-Success "Running with Administrator privileges"

# ============================================================================
# Install OpenSSH Server
# ============================================================================
Write-Header "Installing OpenSSH Server"

$sshServerFeature = Get-WindowsCapability -Online | Where-Object Name -like 'OpenSSH.Server*'

if ($sshServerFeature.State -eq "Installed") {
    Write-Success "OpenSSH Server is already installed"
} else {
    Write-Info "Installing OpenSSH Server..."
    try {
        Add-WindowsCapability -Online -Name OpenSSH.Server~~~~0.0.1.0
        Write-Success "OpenSSH Server installed successfully"
    } catch {
        Write-Error "Failed to install OpenSSH Server: $_"
        exit 1
    }
}

# ============================================================================
# Configure and Start SSH Service
# ============================================================================
Write-Header "Configuring SSH Service"

$sshdService = Get-Service -Name sshd -ErrorAction SilentlyContinue

if ($null -eq $sshdService) {
    Write-Error "sshd service not found. Installation may have failed."
    exit 1
}

Write-Info "Setting sshd service to start automatically..."
Set-Service -Name sshd -StartupType Automatic

if ($sshdService.Status -ne "Running") {
    Write-Info "Starting sshd service..."
    Start-Service sshd
    Write-Success "sshd service started"
} else {
    Write-Success "sshd service already running"
}

# Verify service status
$sshdService = Get-Service -Name sshd
if ($sshdService.Status -eq "Running" -and $sshdService.StartType -eq "Automatic") {
    Write-Success "sshd service is running and set to start automatically"
} else {
    Write-Warning "Service status: $($sshdService.Status), StartType: $($sshdService.StartType)"
}

# ============================================================================
# Configure Windows Firewall
# ============================================================================
Write-Header "Configuring Windows Firewall"

$firewallRule = Get-NetFirewallRule -Name "OpenSSH-Server-In-TCP" -ErrorAction SilentlyContinue

if ($null -eq $firewallRule) {
    Write-Info "Creating firewall rule for SSH (port 22)..."
    New-NetFirewallRule -Name 'OpenSSH-Server-In-TCP' `
        -DisplayName 'OpenSSH Server (sshd)' `
        -Enabled True `
        -Direction Inbound `
        -Protocol TCP `
        -Action Allow `
        -LocalPort 22 `
        -Profile Any
    Write-Success "Firewall rule created"
} else {
    if ($firewallRule.Enabled) {
        Write-Success "Firewall rule already exists and is enabled"
    } else {
        Write-Info "Enabling existing firewall rule..."
        Enable-NetFirewallRule -Name "OpenSSH-Server-In-TCP"
        Write-Success "Firewall rule enabled"
    }
}

# ============================================================================
# Get and Display IP Addresses
# ============================================================================
Write-Header "Network Information"

Write-Info "Getting network IP addresses..."
$ipAddresses = Get-NetIPAddress -AddressFamily IPv4 | 
    Where-Object { 
        $_.IPAddress -notlike "127.*" -and 
        $_.IPAddress -notlike "169.254.*" -and
        $_.PrefixOrigin -ne "WellKnown"
    } | 
    Select-Object -ExpandProperty IPAddress

if ($ipAddresses.Count -eq 0) {
    Write-Warning "No active network adapters found with valid IP addresses"
} else {
    Write-Success "Windows IP Address(es):"
    foreach ($ip in $ipAddresses) {
        Write-Host "  • $ip" -ForegroundColor Yellow
    }
}

# Get Windows username
$currentUser = $env:USERNAME
Write-Info "Current Windows username: $currentUser"

# ============================================================================
# Summary and Next Steps
# ============================================================================
Write-Header "Setup Complete!"

Write-Success "✓ OpenSSH Server installed"
Write-Success "✓ sshd service running and set to automatic"
Write-Success "✓ Firewall configured to allow SSH on port 22"

Write-Host "`n"
Write-Header "How to Connect"

Write-Host "From another machine on your network, connect using:`n" -ForegroundColor Cyan

if ($ipAddresses.Count -gt 0) {
    $primaryIp = $ipAddresses[0]
    Write-Host "  ssh $currentUser@$primaryIp" -ForegroundColor Green
    Write-Host "`n"
} else {
    Write-Host "  ssh $currentUser@<WINDOWS_IP>" -ForegroundColor Green
    Write-Host "  (Replace <WINDOWS_IP> with your Windows machine's IP address)`n" -ForegroundColor Gray
}

Write-Host "After SSH login, enter WSL by running:" -ForegroundColor Cyan
Write-Host "  wsl" -ForegroundColor Green
Write-Host "`n"

Write-Host "Then navigate to your Tdarr setup:" -ForegroundColor Cyan
Write-Host "  cd /home/me/betterstrap/tdarr" -ForegroundColor Green
Write-Host "  sudo bash ./setup-wsl-systemd.sh" -ForegroundColor Green
Write-Host "`n"

Write-Header "Optional: Direct SSH to WSL (Advanced)"
Write-Host "If you want to SSH directly into WSL (port 2222):" -ForegroundColor Gray
Write-Host "1. Run setup-wsl-systemd.sh first to install SSH in WSL" -ForegroundColor Gray
Write-Host "2. Uncomment the WSL SSH section in this script and re-run" -ForegroundColor Gray
Write-Host "`n"

# ============================================================================
# OPTIONAL: Direct WSL SSH Setup (Disabled by default)
# ============================================================================
# Uncomment the section below if you want direct SSH access to WSL

<#
Write-Header "Setting up direct WSL SSH access (port 2222)"

# Get WSL IP
$wslIp = (wsl hostname -I).Trim()

if ([string]::IsNullOrEmpty($wslIp)) {
    Write-Warning "Could not detect WSL IP. Make sure WSL is running."
} else {
    Write-Info "WSL IP detected: $wslIp"
    
    # Remove existing portproxy rule if it exists
    $existingProxy = netsh interface portproxy show v4tov4 | Select-String "2222"
    if ($existingProxy) {
        Write-Info "Removing existing port proxy rule..."
        netsh interface portproxy delete v4tov4 listenport=2222 listenaddress=0.0.0.0
    }
    
    # Add new portproxy rule
    Write-Info "Creating port proxy: Windows:2222 -> WSL:22"
    netsh interface portproxy add v4tov4 listenport=2222 listenaddress=0.0.0.0 connectport=22 connectaddress=$wslIp
    
    # Create firewall rule for port 2222
    $wslFirewallRule = Get-NetFirewallRule -Name "WSL-SSH-In-TCP" -ErrorAction SilentlyContinue
    if ($null -eq $wslFirewallRule) {
        New-NetFirewallRule -Name 'WSL-SSH-In-TCP' `
            -DisplayName 'WSL SSH Access' `
            -Enabled True `
            -Direction Inbound `
            -Protocol TCP `
            -Action Allow `
            -LocalPort 2222 `
            -Profile Any
        Write-Success "Firewall rule created for WSL SSH (port 2222)"
    }
    
    Write-Success "Direct WSL SSH configured!"
    Write-Info "Connect to WSL directly using:"
    if ($ipAddresses.Count -gt 0) {
        Write-Host "  ssh <WSL_USERNAME>@$($ipAddresses[0]) -p 2222" -ForegroundColor Green
    }
    Write-Warning "Note: WSL IP changes on restart. You'll need to update the port proxy rule."
}
#>

Write-Host "Script completed successfully!`n" -ForegroundColor Cyan
