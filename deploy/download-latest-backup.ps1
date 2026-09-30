param(
    [string]$DestinationDirectory = 'D:\KanjiAI-backups',
    [string]$RemoteHost = 'root@remote.io.vn',
    [int]$Port = 12542
)

$ErrorActionPreference = 'Stop'
$projectRoot = Split-Path -Parent $PSScriptRoot
$projectPath = [IO.Path]::GetFullPath($projectRoot).TrimEnd('\')
$destination = [IO.Path]::GetFullPath($DestinationDirectory).TrimEnd('\')
if ($destination -eq $projectPath -or $destination.StartsWith($projectPath + '\', [StringComparison]::OrdinalIgnoreCase)) {
    throw 'Chọn thư mục backup ngoài repository KanjiAI.'
}
New-Item -ItemType Directory -Force -Path $destination | Out-Null

$remotePath = (& ssh -p $Port $RemoteHost 'find /opt/kanjiai/backups -maxdepth 1 -type f -name "kanjiai-*.db" | sort -r | head -n 1') | Select-Object -First 1
if ($LASTEXITCODE -ne 0 -or $remotePath -notmatch '^/opt/kanjiai/backups/kanjiai-\d{8}T\d{6}Z\.db$') {
    throw 'Không tìm được bản backup hợp lệ trên VPS. Kiểm tra SSH và cron trước.'
}
$name = [IO.Path]::GetFileName($remotePath)
$localPath = Join-Path $destination $name
if (Test-Path -LiteralPath $localPath) {
    throw "Đã có file $localPath; không ghi đè bản backup cũ."
}
& scp -P $Port "${RemoteHost}:$remotePath" $localPath
if ($LASTEXITCODE -ne 0) { throw 'Tải backup qua SCP thất bại.' }
& python (Join-Path $PSScriptRoot 'verify_backup.py') --backup $localPath
if ($LASTEXITCODE -ne 0) { throw 'File đã tải không qua được kiểm tra SQLite.' }
Write-Output "Bản sao ngoài VPS: $localPath"
