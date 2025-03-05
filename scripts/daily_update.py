#!/usr/bin/env python
"""
Nookの情報収集を実行するスクリプト。
すべてのサービス（Reddit、Hacker News、GitHub Trending、Tech Feed、arXiv論文）から
情報を収集し、ローカルストレージに保存します。

使用方法:
    python scripts/daily_update.py
    または
    ./scripts/daily_update.py

オプション:
    --service SERVICE    実行するサービス (all, reddit, hackernews, github, techfeed, paper)
    --log-file FILE      ログの出力先ファイル (デフォルト: logs/daily_update.log)
    -h, --help           ヘルプメッセージを表示
"""

import os
import sys
import argparse
import subprocess
import logging
from datetime import datetime
import time

def setup_logging(log_file=None):
    """ロギングの設定"""
    if log_file:
        log_dir = os.path.dirname(log_file)
        if log_dir and not os.path.exists(log_dir):
            os.makedirs(log_dir)
        
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s [%(levelname)s] %(message)s',
            handlers=[
                logging.FileHandler(log_file),
                logging.StreamHandler(sys.stdout)
            ]
        )
    else:
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s [%(levelname)s] %(message)s',
            handlers=[
                logging.StreamHandler(sys.stdout)
            ]
        )

def run_service(service="all"):
    """指定されたサービスを実行"""
    start_time = time.time()
    logging.info(f"サービス '{service}' の実行を開始します...")
    
    cmd = [
        sys.executable, "-m", "nook.services.run_services",
        "--service", service
    ]
    
    try:
        process = subprocess.Popen(
            cmd,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
            bufsize=1
        )
        
        # 出力をリアルタイムでログに記録
        for line in iter(process.stdout.readline, ''):
            if line:
                logging.info(line.strip())
        
        process.wait()
        
        if process.returncode == 0:
            elapsed_time = time.time() - start_time
            logging.info(f"サービス '{service}' の実行が完了しました (所要時間: {elapsed_time:.2f}秒)")
            return True
        else:
            logging.error(f"サービス '{service}' の実行中にエラーが発生しました (終了コード: {process.returncode})")
            return False
    
    except Exception as e:
        logging.error(f"サービス '{service}' の実行中に例外が発生しました: {e}")
        return False

def main():
    """メイン関数: コマンドライン引数を解析し、サービスを実行"""
    parser = argparse.ArgumentParser(description="Nookの情報収集を実行します")
    parser.add_argument(
        "--service",
        type=str,
        default="all",
        choices=["all", "reddit", "hackernews", "github", "techfeed", "paper"],
        help="実行するサービス (デフォルト: all)"
    )
    parser.add_argument(
        "--log-file",
        type=str,
        default="logs/daily_update.log",
        help="ログの出力先ファイル (デフォルト: logs/daily_update.log)"
    )
    
    args = parser.parse_args()
    
    # ロギングの設定
    setup_logging(args.log_file)
    
    # 実行開始時刻をログに記録
    now = datetime.now()
    logging.info(f"日次更新を開始します - {now.strftime('%Y-%m-%d %H:%M:%S')}")
    
    # サービスを実行
    success = run_service(args.service)
    
    # 実行終了時刻をログに記録
    now = datetime.now()
    if success:
        logging.info(f"日次更新が正常に完了しました - {now.strftime('%Y-%m-%d %H:%M:%S')}")
    else:
        logging.error(f"日次更新が異常終了しました - {now.strftime('%Y-%m-%d %H:%M:%S')}")
    
    # 終了コードを設定
    sys.exit(0 if success else 1)

if __name__ == "__main__":
    main() 