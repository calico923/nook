#!/usr/bin/env python3
"""
ストレージ機能のテスト用スクリプト
Grokの要約やスクレイピング、API実行は行わずにファイル保存機能のみをテストします
"""

import os
import sys
from pathlib import Path
from datetime import datetime
import logging

# ロギングの設定
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

# nookパッケージをインポートできるようにする
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# 必要なモジュールをインポート
from nook.common.storage import LocalStorage
from nook.common.config import get_data_dir, get_data_dir_setting
from nook.services.github_trending.github_trending import GithubTrending
from nook.services.tech_feed.tech_feed import TechFeed
from nook.services.paper_summarizer.paper_summarizer import PaperSummarizer
from nook.services.reddit_explorer.reddit_explorer import RedditExplorer
from nook.services.hacker_news.hacker_news import HackerNewsRetriever

def test_data_dir_setting():
    """
    DATA_DIR環境変数の設定をテストします
    """
    data_dir_setting = get_data_dir_setting()
    data_dir = get_data_dir()
    
    logging.info(f"DATA_DIR環境変数の設定: {data_dir_setting}")
    logging.info(f"実際のデータディレクトリパス: {data_dir}")
    
    # データディレクトリが存在することを確認
    assert data_dir.exists(), f"データディレクトリが存在しません: {data_dir}"
    
    return data_dir

def test_local_storage():
    """
    LocalStorageクラスの基本機能をテストします
    """
    # LocalStorageをNoneで初期化（環境変数から設定を取得）
    storage = LocalStorage(base_dir=None)
    logging.info(f"LocalStorage base_dir: {storage.base_dir}")
    
    # テスト用のコンテンツを作成
    test_content = f"""# テスト

これはテストファイルです。
作成日時: {datetime.now().isoformat()}
"""
    
    # 各サービス用のテストファイルを保存
    services = ["github_trending", "tech_feed", "paper_summarizer"]
    saved_paths = {}
    
    for service in services:
        file_path = storage.save_markdown(test_content, service)
        saved_paths[service] = file_path
        logging.info(f"{service}のテストファイルを保存しました: {file_path}")
        
        # ファイルが存在することを確認
        assert file_path.exists(), f"ファイルが存在しません: {file_path}"
    
    return saved_paths

def test_github_trending_storage():
    """
    GitHubTrendingクラスのストレージ機能をテストします
    Grokの要約やスクレイピングは行いません
    """
    # storage_dir=Noneで初期化
    github_trending = GithubTrending(storage_dir=None)
    logging.info(f"GitHubTrending storage base_dir: {github_trending.storage.base_dir}")
    
    # モックデータを作成
    class Repository:
        def __init__(self, name, link, description, stars):
            self.name = name
            self.link = link
            self.description = description
            self.stars = stars
    
    # テスト用のリポジトリデータ
    repositories = [
        Repository(
            name="test/repo1",
            link="https://github.com/test/repo1",
            description="テスト用リポジトリ1",
            stars="100"
        ),
        Repository(
            name="test/repo2",
            link="https://github.com/test/repo2",
            description="テスト用リポジトリ2",
            stars="200"
        )
    ]
    
    # 言語ごとのリポジトリリスト
    repositories_by_language = [
        ("python", repositories),
        ("javascript", repositories)
    ]
    
    # 保存処理を実行
    github_trending._store_summaries(repositories_by_language)
    
    # 保存先ディレクトリを確認
    service_dir = github_trending.storage.base_dir / "github_trending"
    logging.info(f"GitHubTrending保存先ディレクトリ: {service_dir}")
    
    # ディレクトリが存在することを確認
    assert service_dir.exists(), f"ディレクトリが存在しません: {service_dir}"
    
    # ファイルが存在することを確認
    files = list(service_dir.glob("*.md"))
    logging.info(f"保存されたファイル: {files}")
    assert len(files) > 0, "ファイルが保存されていません"
    
    return service_dir

def test_tech_feed_storage():
    """
    TechFeedクラスのストレージ機能をテストします
    Grokの要約やスクレイピングは行いません
    """
    # storage_dir=Noneで初期化（Grokクライアントはモック）
    tech_feed = TechFeed(storage_dir=None)
    logging.info(f"TechFeed storage base_dir: {tech_feed.storage.base_dir}")
    
    # モックデータを作成
    class Article:
        def __init__(self, feed_name, title, url, text, category=None, summary=None):
            self.feed_name = feed_name
            self.title = title
            self.url = url
            self.text = text
            self.category = category
            self.summary = summary or "テスト用の要約です。"
            # BeautifulSoupオブジェクトのモック
            self.soup = None
    
    # テスト用の記事データ
    articles = [
        Article(
            feed_name="TestBlog",
            title="テスト記事1",
            url="https://example.com/article1",
            text="これはテスト記事1の本文です。",
            category="technology"
        ),
        Article(
            feed_name="TestBlog",
            title="テスト記事2",
            url="https://example.com/article2",
            text="これはテスト記事2の本文です。",
            category="programming"
        )
    ]
    
    # 保存処理を実行
    tech_feed._store_summaries(articles)
    
    # 保存先ディレクトリを確認
    service_dir = tech_feed.storage.base_dir / "tech_feed"
    logging.info(f"TechFeed保存先ディレクトリ: {service_dir}")
    
    # ディレクトリが存在することを確認
    assert service_dir.exists(), f"ディレクトリが存在しません: {service_dir}"
    
    # ファイルが存在することを確認
    files = list(service_dir.glob("*.md"))
    logging.info(f"保存されたファイル: {files}")
    assert len(files) > 0, "ファイルが保存されていません"
    
    return service_dir

def test_paper_summarizer_storage():
    """
    PaperSummarizerクラスのストレージ機能をテストします
    Grokの要約やスクレイピングは行いません
    """
    # storage_dir=Noneで初期化（Grokクライアントはモック）
    paper_summarizer = PaperSummarizer(storage_dir=None)
    logging.info(f"PaperSummarizer storage base_dir: {paper_summarizer.storage.base_dir}")
    
    # モックデータを作成
    class PaperInfo:
        def __init__(self, title, abstract, url, contents, summary=None):
            self.title = title
            self.abstract = abstract
            self.url = url
            self.contents = contents
            self.summary = summary or "テスト用の要約です。"
    
    # テスト用の論文データ
    papers = [
        PaperInfo(
            title="テスト論文1",
            abstract="これはテスト論文1の要約です。",
            url="https://arxiv.org/abs/test.1",
            contents="これはテスト論文1の本文です。"
        ),
        PaperInfo(
            title="テスト論文2",
            abstract="これはテスト論文2の要約です。",
            url="https://arxiv.org/abs/test.2",
            contents="これはテスト論文2の本文です。"
        )
    ]
    
    # 保存処理を実行
    paper_summarizer._store_summaries(papers)
    
    # 保存先ディレクトリを確認
    service_dir = paper_summarizer.storage.base_dir / "paper_summarizer"
    logging.info(f"PaperSummarizer保存先ディレクトリ: {service_dir}")
    
    # ディレクトリが存在することを確認
    assert service_dir.exists(), f"ディレクトリが存在しません: {service_dir}"
    
    # ファイルが存在することを確認
    files = list(service_dir.glob("*.md"))
    logging.info(f"保存されたファイル: {files}")
    assert len(files) > 0, "ファイルが保存されていません"
    
    return service_dir

def test_reddit_explorer_storage():
    """
    RedditExplorerクラスのストレージ機能をテストします
    Grokの要約やスクレイピングは行いません
    """
    # storage_dir=Noneで初期化（APIクライアントは初期化しない）
    # APIクレデンシャルをモックする
    os.environ["REDDIT_CLIENT_ID"] = "mock_client_id"
    os.environ["REDDIT_CLIENT_SECRET"] = "mock_client_secret"
    os.environ["REDDIT_USER_AGENT"] = "mock_user_agent"
    
    # RedditExplorerクラスを継承したモッククラスを作成
    class MockRedditExplorer(RedditExplorer):
        def __init__(self, storage_dir=None):
            # APIクライアントの初期化をスキップ
            self.storage = LocalStorage(storage_dir)
    
    reddit_explorer = MockRedditExplorer(storage_dir=None)
    logging.info(f"RedditExplorer storage base_dir: {reddit_explorer.storage.base_dir}")
    
    # モックデータを作成
    class RedditPost:
        def __init__(self, id, title, url, upvotes, text, permalink, summary=None):
            self.id = id
            self.title = title
            self.url = url
            self.upvotes = upvotes
            self.text = text
            self.permalink = permalink
            self.summary = summary or "テスト用の要約です。"
    
    # テスト用の投稿データ
    posts = [
        ("technology", "programming", RedditPost(
            id="post1",
            title="テスト投稿1",
            url="https://example.com/post1",
            upvotes=100,
            text="これはテスト投稿1の本文です。",
            permalink="https://reddit.com/r/programming/post1"
        )),
        ("entertainment", "movies", RedditPost(
            id="post2",
            title="テスト投稿2",
            url="https://example.com/post2",
            upvotes=200,
            text="これはテスト投稿2の本文です。",
            permalink="https://reddit.com/r/movies/post2"
        ))
    ]
    
    # 保存処理を実行
    reddit_explorer._store_summaries(posts)
    
    # 保存先ディレクトリを確認
    service_dir = reddit_explorer.storage.base_dir / "reddit_explorer"
    logging.info(f"RedditExplorer保存先ディレクトリ: {service_dir}")
    
    # ディレクトリが存在することを確認
    assert service_dir.exists(), f"ディレクトリが存在しません: {service_dir}"
    
    # ファイルが存在することを確認
    files = list(service_dir.glob("*.md"))
    logging.info(f"保存されたファイル: {files}")
    assert len(files) > 0, "ファイルが保存されていません"
    
    return service_dir

def test_hacker_news_storage():
    """
    HackerNewsRetrieverクラスのストレージ機能をテストします
    Grokの要約やスクレイピングは行いません
    """
    # storage_dir=Noneで初期化
    hacker_news = HackerNewsRetriever(storage_dir=None)
    logging.info(f"HackerNewsRetriever storage base_dir: {hacker_news.storage.base_dir}")
    
    # モックデータを作成
    class Story:
        def __init__(self, title, score, url=None, text=None):
            self.title = title
            self.score = score
            self.url = url
            self.text = text
    
    # テスト用の記事データ
    stories = [
        Story(
            title="テスト記事1",
            score=100,
            url="https://example.com/story1",
            text="これはテスト記事1の本文です。"
        ),
        Story(
            title="テスト記事2",
            score=200,
            url="https://example.com/story2",
            text="これはテスト記事2の本文です。"
        )
    ]
    
    # 保存処理を実行
    hacker_news._store_summaries(stories)
    
    # 保存先ディレクトリを確認
    service_dir = hacker_news.storage.base_dir / "hacker_news"
    logging.info(f"HackerNewsRetriever保存先ディレクトリ: {service_dir}")
    
    # ディレクトリが存在することを確認
    assert service_dir.exists(), f"ディレクトリが存在しません: {service_dir}"
    
    # ファイルが存在することを確認
    files = list(service_dir.glob("*.md"))
    logging.info(f"保存されたファイル: {files}")
    assert len(files) > 0, "ファイルが保存されていません"
    
    return service_dir

def main():
    """
    すべてのテストを実行します
    """
    logging.info("=== ストレージ機能テスト開始 ===")
    
    try:
        # DATA_DIR環境変数の設定をテスト
        data_dir = test_data_dir_setting()
        logging.info(f"✅ DATA_DIR設定テスト成功: {data_dir}")
        
        # LocalStorageの基本機能をテスト
        saved_paths = test_local_storage()
        logging.info(f"✅ LocalStorage基本機能テスト成功: {saved_paths}")
        
        # GitHubTrendingのストレージ機能をテスト
        github_dir = test_github_trending_storage()
        logging.info(f"✅ GitHubTrendingストレージテスト成功: {github_dir}")
        
        # TechFeedのストレージ機能をテスト
        tech_feed_dir = test_tech_feed_storage()
        logging.info(f"✅ TechFeedストレージテスト成功: {tech_feed_dir}")
        
        # PaperSummarizerのストレージ機能をテスト
        paper_dir = test_paper_summarizer_storage()
        logging.info(f"✅ PaperSummarizerストレージテスト成功: {paper_dir}")
        
        # RedditExplorerのストレージ機能をテスト
        reddit_dir = test_reddit_explorer_storage()
        logging.info(f"✅ RedditExplorerストレージテスト成功: {reddit_dir}")
        
        # HackerNewsRetrieverのストレージ機能をテスト
        hacker_news_dir = test_hacker_news_storage()
        logging.info(f"✅ HackerNewsRetrieverストレージテスト成功: {hacker_news_dir}")
        
        logging.info("=== すべてのテストが成功しました ===")
        logging.info(f"データディレクトリ {data_dir} を確認してください")
        
        return 0
    except Exception as e:
        logging.error(f"テスト中にエラーが発生しました: {str(e)}", exc_info=True)
        return 1

if __name__ == "__main__":
    sys.exit(main()) 