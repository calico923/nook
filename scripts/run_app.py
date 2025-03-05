#!/usr/bin/env python
"""
Nookアプリケーションを一括起動するスクリプト。
バックエンドAPIとフロントエンドStreamlitアプリを同時に起動します。

使用方法:
    python scripts/run_app.py
    または
    ./scripts/run_app.py

オプション:
    --api-host HOST     APIサーバーのホストアドレス (デフォルト: 0.0.0.0)
    --api-port PORT     APIサーバーのポート番号 (デフォルト: 8000)
    --frontend-port PORT フロントエンドのポート番号 (デフォルト: 8501)
    --no-reload         コード変更時に自動リロードしない
    --backend-only      バックエンドのみを起動
    --frontend-only     フロントエンドのみを起動
    --daemon            バックグラウンドで起動し、ログを表示しない
    --log-file FILE     ログの出力先ファイル (デフォルト: nook_app.log)
    -h, --help          ヘルプメッセージを表示
"""

import os
import sys
import argparse
import subprocess
import time
from pathlib import Path
import signal
import atexit
import logging
from datetime import datetime

# プロセスを格納するグローバル変数
processes = []

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

def signal_handler(sig, frame):
    """シグナルハンドラー: Ctrl+Cなどで終了時に全プロセスを終了させる"""
    logging.info("アプリケーションを終了しています...")
    for process in processes:
        if process.poll() is None:  # プロセスが実行中なら
            process.terminate()
    sys.exit(0)

def cleanup():
    """終了時に全プロセスをクリーンアップする"""
    for process in processes:
        if process.poll() is None:  # プロセスが実行中なら
            process.terminate()

def start_backend(host="0.0.0.0", port=8000, reload=True, daemon=False):
    """バックエンドAPIサーバーを起動"""
    logging.info(f"バックエンドAPIを起動しています... http://{host}:{port}")
    cmd = [
        sys.executable, "-m", "uvicorn", "nook.api.main:app",
        "--host", host,
        "--port", str(port)
    ]
    if reload:
        cmd.append("--reload")
    
    # 標準出力と標準エラー出力の設定
    if daemon:
        stdout = subprocess.DEVNULL
        stderr = subprocess.DEVNULL
    else:
        stdout = subprocess.PIPE
        stderr = subprocess.STDOUT
    
    process = subprocess.Popen(
        cmd,
        stdout=stdout,
        stderr=stderr,
        text=True if not daemon else None,
        bufsize=1
    )
    processes.append(process)
    return process

def start_frontend(port=8501, daemon=False):
    """フロントエンドStreamlitアプリを起動"""
    logging.info(f"フロントエンドを起動しています... http://localhost:{port}")
    
    # 標準出力と標準エラー出力の設定
    if daemon:
        stdout = subprocess.DEVNULL
        stderr = subprocess.DEVNULL
    else:
        stdout = subprocess.PIPE
        stderr = subprocess.STDOUT
    
    process = subprocess.Popen(
        [sys.executable, "-m", "streamlit", "run", "nook/frontend/app.py", "--server.port", str(port)],
        stdout=stdout,
        stderr=stderr,
        text=True if not daemon else None,
        bufsize=1
    )
    processes.append(process)
    return process

def monitor_processes(daemon=False):
    """プロセスの出力をモニタリングして表示する"""
    if daemon:
        # デーモンモードの場合は、プロセスが終了するまで待機するだけ
        for process in processes:
            process.wait()
        return
    
    while True:
        all_terminated = True
        for i, process in enumerate(processes):
            if process.poll() is None:  # プロセスが実行中
                all_terminated = False
                try:
                    # 出力を1行読み込む（ブロックしない）
                    output = process.stdout.readline()
                    if output:
                        prefix = "\033[94m[API]\033[0m     " if i == 0 else "\033[92m[FRONTEND]\033[0m"
                        print(f"{prefix} {output.strip()}")
                except Exception:
                    pass
            else:
                # プロセスが終了した場合、残りの出力を読み込む
                if process.stdout:
                    remaining_output = process.stdout.read()
                    if remaining_output:
                        prefix = "\033[94m[API]\033[0m     " if i == 0 else "\033[92m[FRONTEND]\033[0m"
                        print(f"{prefix} {remaining_output.strip()}")
        
        if all_terminated:
            logging.info("すべてのプロセスが終了しました。")
            break
        
        time.sleep(0.1)

def create_pid_file(pid_file):
    """PIDファイルを作成"""
    with open(pid_file, 'w') as f:
        f.write(str(os.getpid()))

def main():
    """メイン関数: コマンドライン引数を解析し、アプリケーションを起動"""
    parser = argparse.ArgumentParser(description="Nookアプリケーションを一括起動します")
    parser.add_argument(
        "--api-host", 
        type=str, 
        default="0.0.0.0", 
        help="APIサーバーのホストアドレス (デフォルト: 0.0.0.0)"
    )
    parser.add_argument(
        "--api-port", 
        type=int, 
        default=8000, 
        help="APIサーバーのポート番号 (デフォルト: 8000)"
    )
    parser.add_argument(
        "--frontend-port", 
        type=int, 
        default=8501, 
        help="フロントエンドのポート番号 (デフォルト: 8501)"
    )
    parser.add_argument(
        "--no-reload", 
        action="store_true", 
        help="コード変更時に自動リロードしない"
    )
    parser.add_argument(
        "--backend-only",
        action="store_true",
        help="バックエンドのみを起動"
    )
    parser.add_argument(
        "--frontend-only",
        action="store_true",
        help="フロントエンドのみを起動"
    )
    parser.add_argument(
        "--daemon",
        action="store_true",
        help="バックグラウンドで起動し、ログを表示しない"
    )
    parser.add_argument(
        "--log-file",
        type=str,
        default="nook_app.log",
        help="ログの出力先ファイル (デフォルト: nook_app.log)"
    )
    parser.add_argument(
        "--pid-file",
        type=str,
        default="nook_app.pid",
        help="PIDファイルのパス (デフォルト: nook_app.pid)"
    )
    
    args = parser.parse_args()
    
    # ロギングの設定
    log_file = args.log_file if args.daemon else None
    setup_logging(log_file)
    
    # デーモンモードの場合はPIDファイルを作成
    if args.daemon:
        create_pid_file(args.pid_file)
        logging.info(f"PIDファイルを作成しました: {args.pid_file}")
    
    # 相互排他的なオプションのチェック
    if args.backend_only and args.frontend_only:
        logging.error("エラー: --backend-only と --frontend-only は同時に指定できません")
        sys.exit(1)
    
    # シグナルハンドラーを設定
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)
    
    # 終了時のクリーンアップを登録
    atexit.register(cleanup)
    
    logging.info("Nookアプリケーションを起動しています...")
    
    # 起動するコンポーネントを決定
    if args.frontend_only:
        logging.info("注意: フロントエンドのみを起動します。バックエンドが別途起動されていることを確認してください。")
        frontend_process = start_frontend(port=args.frontend_port, daemon=args.daemon)
    elif args.backend_only:
        logging.info("注意: バックエンドのみを起動します。")
        backend_process = start_backend(
            host=args.api_host,
            port=args.api_port,
            reload=not args.no_reload,
            daemon=args.daemon
        )
    else:
        # 両方起動（デフォルト）
        backend_process = start_backend(
            host=args.api_host,
            port=args.api_port,
            reload=not args.no_reload,
            daemon=args.daemon
        )
        
        # バックエンドが起動するまで少し待つ
        time.sleep(2)
        
        frontend_process = start_frontend(port=args.frontend_port, daemon=args.daemon)
    
    if not args.daemon:
        logging.info("ログ出力:")
    
    # プロセスの出力をモニタリング
    try:
        monitor_processes(daemon=args.daemon)
    except KeyboardInterrupt:
        logging.info("アプリケーションを終了しています...")
        sys.exit(0)

if __name__ == "__main__":
    main()