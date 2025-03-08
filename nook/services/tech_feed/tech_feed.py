"""技術ブログのRSSフィードを監視・収集・要約するサービス。"""

import os
import tomli
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from pathlib import Path
from typing import List, Optional

import feedparser
import requests
from bs4 import BeautifulSoup
from dotenv import load_dotenv

from nook.common.grok_client import Grok3Client
from nook.common.storage import LocalStorage


@dataclass
class Article:
    """
    技術ブログの記事情報。
    
    Parameters
    ----------
    feed_name : str
        フィード名。
    title : str
        タイトル。
    url : str
        URL。
    text : str
        本文。
    soup : BeautifulSoup
        BeautifulSoupオブジェクト。
    category : str | None
        カテゴリ。
    summary : str
        記事の要約。
    social_post : str
        SNS投稿用の文章。
    social_post_char_count : int
        SNS投稿用文章の文字数。
    """
    
    feed_name: str
    title: str
    url: str
    text: str
    soup: BeautifulSoup
    category: Optional[str] = None
    summary: str = field(default="")
    social_post: str = field(default="")
    social_post_char_count: int = field(default=0)


class TechFeed:
    """
    技術ブログのRSSフィードを監視・収集・要約するクラス。
    
    Parameters
    ----------
    storage_dir : str, default="data"
        ストレージディレクトリのパス。
    """
    
    def __init__(self, storage_dir: str = "data"):
        """
        TechFeedを初期化します。
        
        Parameters
        ----------
        storage_dir : str, default="data"
            ストレージディレクトリのパス。
        """
        # .envファイルを読み込む
        load_dotenv()
        
        self.storage = LocalStorage(storage_dir)
        self.grok_client = Grok3Client()
        
        # フィードの設定を読み込む
        script_dir = Path(__file__).parent
        with open(script_dir / "feed.toml", "rb") as f:
            self.feed_config = tomli.load(f)
    
    def run(self, days: int = 1, limit: int = 3) -> None:
        """
        技術ブログのRSSフィードを監視・収集・要約して保存します。
        
        Parameters
        ----------
        days : int, default=1
            何日前までの記事を取得するか。
        limit : int, default=3
            各フィードから取得する記事数。
        """
        all_articles = []
        
        # 各カテゴリのフィードから記事を取得
        for category, feeds in self.feed_config.items():
            print(f"カテゴリ {category} の処理を開始します...")
            for feed_url in feeds:
                try:
                    # フィードを解析
                    print(f"フィード {feed_url} を解析しています...")
                    feed = feedparser.parse(feed_url)
                    feed_name = feed.feed.title if hasattr(feed, "feed") and hasattr(feed.feed, "title") else feed_url
                    
                    # 新しいエントリをフィルタリング
                    entries = self._filter_entries(feed.entries, days, limit)
                    print(f"フィード {feed_name} から {len(entries)} 件のエントリを取得しました")
                    
                    for entry in entries:
                        # 記事を取得
                        article = self._retrieve_article(entry, feed_name, category)
                        if article:
                            # 記事を要約
                            self._summarize_article(article)
                            all_articles.append(article)
                
                except Exception as e:
                    print(f"Error processing feed {feed_url}: {str(e)}")
        
        print(f"合計 {len(all_articles)} 件の記事を取得しました")
        
        # 要約を保存
        if all_articles:
            self._store_summaries(all_articles)
            print(f"記事の要約を保存しました")

            # 投稿文を保存
            social_posts = [
                {
                    'url': article.url,
                    'title': article.title,
                    'content': article.social_post,
                    'char_count': article.social_post_char_count
                }
                for article in all_articles
                if article.social_post  # 投稿文が生成されている記事のみ
            ]
            
            if social_posts:
                self._store_social_posts(social_posts)
                print(f"{len(social_posts)} 件の投稿文を保存しました")
            else:
                print("保存する投稿文がありません")
        else:
            print("保存する記事がありません")
    
    def _filter_entries(self, entries: List[dict], days: int, limit: int) -> List[dict]:
        """
        新しいエントリをフィルタリングします。
        
        Parameters
        ----------
        entries : List[dict]
            エントリのリスト。
        days : int
            何日前までの記事を取得するか。
        limit : int
            取得する記事数。
            
        Returns
        -------
        List[dict]
            フィルタリングされたエントリのリスト。
        """
        print(f"エントリのフィルタリングを開始します（{len(entries)}件）...")
        
        # 日付でフィルタリング
        cutoff_date = datetime.now() - timedelta(days=days)
        recent_entries = []
        
        for entry in entries:
            entry_date = None
            
            if hasattr(entry, "published_parsed") and entry.published_parsed:
                entry_date = datetime(*entry.published_parsed[:6])
            elif hasattr(entry, "updated_parsed") and entry.updated_parsed:
                entry_date = datetime(*entry.updated_parsed[:6])
            
            if entry_date:
                print(f"エントリ日付: {entry_date}, カットオフ日付: {cutoff_date}")
                if entry_date >= cutoff_date:
                    recent_entries.append(entry)
            else:
                # 日付が取得できない場合は含める
                print("エントリに日付情報がありません。含めます。")
                recent_entries.append(entry)
        
        print(f"フィルタリング後のエントリ数: {len(recent_entries)}")
        
        # 最新の記事を取得
        return recent_entries[:limit]
    
    def _retrieve_article(self, entry: dict, feed_name: str, category: str) -> Optional[Article]:
        """
        記事を取得します。
        
        Parameters
        ----------
        entry : dict
            エントリ情報。
        feed_name : str
            フィード名。
        category : str
            カテゴリ。
            
        Returns
        -------
        Article or None
            取得した記事。取得に失敗した場合はNone。
        """
        try:
            # URLを取得
            url = entry.link if hasattr(entry, "link") else None
            if not url:
                return None
            
            # タイトルを取得
            title = entry.title if hasattr(entry, "title") else "無題"
            
            # 記事の内容を取得
            response = requests.get(url, timeout=10)
            if response.status_code != 200:
                return None
            
            soup = BeautifulSoup(response.text, "html.parser")
            
            # 本文を抽出
            text = ""
            
            # まずはエントリの要約を使用
            if hasattr(entry, "summary"):
                text = entry.summary
            
            # 次に記事の本文を抽出
            if not text:
                # メタディスクリプションを取得
                meta_desc = soup.find("meta", attrs={"name": "description"})
                if meta_desc and meta_desc.get("content"):
                    text = meta_desc.get("content")
                else:
                    # 本文の最初の段落を取得
                    paragraphs = soup.find_all("p")
                    if paragraphs:
                        text = "\n".join([p.get_text() for p in paragraphs[:5]])
            
            # タイトルと本文を日本語に翻訳
            title_ja = self._translate_to_japanese(title)
            text_ja = self._translate_to_japanese(text)
            
            return Article(
                feed_name=feed_name,
                title=title_ja,
                url=url,
                text=text_ja,
                soup=soup,
                category=category
            )
        
        except Exception as e:
            print(f"Error retrieving article {entry.get('link', 'unknown')}: {str(e)}")
            return None
    
    def _translate_to_japanese(self, text: str) -> str:
        """
        テキストを日本語に翻訳します。
        
        Parameters
        ----------
        text : str
            翻訳するテキスト。
            
        Returns
        -------
        str
            翻訳されたテキスト。
        """
        try:
            prompt = f"以下の英語のテキストを自然な日本語に翻訳してください。技術用語は適切に翻訳し、必要に応じて英語の専門用語を括弧内に残してください。\n\n{text}"
            
            translated_text = self.grok_client.generate_content(
                prompt=prompt,
                temperature=0.3,
                max_tokens=1000
            )
            
            return translated_text
        except Exception as e:
            print(f"Error translating text: {str(e)}")
            return text  # 翻訳に失敗した場合は原文を返す
    
    def _summarize_article(self, article: Article) -> None:
        """
        記事を要約し、SNS投稿用の文章を生成します。
        
        Parameters
        ----------
        article : Article
            要約する記事。
        """
        # 要約の生成
        prompt = f"""
        以下の技術ブログの記事を要約してください。

        タイトル: {article.title}
        本文: {article.text[:2000]}
        
        要約は以下の形式で行い、日本語で回答してください:
        1. 記事の主な内容（1-2文）
        2. 重要なポイント（箇条書き3-5点）
        3. 技術的な洞察
        """
        
        system_instruction = """
        あなたは技術ブログの記事の要約を行うアシスタントです。
        与えられた記事を分析し、簡潔で情報量の多い要約を作成してください。
        技術的な内容は正確に、一般的な内容は分かりやすく要約してください。
        回答は必ず日本語で行ってください。専門用語は適切に翻訳し、必要に応じて英語の専門用語を括弧内に残してください。
        """
        
        try:
            # 要約を生成
            summary = self.grok_client.generate_content(
                prompt=prompt,
                system_instruction=system_instruction,
                temperature=0.3,
                max_tokens=1000
            )
            article.summary = summary

            # SNS投稿用の文章を生成
            social_post = self._create_social_post(article)
            if social_post:
                article.social_post = social_post
                article.social_post_char_count = len(social_post)
            else:
                print(f"Warning: Failed to generate valid social post for article: {article.url}")

        except Exception as e:
            article.summary = f"要約の生成中にエラーが発生しました: {str(e)}"
            print(f"Error summarizing article: {str(e)}")
    
    def _store_summaries(self, articles: List[Article]) -> None:
        """
        要約を保存します。
        
        Parameters
        ----------
        articles : List[Article]
            保存する記事のリスト。
        """
        if not articles:
            print("保存する記事がありません")
            return
        
        today = datetime.now()
        content = f"# 技術ブログ記事 ({today.strftime('%Y-%m-%d')})\n\n"
        
        # カテゴリごとに整理
        categories = {}
        for article in articles:
            if article.category not in categories:
                categories[article.category] = []
            
            categories[article.category].append(article)
        
        # Markdownを生成
        for category, category_articles in categories.items():
            content += f"## {category.replace('_', ' ').capitalize()}\n\n"
            
            for article in category_articles:
                content += f"### [{article.title}]({article.url})\n\n"
                content += f"**フィード**: {article.feed_name}\n\n"
                content += f"**要約**:\n{article.summary}\n\n"
                content += "---\n\n"
        
        # 保存
        print(f"tech_feed ディレクトリに保存します: {today.strftime('%Y-%m-%d')}.md")
        try:
            self.storage.save_markdown(content, "tech_feed", today)
            print("保存が完了しました")
        except Exception as e:
            print(f"保存中にエラーが発生しました: {str(e)}")
            # ディレクトリを作成して再試行
            try:
                tech_feed_dir = Path(self.storage.base_dir) / "tech_feed"
                tech_feed_dir.mkdir(parents=True, exist_ok=True)
                
                file_path = tech_feed_dir / f"{today.strftime('%Y-%m-%d')}.md"
                with open(file_path, "w", encoding="utf-8") as f:
                    f.write(content)
                print(f"再試行で保存に成功しました: {file_path}")
            except Exception as e2:
                print(f"再試行でも保存に失敗しました: {str(e2)}")

    def _create_social_post(self, article: Article) -> str:
        """
        記事からSNS投稿用の文章を生成する。

        Parameters
        ----------
        article : Article
            投稿文を生成する記事。
            article.titleとarticle.textを使用。

        Returns
        -------
        str
            生成された投稿用文章。文字数制限は247-257文字をGrokに指示しますが、
            出力の文字数チェックは行いません。
        """
        prompt = f"""
        以下の技術ブログの記事から247文字から257文字以内で文章を作成してください。

        タイトル: {article.title}
        本文: {article.text[:2000]}
        
        文章は以下のルールを守って日本語で回答してください。
        ・冒頭文は記事がどんな内容の話かがわかるよう末尾を「〜話。」にする。
        ・冒頭文以降の文章はこの話で最も重要なポイントを初心者でもわかるようにする。
        ・箇条書きはしない。
        """

        system_instruction = """
        あなたは技術ブログの記事の内容からXの投稿を行うアシスタントです。
        与えられた記事を分析し、簡潔で情報量の多い文章を作成してください。
        技術的な内容は正確に、一般的な内容は分かりやすく説明してください。
        回答は必ず日本語で行ってください。専門用語は適切に翻訳し、必要に応じて英語の専門用語を括弧内に残してください。
        """

        try:
            social_post = self.grok_client.generate_content(
                prompt=prompt,
                system_instruction=system_instruction,
                temperature=0.3,
                max_tokens=1000
            )

            # 文字数をカウント（情報提供のみ）
            char_count = len(social_post)
            print(f"Generated post length: {char_count} chars")

            # 冒頭文チェック
            first_sentence = social_post.split('。')[0] + '。'
            if not first_sentence.endswith('話。'):
                print(f"Warning: First sentence does not end with '話。': {first_sentence}")
                return ""

            return social_post

        except Exception as e:
            print(f"Error generating social post: {str(e)}")
            return ""

    def _store_social_posts(self, posts: List[dict]) -> None:
        """
        生成された投稿用文章を保存する。

        Parameters
        ----------
        posts : List[dict]
            投稿情報のリスト。各要素は以下の形式:
            {
                'url': str,
                'title': str,
                'content': str,
                'char_count': int  # 文字数
            }
        """
        try:
            today = datetime.now()
            
            # 保存先ディレクトリの作成
            contents_dir = Path(os.getenv('CONTENTS_DIR', 'contents'))
            print(f"CONTENTS_DIR環境変数: {os.getenv('CONTENTS_DIR')}")
            print(f"保存先ディレクトリ: {contents_dir}")
            contents_dir.mkdir(parents=True, exist_ok=True)
            
            # ファイル名の生成
            file_path = contents_dir / f"{today.strftime('%Y-%m-%d')}.md"
            print(f"保存先ファイルパス: {file_path}")
            
            # Markdownファイルの作成
            content = f"# SNS投稿文 ({today.strftime('%Y-%m-%d')})\n\n"
            
            for post in posts:
                content += f"## {post['title']}\n\n"
                content += f"- URL: {post['url']}\n"
                content += f"- 文字数: {post['char_count']}\n\n"
                content += f"```\n{post['content']}\n```\n\n"
                content += "---\n\n"
            
            # ファイルに保存
            file_path.parent.mkdir(parents=True, exist_ok=True)  # 親ディレクトリを作成
            file_path.write_text(content, encoding='utf-8')
            
            print(f"Social posts saved to: {file_path}")
            
        except Exception as e:
            print(f"Error storing social posts: {str(e)}")


if __name__ == "__main__":
    tech_feed = TechFeed()
    tech_feed.run(days=1, limit=3) 