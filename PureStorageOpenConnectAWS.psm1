<#	
===========================================================================
	Created by:   	barkz@purestorage.com
	Organization: 	Pure Storage, Inc.
    Filename:     	PureStorageOpenConnectAWS.psm1
    Version:        1.0
	Copyright:		(c) 2017 Pure Storage, Inc.
	Github:			https://github.com/purestorage-opeconnect/aws 
	-------------------------------------------------------------------------
	Module Name: PureStorageOpenConnectAWS
#>
<#
	Disclaimer
	The sample script and documentation are provided AS IS and are not supported by 
	the author or the author?s employer, unless otherwise agreed in writing. You bear 
	all risk relating to the use or performance of the sample script and documentation. 
	The author and the author?s employer disclaim all express or implied warranties 
	(including, without limitation, any warranties of merchantability, title, infringement 
	or fitness for a particular purpose). In no event shall the author, the author?s employer 
	or anyone else involved in the creation, production, or delivery of the scripts be liable 
	for any damages whatsoever arising out of the use or performance of the sample script and 
	documentation (including, without limitation, damages for loss of business profits, 
	business interruption, loss of business information, or other pecuniary loss), even if 
	such person has been advised of the possibility of such damages.
#>

#
# Connect to the Pure Storage FlashArray with credentials
#
$ReadHost_FA = Read-Host -Prompt "Enter the IP Address of the FlashArray"
$ReadHost_User = Read-Host -Prompt "Enter username"
$ReadHost_UserPwd = Read-Host -Prompt "Enter the password for $($ReadHost_User)" -AsSecureString
$FaCreds = New-Object System.Management.Automation.PSCredential ($ReadHost_User, $ReadHost_UserPwd)
$FlashArray = New-PfaArray -EndPoint $ReadHost_FA -Credentials $FaCreds -IgnoreCertificateError

#
# Retrieve the IQN number of the initiator
# 
$Iqn = Get-InitiatorPort | Where-Object { $_.NodeAddress -like 'iqn.*' }

#
# Create a host with the given iqn number 
#
$ReadHost_HostName = Read-Host -Prompt "Name of the host"
New-PfaHost -Array $FlashArray -IqnList $Iqn.NodeAddress -Name $ReadHost_HostName

#
# Create new volume with size
#
$ReadHost_Vol = Read-Host -Prompt "Name of the Volume"
$ReadHost_VolSize = Read-Host -Prompt 'Volume size (T,G,M)'
New-PfaVolume -Array $FlashArray -VolumeName $ReadHost_Vol -Unit G -Size $ReadHost_VolSize

#
# Connecting volume/host
#
New-PfaHostVolumeConnection -Array $FlashArray -VolumeName $ReadHost_Vol -HostName $ReadHost_HostName
