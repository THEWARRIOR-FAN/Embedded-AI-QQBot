# 项目工具

本目录存放开发、同步等辅助工具，不属于机器人运行时的核心源码。

## 同步源码到 Rock Pi

`sync-to-rock.ps1` 用于从 Windows PowerShell 把项目源码包同步到 Rock Pi。为避免公开个人设备信息，脚本不会内置 Rock Pi 的 IP、Linux 用户名或远程路径，运行时需要通过参数提供。

在 PowerShell 中先进入项目根目录。下面的路径是示例，按本机实际位置修改：

```powershell
cd "C:\path\to\ai-qq-bot"
$rockPiAddress = Read-Host "Rock Pi 地址或主机名"
$linuxUser = Read-Host "Rock Pi Linux 用户名"
$remoteDir = Read-Host "Rock Pi 上的项目绝对路径"
.\tool\sync-to-rock.ps1 -RockHost $rockPiAddress -RockUser $linuxUser -RemoteDir $remoteDir
```

同步完成后应用更新并重启 systemd 服务：

```powershell
.\tool\sync-to-rock.ps1 -RockHost $rockPiAddress -RockUser $linuxUser -RemoteDir $remoteDir -Restart
```

脚本会排除 `.env`、`config/persona.json`、`.venv/`、`data/`、数据库、日志和 Python 缓存。因此 Rock Pi 上的密钥、个性化人设、虚拟环境和聊天数据会保留。同步会覆盖目标端同名文件并添加新文件，不会自动删除仅存在于 Rock Pi 上的旧文件。

如需更换设备或目录：

```powershell
$rockPiAddress = "rock-pi.local"
$linuxUser = "your-user"
$remoteDir = "/home/your-user/project/ai-qq-bot"
.\tool\sync-to-rock.ps1 -RockHost $rockPiAddress -RockUser $linuxUser -RemoteDir $remoteDir
```

如果把真实 IP、用户名和目录写进本地快捷命令，请保存在已被 `.gitignore` 忽略的本地文件中，不要提交到 GitHub。

运行前，Windows 需要能使用 `ssh` 和 `tar`，并且 SSH 能登录目标 Rock Pi。首次同步建议先不加 `-Restart`，确认传输成功后再重启服务。
