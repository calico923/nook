#!/bin/bash
# Nookの日次更新用cronジョブを設定するスクリプト

# 現在のディレクトリを取得
CURRENT_DIR=$(pwd)
SCRIPT_PATH="$CURRENT_DIR/scripts/daily_update.py"
LOG_PATH="$CURRENT_DIR/logs/daily_update.log"

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

# cronジョブの内容を作成
CRON_JOB="0 9 * * * cd $CURRENT_DIR && $PYTHON_PATH $SCRIPT_PATH --log-file $LOG_PATH >> $LOG_PATH 2>&1"

# 既存のcronジョブを確認
EXISTING_CRON=$(crontab -l 2>/dev/null | grep -F "$SCRIPT_PATH")

if [ -n "$EXISTING_CRON" ]; then
    echo "既存のcronジョブが見つかりました。上書きしますか？ (y/n)"
    read -r CONFIRM
    if [ "$CONFIRM" != "y" ]; then
        echo "キャンセルしました。"
        exit 0
    fi
    
    # 既存のジョブを削除
    crontab -l 2>/dev/null | grep -v -F "$SCRIPT_PATH" | crontab -
fi

# 新しいcronジョブを追加
(crontab -l 2>/dev/null; echo "$CRON_JOB") | crontab -

echo "cronジョブを設定しました。毎日午前9時に日次更新が実行されます。"
echo "設定したcronジョブ: $CRON_JOB"
echo ""
echo "現在のcronジョブ一覧:"
crontab -l 