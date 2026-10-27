#!/bin/bash
# ============================================
# QQ 群聊机器人 - Rock Pi 4B 一键部署脚本
# 在板子上执行：bash deploy.sh
# ============================================
set -e

echo "========================================"
echo "  QQ 群聊机器人 - Rock Pi 4B 部署脚本"
echo "========================================"

# ---------- 1. 检查系统 ----------
echo ""
echo "[1/6] 检查系统环境..."

ARCH=$(uname -m)
echo "  CPU 架构: $ARCH"

if [[ "$ARCH" != "aarch64" && "$ARCH" != "arm64" ]]; then
    echo "  ⚠ 当前架构 $ARCH 不是 aarch64，请确认在 Rock Pi 4B 上运行"
    echo "  继续吗？(y/n)"
    read -r confirm
    [[ "$confirm" != "y" ]] && exit 1
fi

# 允许通过 PYTHON_BIN 指定解释器；Rock Pi 4B 的推荐路径是源码安装的 3.11。
if [[ -z "${PYTHON_BIN:-}" ]]; then
    if [[ -x "/opt/python/3.11/bin/python3.11" ]]; then
        PYTHON_BIN="/opt/python/3.11/bin/python3.11"
    elif command -v python3.11 &> /dev/null; then
        PYTHON_BIN="$(command -v python3.11)"
    elif command -v python3 &> /dev/null; then
        PYTHON_BIN="$(command -v python3)"
    else
        echo "  未找到 Python。请先安装 Python 3.11，或执行：PYTHON_BIN=/path/to/python3.11 bash deploy/deploy.sh"
        exit 1
    fi
fi

PY_VERSION=$($PYTHON_BIN --version 2>&1)
echo "  Python: $PY_VERSION"

# 检查 git
if ! command -v git &> /dev/null; then
    echo "  安装 git..."
    sudo apt install -y git
fi

echo "  系统检查通过 ✓"

# ---------- 2. 确定项目目录 ----------
echo ""
echo "[2/6] 确定项目目录..."

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
SOURCE_DIR="$(cd "$SCRIPT_DIR/.." && pwd)"
PROJECT_DIR="${PROJECT_DIR:-$SOURCE_DIR}"
mkdir -p "$PROJECT_DIR"
echo "  项目路径: $PROJECT_DIR"

# ---------- 3. 复制项目文件 ----------
echo ""
echo "[3/6] 复制项目文件..."

if [[ "$SOURCE_DIR" != "$PROJECT_DIR" ]]; then
    echo "  从 $SOURCE_DIR 复制到 $PROJECT_DIR"
    cp -r "$SOURCE_DIR"/* "$PROJECT_DIR/" 2>/dev/null || true
    cp "$SOURCE_DIR"/.env "$PROJECT_DIR/" 2>/dev/null || true
    cp "$SOURCE_DIR"/.env.example "$PROJECT_DIR/" 2>/dev/null || true
fi

echo "  文件就位 ✓"

# ---------- 4. 创建虚拟环境 + 装依赖 ----------
echo ""
echo "[4/6] 创建虚拟环境并安装依赖..."

VENV_DIR="$PROJECT_DIR/.venv"
if [[ ! -x "$VENV_DIR/bin/python" ]]; then
    "$PYTHON_BIN" -m venv "$VENV_DIR"
fi

echo "  激活虚拟环境..."
source "$VENV_DIR/bin/activate"

echo "  升级 pip..."
pip install --upgrade pip -q

echo "  安装依赖（可能需要 1-2 分钟）..."
pip install -r "$PROJECT_DIR/requirements.txt"

echo "  依赖安装完成 ✓"

# ---------- 5. 检查 .env ----------
echo ""
echo "[5/6] 检查配置文件..."

ENV_FILE="$PROJECT_DIR/.env"
if [[ ! -f "$ENV_FILE" ]]; then
    echo "  ⚠ 未找到 .env 文件！"
    echo "  请把 .env.example 复制成 .env 并填好密钥："
    echo "    cp $PROJECT_DIR/.env.example $PROJECT_DIR/.env"
    echo "    nano $PROJECT_DIR/.env"
    echo ""
    echo "  填好后重新运行本脚本。"
    exit 1
fi

# 检查关键字段
BOT_APPID=$(grep "^BOT_APPID=" "$ENV_FILE" | cut -d= -f2)
BOT_SECRET=$(grep "^BOT_SECRET=" "$ENV_FILE" | cut -d= -f2)
LLM_API_KEY=$(grep "^LLM_API_KEY=" "$ENV_FILE" | cut -d= -f2)

if [[ -z "$BOT_APPID" || "$BOT_APPID" == *"你的"* ]]; then
    echo "  ⚠ BOT_APPID 未填写，请编辑 $ENV_FILE"
    exit 1
fi
if [[ -z "$BOT_SECRET" || "$BOT_SECRET" == *"你的"* ]]; then
    echo "  ⚠ BOT_SECRET 未填写，请编辑 $ENV_FILE"
    exit 1
fi
if [[ -z "$LLM_API_KEY" || "$LLM_API_KEY" == *"你的"* ]]; then
    echo "  ⚠ LLM_API_KEY 未填写，请编辑 $ENV_FILE"
    exit 1
fi

echo "  配置检查通过 ✓"

# ---------- 6. 安装 systemd 服务 ----------
echo ""
echo "[6/6] 安装开机自启服务..."

SERVICE_FILE="/etc/systemd/system/ai-qq-bot.service"

echo "  创建 systemd 服务文件..."
sudo tee "$SERVICE_FILE" > /dev/null << EOF
[Unit]
Description=QQ 群聊机器人
After=network-online.target
Wants=network-online.target

[Service]
Type=simple
User=$USER
WorkingDirectory=$PROJECT_DIR
ExecStart=$VENV_DIR/bin/python src/main.py
Restart=on-failure
RestartSec=10
StandardOutput=journal
StandardError=journal

[Install]
WantedBy=multi-user.target
EOF

echo "  重新加载 systemd..."
sudo systemctl daemon-reload

echo "  启用开机自启..."
sudo systemctl enable ai-qq-bot

echo "  启动服务..."
sudo systemctl start ai-qq-bot

sleep 3

# 检查状态
if systemctl is-active --quiet ai-qq-bot; then
    echo ""
    echo "========================================"
    echo "  部署成功！机器人已上线 ✓"
    echo "========================================"
    echo ""
    echo "常用命令："
    echo "  查看状态:  sudo systemctl status ai-qq-bot"
    echo "  查看日志:  sudo journalctl -u ai-qq-bot -f"
    echo "  重启服务:  sudo systemctl restart ai-qq-bot"
    echo "  停止服务:  sudo systemctl stop ai-qq-bot"
    echo "  取消自启:  sudo systemctl disable ai-qq-bot"
    echo ""
    echo "日志也写入: $PROJECT_DIR/botpy.log"
else
    echo ""
    echo "  ⚠ 服务启动失败，查看日志："
    echo "  sudo journalctl -u ai-qq-bot -n 30"
    echo ""
    echo "  最常见原因："
    echo "  1. .env 里的密钥填错"
    echo "  2. 网络不通（Rock Pi 没连上 WiFi/网线）"
    echo "  3. 依赖没装全（重新运行 pip install -r requirements.txt）"
fi
