# AI-QQ 群聊机器人

基于 QQ 官方机器人开放平台和 OpenAI 兼容大模型的 QQ 群聊机器人。QQ 连接、消息适配、应用处理、模型调用和 SQLite 记忆分层组织，但部署时仍是一个 Python 服务。

## 快速开始

先准备实际配置：带 `.example` 后缀的文件只是模板，不会被程序自动读取。

Windows PowerShell：

```powershell
cd "C:\path\to\ai-qq-bot"
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
if (!(Test-Path .env)) { Copy-Item .env.example .env }
if (!(Test-Path config\persona.json)) { Copy-Item config\persona.example.json config\persona.json }
```

Linux：

```bash
cd /path/to/ai-qq-bot
python3 -m venv .venv
source .venv/bin/activate
python -m pip install -r requirements.txt
test -f .env || cp .env.example .env
test -f config/persona.json || cp config/persona.example.json config/persona.json
```

编辑实际配置文件：

- `.env`：填写 `BOT_APPID`、`BOT_SECRET` 和 `LLM_API_KEY`；
- `config/persona.json`：修改机器人的名称、规则、语气和示例对话。该文件属于本地实际配置，不提交到仓库。

先用命令行验证模型和人设：

```bash
python src/cli_chat.py
```

确认试聊正常后启动 QQ 服务：

```bash
python src/main.py
```

输入 `退出`、`quit` 或 `exit` 可以结束命令行试聊。正式服务运行时不要同时启动第二个 `src/main.py` 实例，否则可能造成重复连接。

## 配置关系

```text
.env.example                config/persona.example.json
       │ 复制                         │ 复制
       ▼                              ▼
.env（实际环境变量）        config/persona.json（实际人设）
       │                              │
       └────────────── 程序启动时读取 ─┘
```

`.env` 含有密钥，不要提交到仓库；`config/persona.json` 可能包含个人设定、内部群信息或不适合公开的示例，也不提交到仓库。修改人设后重启进程即可生效。

## 当前架构

```text
QQ botpy 回调 → QQ 适配器 → 统一消息 → 应用核心
                                      ├─ 访问控制 / 限速
                                      ├─ 人设与触发器
                                      ├─ LLM 接口
                                      └─ SQLite 对话存储
```

SQLite 默认写入 `data/memory.db`，可通过 `DATA_DIR` 指定持久化目录。完整目录说明见 `项目结构说明.md`；从注册 QQ 机器人到运行的教程见 `docs/从0到1搭建QQ群聊机器人.md`；Rock Pi 4B 部署见 `docs/Rock-Pi-4B部署指南.md`。

### 会话与功能边界

- 支持群聊 @ 消息和 C2C 私聊；实际可用范围取决于 QQ 平台权限。
- 会话键由平台、会话类型、会话 ID 和用户 ID 组成。群聊设计为“同群不同用户分别记忆”，不是全群共享上下文；用户标识提取的待核对项见下文。
- 每次模型请求读取最近 8 轮历史；SQLite 为每个会话保留最近 200 条消息。
- 用户档案目前只更新昵称和最近出现时间，尚未读取档案参与回复，不属于完整的长期记忆。
- 人设和关键词触发器从 `config/persona.json` 加载并缓存，修改后需要重启。
- 默认按用户限制为 1 秒内不能连续触发、每分钟最多 8 次。白名单和黑名单在 `src/guard.py` 中配置，使用平台提供的用户标识，不应直接假定为 QQ 号码。

### 当前待完善项

以下是源码检查中发现的限制，不代表已经修复或完成线上验证：

1. **群聊用户标识待核对**：适配器当前读取 `author.id`，缺失时回退到群 ID。应根据实际 botpy 版本和事件结构核对 `member_openid` 等字段，否则可能导致同群用户共用历史和限流。
2. **同一会话未串行处理**：并发消息可能读取相同旧历史，回复完成和存储顺序也可能与接收顺序不同。
3. **模型请求未显式设置超时**：目前依赖 OpenAI SDK 的默认超时与重试策略。
4. **部署缺少人设文件预检**：部署脚本检查 `.env`，但没有检查 `config/persona.json`，请在启动前手动确认文件存在且内容有效。
5. **缺少自动化回归测试**：`src/smoke_test.py` 会请求在线模型并打印结果，不包含自动断言，也不能代替单元测试。它只是“不连接 QQ”，并非断网可运行。

## 同步到 Rock Pi

源码有更新时，在项目根目录的 Windows PowerShell 执行：

```powershell
cd "C:\path\to\ai-qq-bot"
$rockPiAddress = Read-Host "Rock Pi 地址或主机名"
$linuxUser = Read-Host "Rock Pi Linux 用户名"
$remoteDir = Read-Host "Rock Pi 上的项目绝对路径"
.\tool\sync-to-rock.ps1 -RockHost $rockPiAddress -RockUser $linuxUser -RemoteDir $remoteDir
```

需要同步后自动重启服务时，加上 `-Restart`：

```powershell
.\tool\sync-to-rock.ps1 -RockHost $rockPiAddress -RockUser $linuxUser -RemoteDir $remoteDir -Restart
```

同步脚本不再内置设备 IP、Linux 用户名或项目路径；请在命令参数中填入自己的值。它会保留设备上的 `.env`、`.venv` 和 `data/`。完整说明见 `tool/README.md`。

## Rock Pi 服务管理

Rock Pi 上使用 systemd 运行时：

```bash
sudo systemctl status ai-qq-bot
sudo systemctl is-active ai-qq-bot
sudo systemctl is-enabled ai-qq-bot
sudo journalctl -u ai-qq-bot -f
```

`active` 表示正在运行，`enabled` 表示已设置开机自启。完整部署步骤见 `docs/Rock-Pi-4B部署指南.md`。
