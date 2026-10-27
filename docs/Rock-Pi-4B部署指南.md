# QQ 群聊机器人：Rock Pi 4B 部署指南

本文以 Ubuntu 20.04、aarch64 和 Python 3.11 为部署示例。下文中的用户名、设备地址和项目目录都应替换成你自己的值；不要把含个人信息的本地快捷命令提交到公开仓库。

## 目录和配置关系

```text
~/project/ai-qq-bot/
├── .venv/                 ← Python 3.11 虚拟环境
├── .env                   ← 实际密钥配置，权限应为 600
├── config/persona.json    ← 实际生效的人设
└── data/memory.db        ← SQLite 运行数据
```

`.env.example` 和 `config/persona.example.json` 只是模板，不会自动生效。程序启动时读取 `.env` 和 `config/persona.json`。

## 1. 传输源码

在 Windows PowerShell 中执行，先把示例路径和连接信息换成自己的：

```powershell
$sshTarget = Read-Host "SSH 目标，格式为 Linux用户名@RockPi地址"
scp -r "C:\path\to\ai-qq-bot" "${sshTarget}:/path/to/project/"
```

如果目标目录已经存在，传输前先备份 `.env` 和 `data/`，避免覆盖设备上的密钥和聊天记录。

后续只修改源码或文档时，可以用同步脚本。在 Windows PowerShell 项目根目录运行，并按提示输入设备地址、用户名和远程目录：

```powershell
.\tool\sync-to-rock.ps1
```

需要同步后立即重启服务时：

```powershell
.\tool\sync-to-rock.ps1 -Restart
```

脚本会自动排除 `.env`、`config/persona.json`、`.venv`、`data/`、数据库、日志和 Python 缓存，因此不会覆盖设备上的密钥、个性化人设、虚拟环境和聊天记录。它会覆盖目标端同名文件并添加新文件，不会自动删除设备上仅存在的旧文件。

## 2. 准备 Python 3.11 虚拟环境

Rock Pi 的系统 Python 可能是 3.8，项目推荐使用 3.11。用户已将 Python 3.11.11 安装在 `/opt/python/3.11/bin/python3.11`，因此在板子上执行：

```bash
cd "$HOME/project/ai-qq-bot"
/opt/python/3.11/bin/python3.11 -m venv .venv
source .venv/bin/activate
python --version
python -m pip install -r requirements.txt
```

如果虚拟环境已经创建，重复执行不会破坏已有环境；依赖更新时只需重新执行安装命令。

## 3. 创建实际配置

```bash
cd "$HOME/project/ai-qq-bot"
test -f .env || cp .env.example .env
test -f config/persona.json || cp config/persona.example.json config/persona.json
chmod 600 .env
```

然后编辑 `.env`，填写 `BOT_APPID`、`BOT_SECRET` 和 `LLM_API_KEY`。也可以用 heredoc 或其他编辑器写入，关键是最终文件名必须是 `.env`。不要把密钥粘贴到日志或公开问题中；曾经暴露过的 QQ AppSecret 应在正式运行前重新生成。

编辑 `config/persona.json` 修改名称、规则、语气和示例对话。修改后重启服务即可生效。

## 4. 手动验证

```bash
cd "$HOME/project/ai-qq-bot"
source .venv/bin/activate
python src/cli_chat.py      # 先验证模型和人设
python src/main.py          # 再验证 QQ 连接
```

确认群里 @ 机器人可以回复后，再配置开机自启。

## 5. 配置 systemd 开机自启

推荐直接让部署脚本按当前项目目录生成服务：

```bash
cd "$HOME/project/ai-qq-bot"
PYTHON_BIN=/opt/python/3.11/bin/python3.11 bash deploy/deploy.sh
```

如果机器人还在前台运行，先回到运行它的终端按 `Ctrl+C` 停止，再执行部署脚本，避免手动进程和 systemd 服务同时连接 QQ。脚本会复用当前目录，创建或复用 `.venv`，安装依赖，检查 `.env`，生成 `/etc/systemd/system/ai-qq-bot.service`，并执行 `enable` 和 `start`。脚本需要 sudo 权限。

如果手动安装，服务文件中的关键路径必须是：

```ini
User=your-user
WorkingDirectory=/home/your-user/project/ai-qq-bot
ExecStart=/home/your-user/project/ai-qq-bot/.venv/bin/python src/main.py
```

手动安装前，把 `your-user` 和项目路径替换成设备上的实际值。通过 `deploy/deploy.sh` 自动安装时，脚本会根据运行用户和当前项目目录生成这些字段。

安装后执行：

```bash
sudo cp deploy/ai-qq-bot.service /etc/systemd/system/ai-qq-bot.service
sudo systemctl daemon-reload
sudo systemctl enable ai-qq-bot
sudo systemctl start ai-qq-bot
```

## 6. 查看状态和日志

```bash
sudo systemctl status ai-qq-bot
sudo systemctl is-active ai-qq-bot
sudo systemctl is-enabled ai-qq-bot
sudo journalctl -u ai-qq-bot -f
```

`status` 中看到 `Active: active (running)` 或 `is-active` 输出 `active`，表示服务正在运行；`is-enabled` 输出 `enabled`，表示已设置开机自启。按 `Ctrl+C` 退出实时日志查看，不会停止机器人。

常用管理命令：

```bash
sudo systemctl restart ai-qq-bot
sudo systemctl stop ai-qq-bot
sudo systemctl enable ai-qq-bot
sudo systemctl disable ai-qq-bot
```

## 查看资源占用

查看整机 CPU 和进程动态占用：

```bash
top
```

按 `q` 退出。查看内存总量和剩余量：

```bash
free -h
```

只看机器人进程的 CPU、内存和运行时长：

```bash
ps -p "$(systemctl show -p MainPID --value ai-qq-bot)" -o pid,%cpu,%mem,rss,etime,cmd
```

`%cpu` 是进程启动以来的平均 CPU 占用，`%mem` 是内存占比，`rss` 是实际驻留内存（KB），`etime` 是进程运行时间。当前这台 Rock Pi 的一次观测约为 1% CPU、60 MB 内存；具体占用会随消息处理和依赖变化。

## 更新代码

传输新源码后，保留设备上的 `.env`、`config/persona.json` 和 `data/`，然后执行：

```bash
cd "$HOME/project/ai-qq-bot"
source .venv/bin/activate
python -m pip install -r requirements.txt
sudo systemctl restart ai-qq-bot
```

如果新增了配置字段，先对照 `.env.example` 或 `config/persona.example.json` 补齐实际文件。不要用示例文件覆盖已有配置。

## 常见检查

```bash
systemctl is-active ai-qq-bot
python --version
ls -l .env
ls -l data/memory.db
```

服务启动失败时先看：

```bash
sudo journalctl -u ai-qq-bot -n 50 --no-pager
```

常见原因是 `.env` 未创建、密钥无效、虚拟环境路径错误、依赖未安装或设备网络不可用。
