$src = "C:\Users\User\OneDrive\MeuGestor\TRAE\MiniGestor_TRAE"
$destRoot = "C:\Users\User\OneDrive\MeuGestor\MiniBanco\code_backups"
New-Item -ItemType Directory -Path $destRoot -Force | Out-Null
$ts = Get-Date -Format "yyyyMMdd_HHmmss"
$zip = Join-Path $destRoot ("official_" + $ts + ".zip")
Compress-Archive -Path $src -DestinationPath $zip -Force
Write-Output ("Backup criado: " + $zip)
