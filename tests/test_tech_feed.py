"""TechFeedクラスのテスト。特にarticle.summaryの生成過程に注目。"""

import os
from pathlib import Path
from unittest.mock import patch, MagicMock
import pytest
from bs4 import BeautifulSoup
from types import SimpleNamespace

from nook.services.tech_feed.tech_feed import TechFeed, Article

def create_mock_feed_entry():
    """テスト用のフィードエントリを作成。"""
    # SimpleNamespaceを使用してオブジェクトライクな構造を作成
    return SimpleNamespace(
        title='Test Article Title',
        link='https://example.com/test-article',
        summary='This is a test article summary from feed.'
    )

def create_mock_html_content():
    """テスト用のHTML内容を作成。"""
    return """
    <html>
        <head>
            <meta name="description" content="This is a meta description of the article.">
        </head>
        <body>
            <article>
                <p>First paragraph of the article content.</p>
                <p>Second paragraph with technical details.</p>
                <p>Third paragraph explaining implementation.</p>
                <p>Fourth paragraph with results.</p>
                <p>Fifth paragraph with conclusion.</p>
            </article>
        </body>
    </html>
    """

@pytest.fixture
def mock_storage(tmp_path):
    """一時ストレージを作成するフィクスチャ。"""
    return tmp_path

@pytest.fixture
def tech_feed(mock_storage):
    """TechFeedインスタンスを作成するフィクスチャ。"""
    with patch('nook.services.tech_feed.tech_feed.tomli.load') as mock_load:
        mock_load.return_value = {
            'test_category': ['https://example.com/feed']
        }
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
        title='Test Article',
        url='https://example.com/test-article',
        text='\n'.join([p.get_text() for p in mock_soup.find_all('p')]),
        soup=mock_soup,
        category='test_category'
    )
    
    # Grok3Clientのモック
    with patch.object(tech_feed.grok_client, 'generate_content') as mock_generate:
        mock_generate.return_value = "Generated summary of the article"
        
        # 要約を生成
        tech_feed._summarize_article(article)
        
        # Grokに送信されたプロンプトとシステムインストラクションを取得
        call_args = mock_generate.call_args[1]
        sent_prompt = call_args['prompt']
        system_instruction = call_args['system_instruction']
        
        # 結果をファイルに保存
        results_dir = Path('test_results')
        results_dir.mkdir(exist_ok=True)
        
        with open(results_dir / 'summary_generation_test.md', 'w', encoding='utf-8') as f:
            f.write("# Article Summary Generation Test Results\n\n")
            
            f.write("## Original Article Content\n\n")
            f.write("### Full Text\n```\n")
            f.write(article.text)
            f.write("\n```\n\n")
            
            f.write("### Meta Description\n```\n")
            meta_desc = mock_soup.find("meta", attrs={"name": "description"})
            f.write(meta_desc.get("content") if meta_desc else "No meta description")
            f.write("\n```\n\n")
            
            f.write("## Grok API Input\n\n")
            f.write("### System Instruction\n```\n")
            f.write(system_instruction)
            f.write("\n```\n\n")
            
            f.write("### Complete Prompt\n```\n")
            f.write(sent_prompt)
            f.write("\n```\n\n")
            
            f.write("## Generated Summary\n```\n")
            f.write(article.summary)
            f.write("\n```\n")
            
            # プロンプトの解析結果も追加
            f.write("\n## Prompt Analysis\n\n")
            f.write("### Text Length\n")
            f.write(f"Original text length: {len(article.text)} characters\n")
            f.write(f"Text sent to Grok: {len(article.text[:2000])} characters (first 2000 chars)\n\n")
            
            f.write("### Prompt Structure\n")
            for line in sent_prompt.split('\n'):
                if line.strip():
                    f.write(f"- {line.strip()}\n")

def test_article_content_extraction(tech_feed):
    """記事本文の抽出プロセスをテスト。"""
    mock_entry = create_mock_feed_entry()
    
    # 翻訳メソッドのモック
    with patch.object(tech_feed, '_translate_to_japanese') as mock_translate:
        mock_translate.side_effect = lambda x: f"[翻訳済] {x}"  # 翻訳をシミュレート
        
        with patch('requests.get') as mock_get:
            mock_get.return_value.status_code = 200
            mock_get.return_value.text = create_mock_html_content()
            
            # _retrieve_articleメソッドを直接テスト
            article = tech_feed._retrieve_article(mock_entry, 'Test Feed', 'test_category')
            
            assert article is not None, "Article should not be None"
            
            # 結果を保存
            results_dir = Path('test_results')
            results_dir.mkdir(exist_ok=True)
            
            with open(results_dir / 'content_extraction_test.md', 'w', encoding='utf-8') as f:
                f.write("# Article Content Extraction Test Results\n\n")
                
                f.write("## Feed Entry Data\n```\n")
                f.write(f"Title: {mock_entry.title}\n")
                f.write(f"Link: {mock_entry.link}\n")
                f.write(f"Summary: {mock_entry.summary}\n")
                f.write("```\n\n")
                
                f.write("## Extracted Content\n\n")
                f.write("### Article Text\n```\n")
                f.write(article.text)
                f.write("\n```\n\n")
                
                f.write("### Meta Description\n```\n")
                meta_desc = article.soup.find("meta", attrs={"name": "description"})
                f.write(meta_desc.get("content") if meta_desc else "No meta description")
                f.write("\n```\n\n")
                
                # テキストの長さと段落数の情報も追加
                f.write("## Content Analysis\n\n")
                paragraphs = article.soup.find_all('p')
                f.write(f"Total text length: {len(article.text)} characters\n")
                f.write(f"Number of paragraphs: {len(paragraphs)}\n\n")
                
                f.write("### Individual Paragraphs\n")
                for i, p in enumerate(paragraphs, 1):
                    f.write(f"\nParagraph {i}:\n```\n{p.get_text()}\n```\n")
                
                # 翻訳の呼び出し情報
                f.write("\n## Translation Process\n\n")
                f.write(f"Number of translation calls: {mock_translate.call_count}\n\n")
                f.write("### Translation calls:\n")
                for args, kwargs in mock_translate.call_args_list:
                    f.write(f"\nInput text:\n```\n{args[0]}\n```\n")

if __name__ == '__main__':
    # テストを実行
    pytest.main([__file__, '-v']) 