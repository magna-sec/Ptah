#Requires -RunAsAdministrator

# ============================================================
#  Set-SigningConfig.ps1
#  Toggle SMB signing, LDAP signing, and LDAP channel binding
# ============================================================

function Write-Banner {
    Write-Host ""
    Write-Host "  =============================================" -ForegroundColor Cyan
    Write-Host "       SMB / LDAP Signing Configuration        " -ForegroundColor White
    Write-Host "  =============================================" -ForegroundColor Cyan
    Write-Host ""
}

function Write-Status {
    param([string]$Message, [string]$Colour = "Gray")
    Write-Host "  [*] $Message" -ForegroundColor $Colour
}

function Write-Change {
    param([string]$Message)
    Write-Host "  [+] $Message" -ForegroundColor Green
}

function Write-Warn {
    param([string]$Message)
    Write-Host "  [!] $Message" -ForegroundColor Yellow
}

function Write-Err {
    param([string]$Message)
    Write-Host "  [-] $Message" -ForegroundColor Red
}

# ─── Helpers ─────────────────────────────────────────────────

function Get-RegValue {
    param([string]$Path, [string]$Name)
    try {
        return (Get-ItemProperty -Path $Path -Name $Name -ErrorAction Stop).$Name
    } catch {
        return $null
    }
}

function Set-RegValue {
    param([string]$Path, [string]$Name, [int]$Value, [string]$Type = "DWORD")
    if (-not (Test-Path $Path)) {
        New-Item -Path $Path -Force | Out-Null
    }
    Set-ItemProperty -Path $Path -Name $Name -Value $Value -Type $Type
}

function Get-EnableDisable {
    param([string]$Prompt)
    while ($true) {
        Write-Host ""
        Write-Host "  $Prompt" -ForegroundColor White
        Write-Host "    1. Enable" -ForegroundColor Green
        Write-Host "    2. Disable" -ForegroundColor Red
        Write-Host ""
        $choice = Read-Host "  Choice"
        if ($choice -eq "1") { return $true }
        if ($choice -eq "2") { return $false }
        Write-Warn "Enter 1 or 2."
    }
}

function Get-LdapLevel {
    param([string]$Prompt)
    while ($true) {
        Write-Host ""
        Write-Host "  $Prompt" -ForegroundColor White
        Write-Host "    1. None        (signing not required or negotiated)" -ForegroundColor Red
        Write-Host "    2. Negotiate   (sign if the client/server supports it)" -ForegroundColor Yellow
        Write-Host "    3. Require     (signing is mandatory — rejects unsigned traffic)" -ForegroundColor Green
        Write-Host ""
        $choice = Read-Host "  Choice"
        if ($choice -eq "1") { return 0 }
        if ($choice -eq "2") { return 1 }
        if ($choice -eq "3") { return 2 }
        Write-Warn "Enter 1, 2, or 3."
    }
}

function Get-ChannelBindingLevel {
    param([string]$Prompt)
    while ($true) {
        Write-Host ""
        Write-Host "  $Prompt" -ForegroundColor White
        Write-Host "    1. Never       (channel binding not enforced)" -ForegroundColor Red
        Write-Host "    2. When Supported  (enforce only when client claims support)" -ForegroundColor Yellow
        Write-Host "    3. Always      (enforce for all clients)" -ForegroundColor Green
        Write-Host ""
        $choice = Read-Host "  Choice"
        if ($choice -eq "1") { return 0 }
        if ($choice -eq "2") { return 1 }
        if ($choice -eq "3") { return 2 }
        Write-Warn "Enter 1, 2, or 3."
    }
}

# ─── SMB Signing ─────────────────────────────────────────────

function Set-SmbSigningServer {
    $path = "HKLM:\SYSTEM\CurrentControlSet\Services\LanmanServer\Parameters"

    $currentReq = Get-RegValue $path "RequireSecuritySignature"
    $currentEna = Get-RegValue $path "EnableSecuritySignature"
    Write-Status "Current SMB Server signing state:"
    Write-Status "  RequireSecuritySignature = $currentReq"
    Write-Status "  EnableSecuritySignature  = $currentEna"

    $enable = Get-EnableDisable "SMB Server Signing:"

    if ($enable) {
        Set-RegValue $path "RequireSecuritySignature" 1
        Set-RegValue $path "EnableSecuritySignature"  1
        Write-Change "SMB Server signing ENABLED (required). All clients must sign SMB traffic."
        Write-Warn   "Note: clients that do not support SMB signing will be refused."
    } else {
        Set-RegValue $path "RequireSecuritySignature" 0
        Set-RegValue $path "EnableSecuritySignature"  0
        Write-Change "SMB Server signing DISABLED. The server will not require or negotiate signing."
        Write-Warn   "Note: this allows relay attacks (e.g. NTLM relay via Responder)."
    }
}

function Set-SmbSigningClient {
    $path = "HKLM:\SYSTEM\CurrentControlSet\Services\LanmanWorkstation\Parameters"

    $currentReq = Get-RegValue $path "RequireSecuritySignature"
    $currentEna = Get-RegValue $path "EnableSecuritySignature"
    Write-Status "Current SMB Client signing state:"
    Write-Status "  RequireSecuritySignature = $currentReq"
    Write-Status "  EnableSecuritySignature  = $currentEna"

    $enable = Get-EnableDisable "SMB Client Signing:"

    if ($enable) {
        Set-RegValue $path "RequireSecuritySignature" 1
        Set-RegValue $path "EnableSecuritySignature"  1
        Write-Change "SMB Client signing ENABLED (required). This machine will only connect to servers that sign."
        Write-Warn   "Note: this machine will refuse connections to servers without SMB signing."
    } else {
        Set-RegValue $path "RequireSecuritySignature" 0
        Set-RegValue $path "EnableSecuritySignature"  0
        Write-Change "SMB Client signing DISABLED. This machine will not require signing when connecting."
        Write-Warn   "Note: this makes this machine vulnerable to SMB relay attacks."
    }
}

# ─── LDAP Signing ────────────────────────────────────────────

function Set-LdapServerSigning {
    $path = "HKLM:\SYSTEM\CurrentControlSet\Services\NTDS\Parameters"
    $name = "LDAPServerIntegrity"

    $current = Get-RegValue $path $name
    $labels  = @("None", "Negotiate", "Require")
    Write-Status "Current LDAP Server signing: $current ($($labels[$current] ?? 'unknown'))"

    $level = Get-LdapLevel "LDAP Server Signing (domain controller):"

    Set-RegValue $path $name $level
    Write-Change "LDAP Server signing set to: $level ($($labels[$level]))"

    switch ($level) {
        0 { Write-Warn "None: the DC accepts unsigned LDAP binds. Credentials sent in clear text are not protected." }
        1 { Write-Warn "Negotiate: the DC will sign if the client requests it, but won't force it." }
        2 { Write-Change "Require: the DC rejects any LDAP bind that is not signed. Recommended for production." }
    }
}

function Set-LdapClientSigning {
    $path = "HKLM:\SYSTEM\CurrentControlSet\Services\ldap"
    $name = "LDAPClientIntegrity"

    $current = Get-RegValue $path $name
    $labels  = @("None", "Negotiate", "Require")
    Write-Status "Current LDAP Client signing: $current ($($labels[$current] ?? 'unknown'))"

    $level = Get-LdapLevel "LDAP Client Signing (this machine as a client):"

    Set-RegValue $path $name $level
    Write-Change "LDAP Client signing set to: $level ($($labels[$level]))"

    switch ($level) {
        0 { Write-Warn "None: this machine sends unsigned LDAP requests. Vulnerable to LDAP relay." }
        1 { Write-Warn "Negotiate: this machine requests signing but will fall back if the server doesn't support it." }
        2 { Write-Change "Require: this machine will only complete LDAP binds that are signed." }
    }
}

# ─── LDAP Channel Binding ─────────────────────────────────────

function Set-LdapChannelBinding {
    $path = "HKLM:\SYSTEM\CurrentControlSet\Services\NTDS\Parameters"
    $name = "LdapEnforceChannelBinding"

    $current = Get-RegValue $path $name
    $labels  = @("Never", "When Supported", "Always")
    Write-Status "Current LDAP Channel Binding: $current ($($labels[$current] ?? 'unknown'))"

    $level = Get-ChannelBindingLevel "LDAP Channel Binding (domain controller):"

    Set-RegValue $path $name $level
    Write-Change "LDAP Channel Binding set to: $level ($($labels[$level]))"

    switch ($level) {
        0 { Write-Warn "Never: channel binding tokens are not checked. Vulnerable to LDAP relay over TLS." }
        1 { Write-Warn "When Supported: enforced only when the client advertises support. Partial protection." }
        2 { Write-Change "Always: all LDAPS connections must provide a valid channel binding token. Strongest setting." }
    }

    Write-Warn "Channel binding applies to LDAPS (636) and LDAP with STARTTLS only, not plain LDAP (389)."
}

# ─── Show Current State ───────────────────────────────────────

function Show-CurrentState {
    Write-Host ""
    Write-Host "  ---- Current Signing State ----" -ForegroundColor Cyan

    # SMB Server
    $p = "HKLM:\SYSTEM\CurrentControlSet\Services\LanmanServer\Parameters"
    $req = Get-RegValue $p "RequireSecuritySignature"
    $ena = Get-RegValue $p "EnableSecuritySignature"
    Write-Host "  SMB Server   Require=$req  Enable=$ena" -ForegroundColor White

    # SMB Client
    $p = "HKLM:\SYSTEM\CurrentControlSet\Services\LanmanWorkstation\Parameters"
    $req = Get-RegValue $p "RequireSecuritySignature"
    $ena = Get-RegValue $p "EnableSecuritySignature"
    Write-Host "  SMB Client   Require=$req  Enable=$ena" -ForegroundColor White

    # LDAP Server Signing
    $p = "HKLM:\SYSTEM\CurrentControlSet\Services\NTDS\Parameters"
    $labels = @("None", "Negotiate", "Require")
    $val = Get-RegValue $p "LDAPServerIntegrity"
    Write-Host "  LDAP Server Signing    = $val ($($labels[$val] ?? 'not set'))" -ForegroundColor White

    # LDAP Client Signing
    $p = "HKLM:\SYSTEM\CurrentControlSet\Services\ldap"
    $val = Get-RegValue $p "LDAPClientIntegrity"
    Write-Host "  LDAP Client Signing    = $val ($($labels[$val] ?? 'not set'))" -ForegroundColor White

    # Channel Binding
    $p = "HKLM:\SYSTEM\CurrentControlSet\Services\NTDS\Parameters"
    $cbLabels = @("Never", "When Supported", "Always")
    $val = Get-RegValue $p "LdapEnforceChannelBinding"
    Write-Host "  LDAP Channel Binding   = $val ($($cbLabels[$val] ?? 'not set'))" -ForegroundColor White

    Write-Host ""
}

# ─── Main Menu ────────────────────────────────────────────────

function Show-Menu {
    Write-Host "  What would you like to configure?" -ForegroundColor White
    Write-Host "    1. SMB Signing - Server" -ForegroundColor Gray
    Write-Host "    2. SMB Signing - Client" -ForegroundColor Gray
    Write-Host "    3. LDAP Signing - Server (DC)" -ForegroundColor Gray
    Write-Host "    4. LDAP Signing - Client" -ForegroundColor Gray
    Write-Host "    5. LDAP Channel Binding (DC)" -ForegroundColor Gray
    Write-Host "    6. Show current state" -ForegroundColor Gray
    Write-Host "    7. Exit" -ForegroundColor Gray
    Write-Host ""
}

# ─── Entry Point ─────────────────────────────────────────────

Write-Banner

while ($true) {
    Show-Menu
    $choice = Read-Host "  Choice"
    Write-Host ""

    switch ($choice) {
        "1" { Set-SmbSigningServer }
        "2" { Set-SmbSigningClient }
        "3" { Set-LdapServerSigning }
        "4" { Set-LdapClientSigning }
        "5" { Set-LdapChannelBinding }
        "6" { Show-CurrentState }
        "7" { Write-Status "Exiting." "Cyan"; exit 0 }
        default { Write-Warn "Enter a number between 1 and 7." }
    }

    Write-Host ""
    Write-Warn "A reboot (or restart of relevant services) may be required for changes to take effect."
    Write-Host ""
}
