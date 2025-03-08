# TechFeedサービス ドキュメント

## 概要

`TechFeed`クラスは、技術ブログのRSSフィードを監視・収集し、記事の内容を日本語に翻訳して要約するサービスです。また、SNS投稿用の文章を生成し、指定されたディレクトリに保存する機能も提供します。

## 主要コンポーネント

### 1. Article データクラス

```python
@dataclass
class Article:
    feed_name: str
    title: str
    url: str
    text: str
    soup: BeautifulSoup
    category: Optional[str] = None
    summary: str = field(default="")
    social_post: str = field(default="")  # SNS投稿用の文章
    social_post_char_count: int = field(default=0)  # 投稿文の文字数
```

技術ブログの記事情報を格納するデータクラスです。

- **feed_name**: フィード名（ブログ名）
- **title**: 記事のタイトル
- **url**: 記事のURL
- **text**: 記事の本文
- **soup**: BeautifulSoupオブジェクト（HTMLパース結果）
- **category**: 記事のカテゴリ（オプション）
- **summary**: 記事の要約（デフォルトは空文字列）
- **social_post**: SNS投稿用の文章（デフォルトは空文字列）
- **social_post_char_count**: 投稿文の文字数（デフォルトは0）

### 2. TechFeed クラス

技術ブログのRSSフィードを監視・収集・要約する主要クラスです。

#### 初期化

```python
def __init__(self, storage_dir: str = "data"):
    self.storage = LocalStorage(storage_dir)
    self.grok_client = Grok3Client()
    
    # フィードの設定を読み込む
    script_dir = Path(__file__).parent
    with open(script_dir / "feed.toml", "rb") as f:
        self.feed_config = tomli.load(f)
```

- **storage_dir**: データを保存するディレクトリのパス（デフォルト: "data"）
- **storage**: `LocalStorage`クラスのインスタンス（ファイル操作を担当）
- **grok_client**: `Grok3Client`クラスのインスタンス（LLMによる翻訳・要約を担当）
- **feed_config**: RSSフィードの設定（feed.tomlから読み込み）

#### 主要メソッド

##### run(days: int = 1, limit: int = 3) -> None

```python
def run(days: int = 1, limit: int = 3) -> None:
```

サービスの主要エントリーポイント。以下の処理を実行します：

1. 各カテゴリのRSSフィードから記事を取得
2. 指定した日数内の新しい記事をフィルタリング
3. 各記事の内容を取得し、日本語に翻訳
4. 記事を要約
5. 結果をMarkdownファイルとして保存

- **days**: 何日前までの記事を取得するか（デフォルト: 1）
- **limit**: 各フィードから取得する記事数（デフォルト: 3）

##### _filter_entries(entries: List[dict], days: int, limit: int) -> List[dict]

```python
def _filter_entries(self, entries: List[dict], days: int, limit: int) -> List[dict]:
```

新しいエントリをフィルタリングするプライベートメソッド。

1. 指定した日数内の記事を抽出
2. 日付情報がない記事も含める
3. 最新の記事を指定した数だけ返却

- **entries**: エントリのリスト
- **days**: 何日前までの記事を取得するか
- **limit**: 取得する記事数
- **戻り値**: フィルタリングされたエントリのリスト

##### _retrieve_article(entry: dict, feed_name: str, category: str) -> Optional[Article]

```python
def _retrieve_article(self, entry: dict, feed_name: str, category: str) -> Optional[Article]:
```

記事を取得するプライベートメソッド。

1. エントリからURLとタイトルを取得
2. 記事のHTMLコンテンツを取得
3. BeautifulSoupを使用してHTMLをパース
4. 記事の本文を抽出（要約、メタディスクリプション、または最初の段落）
5. タイトルと本文を日本語に翻訳
6. `Article`オブジェクトを返却

- **entry**: エントリ情報
- **feed_name**: フィード名
- **category**: カテゴリ
- **戻り値**: 取得した記事（取得に失敗した場合はNone）

##### _translate_to_japanese(text: str) -> str

```python
def _translate_to_japanese(self, text: str) -> str:
```

テキストを日本語に翻訳するプライベートメソッド。

1. Grok3Clientを使用して翻訳
2. 技術用語は適切に翻訳し、必要に応じて英語の専門用語を括弧内に残す

- **text**: 翻訳するテキスト
- **戻り値**: 翻訳されたテキスト

##### _summarize_article(article: Article) -> None

```python
def _summarize_article(self, article: Article) -> None:
```

記事を要約するプライベートメソッド。

1. 記事のタイトルと本文を使用して要約プロンプトを作成
2. Grok3Clientを使用して要約を生成
3. 要約結果を`article.summary`に設定

- **article**: 要約する記事

##### _store_summaries(articles: List[Article]) -> None

```python
def _store_summaries(self, articles: List[Article]) -> None:
```

要約を保存するプライベートメソッド。

1. カテゴリごとに記事を整理
2. Markdownフォーマットで記事情報を整形
   - カテゴリごとにセクション分け
   - 記事ごとにタイトル、フィード名、要約を記載
3. LocalStorageを使用してMarkdownファイルを保存

- **articles**: 保存する記事のリスト

##### _create_social_post(article: Article) -> str

```python
def _create_social_post(self, article: Article) -> str:
```

記事からSNS投稿用の文章を生成するプライベートメソッド。

1. 記事のタイトルと本文を使用して投稿文生成プロンプトを作成
2. Grok3Clientを使用して投稿文を生成
3. 生成された文章は以下のルールに従う：
   - 180-200文字の範囲内
   - 3文で構成
   - 最初の文は「自分用メモ。」
   - 2番目の文は「この記事は」で始まり「を解説。」で終わる
   - 3番目の文は「最も重要なポイントは」で始まり「と説明している。」で終わる

- **article**: 投稿文を生成する記事
- **戻り値**: 生成された投稿用文章

##### _store_social_posts(posts: List[dict]) -> None

```python
def _store_social_posts(self, posts: List[dict]) -> None:
```

生成された投稿用文章を保存するプライベートメソッド。

1. 環境変数`CONTENTS_DIR`から保存先ディレクトリを取得
2. 日付ベースのファイル名を生成
3. 各投稿を以下の形式で保存：
   ```
   投稿文 URL
   ---
   ```

- **posts**: 投稿情報のリスト（各要素は`url`、`title`、`content`、`char_count`を含む辞書）

## 依存関係

### 外部ライブラリ

- **feedparser**: RSSフィードの解析
- **requests**: HTTPリクエスト送信
- **BeautifulSoup**: HTMLパース
- **tomli**: TOMLファイル読み込み

### 内部モジュール

- **nook.common.storage.LocalStorage**: ファイル操作
- **nook.common.grok_client.Grok3Client**: LLMによる翻訳・要約

## 設定ファイル

### feed.toml

収集対象のRSSフィードを定義するTOMLファイル。

```toml
# 技術ブログ
tech_blogs = [
    "https://engineering.atspotify.com/feed/",
    "https://netflixtechblog.com/feed",
    "https://blog.cloudflare.com/rss/",
    # ...
]

# AI/ML関連
ai_ml = [
    "https://ai.googleblog.com/feeds/posts/default",
    "https://openai.com/blog/rss/",
    # ...
]

# プログラミング言語
programming = [
    "https://blog.rust-lang.org/feed.xml",
    "https://blog.python.org/feeds/posts/default",
    # ...
]

# 日本語のテック情報
zenn = [
    "https://zenn.dev/topics/cursor/feed",
    "https://zenn.dev/topics/langchain/feed",
    # ...
]

qitta = [
    "http://qiita.com/tags/AI/feed.atom",
    "http://qiita.com/tags/LLM/feed.atom",
    # ...
]
```

## 出力形式

サービスは2種類のファイルを生成します：

### 1. 要約ファイル（tech_feed/YYYY-MM-DD.md）

```markdown
# 技術ブログ記事 (YYYY-MM-DD)

## カテゴリ名

### [記事タイトル](記事URL)

**フィード**: フィード名

**要約**:
1. 記事の主な内容（1-2文）
2. 重要なポイント（箇条書き3-5点）
3. 技術的な洞察

---

（以下、他の記事情報が続く）
```

### 2. 投稿ファイル（CONTENTS_DIR/YYYY-MM-DD.md）

```markdown
投稿文 URL
---
投稿文 URL
---
（以下、他の投稿が続く）
```

## 使用例

```python
# 基本的な使用法
tech_feed = TechFeed()
tech_feed.run()  # デフォルトで1日以内の記事を各フィードから3件まで取得

# カスタム設定
tech_feed = TechFeed(storage_dir="custom_data")
tech_feed.run(days=3, limit=5)  # 3日以内の記事を各フィードから5件まで取得
```

## エラーハンドリング

- フィード処理中にエラーが発生した場合、エラーメッセージを出力し、次のフィードの処理を続行
- 記事取得中にエラーが発生した場合、エラーメッセージを出力し、Noneを返却
- 翻訳中にエラーが発生した場合、エラーメッセージを出力し、原文を返却
- 要約中にエラーが発生した場合、エラーメッセージを要約として設定
- 保存中にエラーが発生した場合、ディレクトリを作成して再試行

## 技術的詳細

1. **RSSフィード解析**: feedparserを使用してRSSフィードを解析
2. **HTML解析**: BeautifulSoupを使用して記事のHTMLを解析
3. **翻訳**: Grok3Client（X.AI API）を使用してタイトルと本文を日本語に翻訳
4. **要約**: Grok3Client（X.AI API）を使用して記事を要約
5. **保存**: LocalStorageを使用してMarkdownファイルとして保存

## まとめ

TechFeedサービスは、技術ブログのRSSフィードを監視・収集し、記事の内容を日本語に翻訳して要約するサービスです。このサービスにより、開発者は様々な技術ブログの最新情報を簡単に把握することができます。 