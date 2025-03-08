"""TechFeedクラスのテスト。特にarticle.summaryとsocial_postの生成過程に注目。"""

import os
from pathlib import Path
from unittest.mock import patch, MagicMock
import pytest
from bs4 import BeautifulSoup
from types import SimpleNamespace
from datetime import datetime

from nook.services.tech_feed.tech_feed import TechFeed, Article

def create_mock_feed_entry():
    """テスト用のフィードエントリを作成。"""
    return SimpleNamespace(
        title='CursorのProject Rules運用のベストプラクティスを探る',
        link='https://zenn.dev/ks0318/articles/b8eb2c9396f9cb',
        summary='この記事では自分がProject Rulesをどのように運用しているかを書いていきます。設定ではなく運用という表現が近いです。'
    )

def create_mock_html_content():
    """テスト用のHTML内容を作成。"""
    return """
    <html>
        <head>
            <meta name="description" content="この記事では自分がProject Rulesをどのように運用しているかを書いていきます。設定ではなく運用という表現が近いです。">
            <meta name="og:title" content="CursorのProject Rules運用のベストプラクティスを探る">
        </head>
        <body>
            <article>
                <p>こんにちは、しば田です！</p>
                <p>この記事では自分がProject Rulesをどのように運用しているかを書いていきます。設定ではなく運用という表現が近いです。</p>
                <p>まずは結論から。現時点での僕の考えるベスプラは以下です。日々アップデートして育てる、育てやすい構成にしておく、複数のmdファイルの中身を結合するスクリプトを作ってmdcファイルを生成する、mdcファイルの参照ルール（Auto Attach、Description、alwaysApply）には落とし穴があるので気をつける。</p>
                <p>Project Rulesは一回作ったら終わりではないです。なぜなら、AIに対しての要望は開発していれば無限に生まれてくるからです。実装していると「AIここ毎回間違えるな」と「この指示は毎度したくないから覚えておいて欲しいな」という場面に結構遭遇します。</p>
                <p>僕が実際のプロジェクトで使用している構成は、.cursor/rulesディレクトリに4つの基本的なmdcファイルを配置し、実際の編集は細かく分けられたmdファイルで行うようにしています。</p>
            </article>
        </body>
    </html>
    """

def create_valid_social_post():
    """有効な投稿文を生成。"""
    return "CursorのProject Rulesについての話。Project Rulesは一回作ったら終わりではありません。AIに対しての要望は開発していれば無限に生まれてくるからです。実装していると「AIここ毎回間違えるな」と「この指示は毎度したくないから覚えておいて欲しいな」という場面に結構遭遇します。そこで、日々アップデートして育てる、育てやすい構成にしておく、複数のmdファイルの中身を結合するスクリプトを作ってmdcファイルを生成する、といった運用方法を提案します。また、mdcファイルの参照ルールには落とし穴があるので注意が必要です。"

@pytest.fixture
def mock_storage(tmp_path):
    """一時ストレージを作成するフィクスチャ。"""
    return tmp_path

@pytest.fixture
def tech_feed(mock_storage):
    """TechFeedインスタンスを作成するフィクスチャ。"""
    with patch('nook.services.tech_feed.tech_feed.tomli.load') as mock_load, \
         patch('nook.services.tech_feed.tech_feed.Grok3Client') as mock_grok:
        mock_load.return_value = {
            'test_category': ['https://example.com/feed']
        }
        # Grok3Clientのモックを設定
        mock_grok_instance = MagicMock()
        mock_grok.return_value = mock_grok_instance
        return TechFeed(storage_dir=str(mock_storage))

def test_article_summary_generation(tech_feed):
    """article.summaryの生成過程をテスト。"""
    # モックの設定
    mock_entry = create_mock_feed_entry()
    mock_html = create_mock_html_content()
    mock_soup = BeautifulSoup(mock_html, 'html.parser')
    
    # テスト用の記事オブジェクトを作成
    article = Article(
        feed_name='Test Feed',
        title='CursorのProject Rules運用のベストプラクティスを探る',
        url='https://zenn.dev/ks0318/articles/b8eb2c9396f9cb',
        text='\n'.join([p.get_text() for p in mock_soup.find_all('p')]),
        soup=mock_soup,
        category='test_category'
    )
    
    # Grok3Clientのモック
    with patch.object(tech_feed.grok_client, 'generate_content') as mock_generate:
        def mock_generate_content(**kwargs):
            if '要約' in kwargs['prompt']:
                return "Project Rulesの運用に関する記事です。日々アップデートして育てること、育てやすい構成にすること、複数のmdファイルを結合してmdcファイルを生成すること、参照ルールの落とし穴に気をつけることが重要です。"
            else:
                # 実際のGrokの出力をシミュレート
                return "CursorのProject Rulesの運用方法についての話。この記事では、Project Rulesを効果的に運用するためのベストプラクティスを紹介します。一度作って終わりではなく、日々の開発の中で継続的にアップデートしていくことが重要です。"
        
        mock_generate.side_effect = mock_generate_content
        
        # 要約を生成
        tech_feed._summarize_article(article)
        
        # Grokに送信されたプロンプトとシステムインストラクションを取得
        call_args = mock_generate.call_args_list
        assert len(call_args) == 2, "Grok3Client.generate_content should be called twice"
        
        # 要約生成の呼び出しを確認
        summary_call = call_args[0][1]
        assert "要約" in summary_call['prompt']
        print(f"\n生成された要約: {article.summary}")
        
        # 投稿文生成の呼び出しを確認
        social_post_call = call_args[1][1]
        assert "190文字から200文字の範囲" in social_post_call['prompt']
        print(f"\n生成された投稿文: {article.social_post}")
        print(f"投稿文の文字数: {len(article.social_post)}")

def test_social_post_generation(tech_feed):
    """social_postの生成をテスト。"""
    article = Article(
        feed_name='Test Feed',
        title='CursorのProject Rules運用のベストプラクティスを探る',
        url='https://zenn.dev/ks0318/articles/b8eb2c9396f9cb',
        text='この記事では自分がProject Rulesをどのように運用しているかを書いていきます。設定ではなく運用という表現が近いです。',
        soup=BeautifulSoup('<html></html>', 'html.parser'),
        category='test_category'
    )
    
    # Grokの出力をテスト
    with patch.object(tech_feed.grok_client, 'generate_content') as mock_generate:
        mock_generate.return_value = "CursorのProject Rulesの運用方法についての話。この記事では、Project Rulesを効果的に運用するためのベストプラクティスを紹介します。一度作って終わりではなく、日々の開発の中で継続的にアップデートしていくことが重要です。"
        
        result = tech_feed._create_social_post(article)
        print(f"\n生成された投稿文: {result}")
        print(f"投稿文の文字数: {len(result)}")
        
        # 基本的な形式のチェック
        assert result.split('。')[0].endswith('話'), "投稿文の最初の文が'話。'で終わっていません"

def test_social_post_storage(tech_feed, tmp_path):
    """social_postsの保存をテスト。"""
    from os import environ
    
    # 環境変数の設定
    environ['CONTENTS_DIR'] = str(tmp_path)
    print(f"\n保存先ディレクトリ: {tmp_path}")
    
    # テスト用の投稿データ
    test_post = "CursorのProject Rulesの運用方法についての話。この記事では、Project Rulesを効果的に運用するためのベストプラクティスを紹介します。一度作って終わりではなく、日々の開発の中で継続的にアップデートしていくことが重要です。"
    posts = [
        {
            'url': 'https://zenn.dev/ks0318/articles/b8eb2c9396f9cb',
            'title': 'CursorのProject Rules運用のベストプラクティスを探る',
            'content': test_post,
            'char_count': len(test_post)
        }
    ]
    
    # 投稿を保存
    tech_feed._store_social_posts(posts)
    
    # 保存されたファイルを確認
    today = datetime.now()
    file_path = tmp_path / f"{today.strftime('%Y-%m-%d')}.md"
    assert file_path.exists()
    
    # ファイルの内容を確認
    content = file_path.read_text()
    print(f"\n保存されたファイルの内容:\n{content}")
    assert test_post in content

def test_end_to_end_workflow(tech_feed, tmp_path):
    """エンドツーエンドのワークフローをテスト。"""
    from os import environ
    
    # 環境変数の設定
    environ['CONTENTS_DIR'] = str(tmp_path)
    print(f"\n保存先ディレクトリ: {tmp_path}")
    
    # モックの設定
    mock_entry = create_mock_feed_entry()
    mock_html = create_mock_html_content()
    
    with patch('requests.get') as mock_get, \
         patch.object(tech_feed.grok_client, 'generate_content') as mock_generate, \
         patch('feedparser.parse') as mock_parse:
        
        # requestsのモック
        mock_get.return_value.status_code = 200
        mock_get.return_value.text = mock_html
        
        # feedparserのモック
        mock_parse.return_value = SimpleNamespace(
            feed=SimpleNamespace(title='Test Feed'),
            entries=[mock_entry]
        )
        
        # Grok3Clientのモック
        def mock_generate_content(**kwargs):
            if '要約' in kwargs['prompt']:
                return "Project Rulesの運用に関する記事です。日々アップデートして育てること、育てやすい構成にすること、複数のmdファイルを結合してmdcファイルを生成すること、参照ルールの落とし穴に気をつけることが重要です。"
            else:
                return "CursorのProject Rulesの運用方法についての話。この記事では、Project Rulesを効果的に運用するためのベストプラクティスを紹介します。一度作って終わりではなく、日々の開発の中で継続的にアップデートしていくことが重要です。"
        
        mock_generate.side_effect = mock_generate_content
        
        # サービスを実行
        tech_feed.run(days=1, limit=1)
        
        # 結果を確認
        today = datetime.now()
        summary_file = Path(tech_feed.storage.base_dir) / "tech_feed" / f"{today.strftime('%Y-%m-%d')}.md"
        social_post_file = tmp_path / f"{today.strftime('%Y-%m-%d')}.md"
        
        assert summary_file.exists()
        assert social_post_file.exists()
        
        # 要約ファイルの内容を確認
        summary_content = summary_file.read_text()
        print(f"\n要約ファイルの内容:\n{summary_content}")
        assert 'Project Rules' in summary_content
        
        # 投稿ファイルの内容を確認
        social_post_content = social_post_file.read_text()
        print(f"\n投稿ファイルの内容:\n{social_post_content}")
        assert 'Project Rules' in social_post_content

if __name__ == '__main__':
    pytest.main([__file__, '-v']) 