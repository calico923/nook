# tech_feed.py 機能追加計画

## 1. 現状分析

### 既存の機能
- RSSフィードから技術ブログの記事を取得
- 記事の内容を要約（_summarize_article）
- 要約結果をMarkdownファイルとして保存（_store_summaries）

### 追加要件
1. _summarize_articleの結果を元に、さらに要約を生成
2. 生成された要約を指定ディレクトリに保存

## 2. 実装計画

### 2.1 新規メソッドの追加

#### `_create_social_post`メソッド
```python
def _create_social_post(self, summary: str, url: str) -> str:
    """
    要約からSNSポスト用の文章を生成する。

    Parameters
    ----------
    summary : str
        _summarize_articleで生成された要約。
    url : str
        記事のURL。

    Returns
    -------
    str
        生成された投稿用文章。
    """
```

#### `_store_social_posts`メソッド
```python
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
            'content': str
        }
    """
```

### 2.2 既存メソッドの修正

#### `_summarize_article`メソッドの拡張
- 要約生成後に`_create_social_post`を呼び出す
- 生成された投稿用文章をArticleクラスに保存

#### `Article`クラスの拡張
```python
@dataclass
class Article:
    # 既存のフィールド
    social_post: str = field(default="")  # 追加
```

#### `run`メソッドの修正
- 記事の要約後に`_store_social_posts`を呼び出す

## 3. 実装手順

1. Articleクラスの拡張
   - social_postフィールドの追加

2. _create_social_postメソッドの実装
   - プロンプトテンプレートの作成
   - Grok3Clientを使用した文章生成
   - 生成された文章の検証

3. _store_social_postsメソッドの実装
   - CONTENTS_DIRからの保存先パスの生成
   - Markdownファイルの作成
   - 投稿内容の書き込み

4. _summarize_articleメソッドの修正
   - social_post生成の追加
   - Articleオブジェクトへの保存

5. runメソッドの修正
   - social_postsの収集
   - _store_social_postsの呼び出し

## 4. エラーハンドリング

- CONTENTS_DIRが存在しない場合の処理
- 文章生成APIのエラー処理
- ファイル書き込みエラーの処理

## 5. テスト計画

1. ユニットテスト
   - _create_social_postのテスト
   - _store_social_postsのテスト
   - 修正された_summarize_articleのテスト

2. 統合テスト
   - 全体のワークフローテスト
   - エラーケースのテスト

## 6. 実装スケジュール

1. 基本実装（2時間）
   - クラス拡張
   - 新規メソッド実装

2. テスト実装（1.5時間）
   - ユニットテスト作成
   - 統合テスト作成

3. デバッグと調整（1時間）
   - エラーケース対応
   - パフォーマンス調整

4. ドキュメント作成（0.5時間）
   - コードコメント
   - README更新

合計予定時間: 5時間

## 7. 注意点

1. 既存機能への影響を最小限に抑える
2. エラーハンドリングを適切に実装
3. テストカバレッジの維持
4. パフォーマンスへの影響を考慮 