#!/usr/bin/env python
"""GitHubTrendingのテストを実行するスクリプト。"""

import sys
import os
from pathlib import Path
from unittest.mock import patch, MagicMock

# プロジェクトのルートディレクトリをPYTHONPATHに追加
sys.path.insert(0, os.path.abspath("."))

# テストモジュールをインポート
from tests.test_github_trending import mock_requests_get

# 必要なモジュールをインポート
from nook.services.github_trending.github_trending import GithubTrending, Repository

def run_test():
    """テストを実行する関数。"""
    # パッチを適用
    with patch('requests.get', side_effect=mock_requests_get) as mock_get:
        with patch('nook.services.github_trending.github_trending.Grok3Client') as mock_grok_client:
            # Grok3Clientのモック設定
            mock_client_instance = mock_grok_client.return_value
            # 呼び出し履歴を記録するためのリスト
            translation_calls = []
            
            def mock_generate_content(prompt, **kwargs):
                # 呼び出し情報を記録
                translation_calls.append({
                    "prompt": prompt,
                    "kwargs": kwargs
                })
                # プロンプトから説明部分だけを抽出
                description = prompt.split('\n\n')[-1]
                # 翻訳結果を返す（実際の翻訳の代わりに「翻訳:」を付けて返す）
                return f"翻訳: {description}"
            
            mock_client_instance.generate_content.side_effect = mock_generate_content
            
            # テスト用の一時ディレクトリを作成
            test_dir = Path("test_data")
            test_dir.mkdir(exist_ok=True)
            
            try:
                # GithubTrendingインスタンスを作成
                github_trending = GithubTrending(storage_dir=str(test_dir))
                
                # 特定の言語のリポジトリを取得
                repositories = github_trending._retrieve_repositories("python", 3)
                
                # 結果を検証
                assert len(repositories) == 3
                
                # 各リポジトリの説明を確認（翻訳前）
                descriptions = [repo.description for repo in repositories]
                expected_descriptions = [
                    "This is a description for repo1. It contains technical terms like API, REST, and GraphQL.",
                    "A simple tool for developers to manage their workflow efficiently.",
                    "Implementation of advanced algorithms for machine learning and data processing."
                ]
                
                # 翻訳前の説明を記録
                results = []
                for i, (expected, actual) in enumerate(zip(expected_descriptions, descriptions)):
                    results.append({
                        "repository": f"repo{i+1}",
                        "expected_description": expected,
                        "actual_description": actual
                    })
                
                # 手動で翻訳処理を実行
                # 言語とリポジトリのタプルのリストを作成
                repositories_by_language = [("python", repositories)]
                # 翻訳処理を実行
                translated_repositories = github_trending._translate_repositories(repositories_by_language)
                
                # 翻訳後の説明を取得
                translated_descriptions = [repo.description for repo in translated_repositories[0][1]]
                
                # 結果をMarkdownファイルに出力
                logs_dir = Path("logs")
                logs_dir.mkdir(exist_ok=True)
                
                # datetime をインポート
                from datetime import datetime
                
                with open(logs_dir / "github_trending_test.md", "w", encoding="utf-8") as f:
                    f.write("# GitHubTrending repo.description テスト結果\n\n")
                    f.write(f"テスト実行日時: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n")
                    
                    f.write("## 翻訳前の説明\n\n")
                    for result in results:
                        f.write(f"### リポジトリ: {result['repository']}\n\n")
                        f.write(f"#### 期待される説明\n\n")
                        f.write(f"```\n{result['expected_description']}\n```\n\n")
                        f.write(f"#### 実際の説明\n\n")
                        f.write(f"```\n{result['actual_description']}\n```\n\n")
                        f.write("---\n\n")
                    
                    f.write("## 翻訳後の説明\n\n")
                    for i, desc in enumerate(translated_descriptions):
                        f.write(f"### リポジトリ: repo{i+1}\n\n")
                        f.write(f"#### 翻訳後の説明\n\n")
                        f.write(f"```\n{desc}\n```\n\n")
                        f.write("---\n\n")
                    
                    # 翻訳プロンプトの例も記録
                    example_prompt = f"以下の英語のテキストを自然な日本語に翻訳してください。技術用語はそのままでも構いません。\n\n{expected_descriptions[0]}"
                    f.write("## 翻訳プロンプトの例\n\n")
                    f.write(f"```\n{example_prompt}\n```\n\n")
                    
                    # モックの呼び出し情報も記録
                    f.write("## モック呼び出し情報\n\n")
                    f.write(f"- requests.get 呼び出し回数: {mock_get.call_count}\n")
                    f.write(f"- Grok3Client.generate_content 呼び出し回数: {mock_client_instance.generate_content.call_count}\n\n")
                    
                    # 翻訳呼び出しの詳細を記録
                    f.write("## 翻訳呼び出しの詳細\n\n")
                    for i, call in enumerate(translation_calls):
                        f.write(f"### 呼び出し {i+1}\n\n")
                        f.write(f"#### プロンプト\n\n")
                        f.write(f"```\n{call['prompt']}\n```\n\n")
                        f.write(f"#### パラメータ\n\n")
                        f.write(f"```\n{call['kwargs']}\n```\n\n")
                        f.write("---\n\n")
                    
                    # デバッグ情報
                    f.write("## デバッグ情報\n\n")
                    f.write("### 期待される翻訳結果と実際の翻訳結果の比較\n\n")
                    for i, (expected, translated) in enumerate(zip(expected_descriptions, translated_descriptions)):
                        f.write(f"#### リポジトリ: repo{i+1}\n\n")
                        f.write(f"期待される翻訳結果: `翻訳: {expected}`\n\n")
                        f.write(f"実際の翻訳結果: `{translated}`\n\n")
                        f.write("---\n\n")
                
                # 検証（翻訳前）
                for expected, actual in zip(expected_descriptions, descriptions):
                    assert expected == actual
                
                # 検証（翻訳後）
                for expected, translated in zip(expected_descriptions, translated_descriptions):
                    assert translated == f"翻訳: {expected}"
                
                return {
                    "original": results,
                    "translated": [
                        {"repository": f"repo{i+1}", "translated_description": desc}
                        for i, desc in enumerate(translated_descriptions)
                    ],
                    "translation_calls": translation_calls
                }
            
            finally:
                # テスト用ディレクトリを削除
                import shutil
                if test_dir.exists():
                    shutil.rmtree(test_dir)

if __name__ == "__main__":
    print("GitHubTrending repo.description テストを実行中...")
    
    # テストを実行
    results = run_test()
    
    # 結果ファイルのパス
    result_file = Path("logs/github_trending_test.md")
    
    if result_file.exists():
        print(f"テストが完了しました。結果は {result_file} に保存されました。")
        
        # 結果ファイルの内容を表示
        print("\n===== テスト結果の内容 =====\n")
        with open(result_file, "r", encoding="utf-8") as f:
            print(f.read())
    else:
        print("テストは実行されましたが、結果ファイルが見つかりません。") 