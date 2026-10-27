param(
    [Parameter(Mandatory = $true)][string]$RockHost,
    [Parameter(Mandatory = $true)][string]$RockUser,
    [Parameter(Mandatory = $true)][string]$RemoteDir,
    [switch]$Restart
)

$ErrorActionPreference = "Stop"
$ProjectDir = (Resolve-Path (Join-Path $PSScriptRoot "..")).Path
$Archive = Join-Path $env:TEMP "ai-qq-bot-sync.tar.gz"

Write-Host "同步项目: $ProjectDir -> $RockUser@$RockHost`:$RemoteDir"

# 运行配置、虚拟环境、数据库和日志保留在 Rock Pi 上，不参与同步。
tar -czf $Archive `
    --exclude=".env" `
    --exclude="config/persona.json" `
    --exclude=".venv" `
    --exclude="data" `
    --exclude="*.log" `
    --exclude="*.db" `
    --exclude="__pycache__" `
    --exclude="*.pyc" `
    -C (Split-Path $ProjectDir) (Split-Path $ProjectDir -Leaf)

if ($LASTEXITCODE -ne 0) { throw "打包失败" }

ssh "$RockUser@$RockHost" "mkdir -p '$RemoteDir'"
if ($LASTEXITCODE -ne 0) { throw "无法连接 Rock Pi" }

# 通过 SSH 传输并解压到项目目录。
cmd /c "type `"$Archive`" | ssh $RockUser@$RockHost `"tar -xzf - -C '$RemoteDir' --strip-components=1`""
if ($LASTEXITCODE -ne 0) { throw "传输或解压失败" }

Remove-Item $Archive -Force -ErrorAction SilentlyContinue
Write-Host "文件同步完成。"

if ($Restart) {
    ssh "$RockUser@$RockHost" "sudo systemctl restart ai-qq-bot && systemctl is-active --quiet ai-qq-bot"
    if ($LASTEXITCODE -ne 0) {
        throw "服务重启失败，请执行 sudo journalctl -u ai-qq-bot -n 50 --no-pager"
    }
    Write-Host "服务已重启。"
} else {
    Write-Host "如需应用更新，执行：.\tool\sync-to-rock.ps1 -Restart"
}
