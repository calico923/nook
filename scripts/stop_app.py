#!/usr/bin/env python
"""
Nookアプリケーションを停止するスクリプト。
デーモンモードで起動したアプリケーションを停止します。

使用方法:
    python scripts/stop_app.py
    または
    ./scripts/stop_app.py

オプション:
    --pid-file FILE     PIDファイルのパス (デフォルト: nook_app.pid)
    -h, --help          ヘルプメッセージを表示
"""

import os
import sys
import argparse
import signal
import logging

def setup_logging():
    """ロギングの設定"""
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s [%(levelname)s] %(message)s',
        handlers=[
            logging.StreamHandler(sys.stdout)
        ]
    )

def stop_app(pid_file):
    """PIDファイルからプロセスを停止する"""
    if not os.path.exists(pid_file):
        logging.error(f"PIDファイルが見つかりません: {pid_file}")
        return False
    
    try:
        with open(pid_file, 'r') as f:
            pid = int(f.read().strip())
        
        logging.info(f"プロセスID {pid} を停止しています...")
        
        try:
            # プロセスにSIGTERMシグナルを送信
            os.kill(pid, signal.SIGTERM)
            logging.info(f"プロセスID {pid} を正常に停止しました。")
            
            # PIDファイルを削除
            os.remove(pid_file)
            logging.info(f"PIDファイルを削除しました: {pid_file}")
            
            return True
        except ProcessLookupError:
            logging.warning(f"プロセスID {pid} は既に終了しています。")
            # PIDファイルを削除
            os.remove(pid_file)
            logging.info(f"PIDファイルを削除しました: {pid_file}")
            return True
        except PermissionError:
            logging.error(f"プロセスID {pid} を停止する権限がありません。")
            return False
    except Exception as e:
        logging.error(f"エラーが発生しました: {e}")
        return False

def main():
    """メイン関数: コマンドライン引数を解析し、アプリケーションを停止"""
    parser = argparse.ArgumentParser(description="Nookアプリケーションを停止します")
    parser.add_argument(
        "--pid-file",
        type=str,
        default="nook_app.pid",
        help="PIDファイルのパス (デフォルト: nook_app.pid)"
    )
    
    args = parser.parse_args()
    
    # ロギングの設定
    setup_logging()
    
    # アプリケーションを停止
    success = stop_app(args.pid_file)
    
    # 終了コードを設定
    sys.exit(0 if success else 1)

if __name__ == "__main__":
    main() 