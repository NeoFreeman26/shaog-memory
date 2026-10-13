#!/usr/bin/env bash
set -e

PROJECT_DIR="$(cd "$(dirname "$0")" && pwd)"
VENV_DIR="$PROJECT_DIR/.venv"
ENV_FILE="$PROJECT_DIR/.env"
LOG_DIR="$PROJECT_DIR/logs"
PLIST_PATH="$HOME/Library/LaunchAgents/com.freeman.shaog.telegram.plist"

echo "=========================================="
echo "☀️ 小g (ShaoG) Mac mini 24 小時安裝精靈"
echo "=========================================="

# 1. 建立 Python 虛擬環境並安裝套件
echo "📦 [1/3] 正在準備 Python 環境與套件..."
python3 -m venv "$VENV_DIR"
"$VENV_DIR/bin/pip" install --upgrade pip -q
"$VENV_DIR/bin/pip" install -r "$PROJECT_DIR/requirements.txt"

# 2. 設定 .env 檔案
if [ ! -f "$ENV_FILE" ]; then
    echo ""
    echo "🔑 [2/3] 請輸入你從 Telegram @BotFather 取得的 Bot Token："
    read -r -p "TELEGRAM_BOT_TOKEN: " BOT_TOKEN
    echo ""
    echo "（選填）如果你已經知道自己的 Telegram User ID 可直接輸入，否則直接按 Enter 跳過："
    read -r -p "ALLOWED_USER_IDS: " USER_ID

    cat > "$ENV_FILE" <<EOF
TELEGRAM_BOT_TOKEN=$BOT_TOKEN
ALLOWED_USER_IDS=$USER_ID
EOF
    echo "✅ 已建立 .env 設定檔！"
else
    echo "✅ [2/3] 偵測到已存在 .env 設定檔，跳過建立。"
fi

# 3. 建立 macOS LaunchAgent 讓小g 24 小時背景常駐
echo ""
echo "⚙️ [3/3] 正在設定 macOS 24 小時背景常駐服務 (launchd)..."
mkdir -p "$LOG_DIR"
mkdir -p "$HOME/Library/LaunchAgents"

cat > "$PLIST_PATH" <<EOF
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
    <key>Label</key>
    <string>com.freeman.shaog.telegram</string>
    <key>ProgramArguments</key>
    <array>
        <string>$VENV_DIR/bin/python</string>
        <string>$PROJECT_DIR/telegram_bot.py</string>
    </array>
    <key>WorkingDirectory</key>
    <string>$PROJECT_DIR</string>
    <key>RunAtLoad</key>
    <true/>
    <key>KeepAlive</key>
    <true/>
    <key>StandardOutPath</key>
    <string>$LOG_DIR/shaog.out.log</string>
    <key>StandardErrorPath</key>
    <string>$LOG_DIR/shaog.err.log</string>
    <key>EnvironmentVariables</key>
    <dict>
        <key>PATH</key>
        <string>/opt/homebrew/bin:/usr/local/bin:/usr/bin:/bin:/usr/sbin:/sbin</string>
    </dict>
</dict>
</plist>
EOF

launchctl unload "$PLIST_PATH" 2>/dev/null || true
launchctl load "$PLIST_PATH"

echo ""
echo "🎉 安裝完成！小g 已經在你的 Mac mini 背景 24 小時啟動囉！"
echo "👉 現在打開 iPhone 的 Telegram，傳送 /start 給你的機器人試試看吧！"
echo "📄 查看小g執行日誌：tail -f \"$LOG_DIR/shaog.out.log\" \"$LOG_DIR/shaog.err.log\""
