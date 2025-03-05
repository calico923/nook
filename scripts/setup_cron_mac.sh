#!/bin/bash
# Nookの日次更新用launchdジョブを設定するスクリプト（macOS用）

# 現在のディレクトリを取得
CURRENT_DIR=$(pwd)
SCRIPT_PATH="$CURRENT_DIR/scripts/daily_update.py"
LOG_PATH="$CURRENT_DIR/logs/daily_update.log"
PLIST_PATH="$HOME/Library/LaunchAgents/com.nook.daily_update.plist"

# スクリプトが存在するか確認
if [ ! -f "$SCRIPT_PATH" ]; then
    echo "エラー: $SCRIPT_PATH が見つかりません。"
    echo "このスクリプトはNookのルートディレクトリから実行してください。"
    exit 1
fi

# ログディレクトリを作成
mkdir -p "$CURRENT_DIR/logs"

# Pythonの実行パスを取得
PYTHON_PATH=$(which python)
if [ -z "$PYTHON_PATH" ]; then
    echo "エラー: Pythonが見つかりません。"
    exit 1
fi

# LaunchAgentsディレクトリを作成
mkdir -p "$HOME/Library/LaunchAgents"

# plistファイルを作成
cat > "$PLIST_PATH" << EOF
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
    <key>Label</key>
    <string>com.nook.daily_update</string>
    <key>ProgramArguments</key>
    <array>
        <string>$PYTHON_PATH</string>
        <string>$SCRIPT_PATH</string>
        <string>--log-file</string>
        <string>$LOG_PATH</string>
    </array>
    <key>WorkingDirectory</key>
    <string>$CURRENT_DIR</string>
    <key>StartCalendarInterval</key>
    <dict>
        <key>Hour</key>
        <integer>9</integer>
        <key>Minute</key>
        <integer>0</integer>
    </dict>
    <key>StandardErrorPath</key>
    <string>$LOG_PATH</string>
    <key>StandardOutPath</key>
    <string>$LOG_PATH</string>
    <key>EnvironmentVariables</key>
    <dict>
        <key>PATH</key>
        <string>/usr/local/bin:/usr/bin:/bin:/usr/sbin:/sbin</string>
    </dict>
</dict>
</plist>
EOF

# 既存のジョブを停止（存在する場合）
launchctl unload "$PLIST_PATH" 2>/dev/null

# 新しいジョブを登録
launchctl load -w "$PLIST_PATH"

echo "launchdジョブを設定しました。毎日午前9時に日次更新が実行されます。"
echo "設定したplistファイル: $PLIST_PATH"
echo ""
echo "ジョブの状態を確認するには:"
echo "launchctl list | grep com.nook"
echo ""
echo "手動で実行するには:"
echo "launchctl start com.nook.daily_update"
echo ""
echo "ジョブを停止するには:"
echo "launchctl unload $PLIST_PATH" 