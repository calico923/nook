# tech_feed.py 機能追加計画

## 1. 現状分析

### 既存の機能
- RSSフィードから技術ブログの記事を取得
- 記事の内容を要約（_summarize_article）
- 要約結果をMarkdownファイルとして保存（_store_summaries）

### 追加要件
1. 記事の内容から247-257文字のSNS投稿用文章を生成
2. 生成された投稿文を指定ディレクトリに保存

## 2. 実装計画

### 2.1 新規メソッドの追加

#### `_create_social_post`メソッド
```python
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
        生成された投稿用文章。文字数制限は180-200文字をGrokに指示しますが、
        出力の文字数チェックは行いません。
    """
    prompt = f"""
        以下の{{技術ブログの記事}}からX投稿用文を作成してください。
        ただし次の{{ルール}}は必ず守ってください。

        # ルール
        X投稿用文は以下のルールを守って日本語で回答してください。
            ・X投稿用文は【必ず180-200文字の範囲内】で作成すること
            ・X投稿用文は【3文】で作成すること
            ・最初の一文は【必ず「自分用メモ。」】と作成すること           
            ・2番目の文は【「この記事は」から始め、その文は「を解説。」】で終わること
            ・3番目の文は【「最も重要なポイントは」】ではじめ、記事で最も重要なポイントを説明し、【と説明している。】で終わること
            ・箇条書きは使用しないこと
            ・作成後、必ず文字数をカウントして180-200文字の範囲内であることを確認すること

        # 技術ブログの記事
                タイトル: {article.title}
                本文: {article.text[:2000]}
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
        return social_post
    except Exception as e:
        print(f"Error generating social post: {str(e)}")
        return ""
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
            'content': str,
            'char_count': int  # 文字数
        }
    """
```

### 2.2 既存メソッドの修正

#### `_summarize_article`メソッドの拡張
- 要約生成後に`_create_social_post`を呼び出す
- 生成された投稿用文章をArticleクラスに保存
- 文字数制限のバリデーション追加

#### `Article`クラスの拡張
```python
@dataclass
class Article:
    # 既存のフィールド
    social_post: str = field(default="")  # 追加
    social_post_char_count: int = field(default=0)  # 文字数
```

#### `run`メソッドの修正
- 記事の要約後に`_store_social_posts`を呼び出す
- 文字数制限外の投稿は警告ログを出力

## 3. 実装手順

1. Articleクラスの拡張
   - social_postフィールドの追加
   - social_post_char_countフィールドの追加

2. _create_social_postメソッドの実装
   - 新しいプロンプトとシステムインストラクションの実装
   - Grok3Clientを使用した文章生成
   - 文字数制限のバリデーション
   - 生成された文章の検証

3. _store_social_postsメソッドの実装
   - CONTENTS_DIRからの保存先パスの生成
   - Markdownファイルの作成
   - 投稿内容と文字数の書き込み

4. _summarize_articleメソッドの修正
   - social_post生成の追加
   - 文字数チェックの追加
   - Articleオブジェクトへの保存

5. runメソッドの修正
   - social_postsの収集
   - 文字数制限外の投稿の警告
   - _store_social_postsの呼び出し

## 4. エラーハンドリング

- CONTENTS_DIRが存在しない場合の処理
- 文章生成APIのエラー処理
- ファイル書き込みエラーの処理
- 文字数制限外の場合の処理
  - 警告ログの出力
  - 再生成オプションの提供

## 5. テスト計画

1. ユニットテスト
   - _create_social_postのテスト
     - 文字数制限の検証
     - 冒頭文の「〜話。」の検証
   - _store_social_postsのテスト
   - 修正された_summarize_articleのテスト

2. 統合テスト
   - 全体のワークフローテスト
   - エラーケースのテスト
   - 文字数制限のエッジケーステスト

## 6. 実装スケジュール

1. 基本実装（2.5時間）
   - クラス拡張
   - 新規メソッド実装
   - 文字数制限の実装

2. テスト実装（2時間）
   - ユニットテスト作成
   - 統合テスト作成
   - 文字数制限のテスト

3. デバッグと調整（1時間）
   - エラーケース対応
   - パフォーマンス調整
   - 文字数制限の微調整

4. ドキュメント作成（0.5時間）
   - コードコメント
   - README更新

合計予定時間: 6時間

## 7. 注意点

1. 既存機能への影響を最小限に抑える
2. エラーハンドリングを適切に実装
3. テストカバレッジの維持
4. 文字数制限の厳密な管理
5. パフォーマンスへの影響を考慮 