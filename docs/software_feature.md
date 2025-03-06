# Nook - ディレクトリ構造と機能概要

## プロジェクト概要

Nookは、様々なソースから情報を収集し、要約・整理して提供するインテリジェントな情報収集・管理システムです。GitHub、Hacker News、Reddit、技術ブログ、arXiv論文などから情報を収集し、Grok APIを使用して要約を生成します。

## ディレクトリ構造

```
nook/
├── api/                  # バックエンドAPI
│   ├── models/           # データモデル定義
│   └── routers/          # APIエンドポイント
├── cli/                  # コマンドラインインターフェース
├── common/               # 共通ユーティリティ
├── frontend/             # フロントエンドUI
│   ├── components/       # UIコンポーネント
│   ├── pages/            # ページレイアウト
│   └── utils/            # フロントエンド用ユーティリティ
└── services/             # 各種情報収集サービス
    ├── github_trending/  # GitHubトレンド収集
    ├── hacker_news/      # Hacker News記事収集
    ├── paper_summarizer/ # arXiv論文収集・要約
    ├── reddit_explorer/  # Reddit投稿収集
    ├── tech_feed/        # 技術ブログRSS収集
    └── twitter_poster/   # Twitter投稿機能（現在未使用）
```

## 主要コンポーネントの機能

### 1. 共通モジュール (`nook/common/`)

- **config.py**: 環境変数からの設定読み込みと管理
- **storage.py**: ローカルファイルシステムでのデータ操作
- **grok_client.py**: Grok API（OpenAI互換）とのインターフェース

### 2. 情報収集サービス (`nook/services/`)

- **github_trending/github_trending.py**: GitHubのトレンドリポジトリを収集
- **hacker_news/hacker_news.py**: Hacker Newsの人気記事を収集
- **paper_summarizer/paper_summarizer.py**: arXiv論文を収集・要約
- **reddit_explorer/reddit_explorer.py**: Redditの人気投稿を収集・要約
- **tech_feed/tech_feed.py**: 技術ブログのRSSフィードを監視・収集・要約
- **run_services.py**: 各サービスを実行するためのスクリプト

### 3. コマンドラインインターフェース (`nook/cli/`)

- **main.py**: コマンドラインからサービスを実行するためのインターフェース

### 4. API (`nook/api/`)

- **main.py**: FastAPIアプリケーションの定義
- **routers/**: 各種APIエンドポイント
  - **content.py**: 収集したコンテンツを提供するAPI
  - **chat.py**: チャット機能のAPI
  - **weather.py**: 天気情報のAPI

### 5. フロントエンド (`nook/frontend/`)

- **app.py**: Streamlitフロントエンドアプリケーション
- **components/**: UIコンポーネント
- **pages/**: アプリケーションの各ページ

## データフロー

1. 各サービス（GitHub、Hacker News、Reddit、技術ブログ、arXiv）からデータを収集
2. Grok APIを使用して収集したデータを要約・翻訳
3. 要約されたデータをMarkdownファイルとしてローカルストレージに保存
4. APIを通じてフロントエンドにデータを提供
5. フロントエンドでデータを表示・操作

## 設定

- 環境変数は `.env` ファイルで管理
- 主要な設定項目:
  - API キー（OpenAI、Grok、Reddit、OpenWeatherMap）
  - フロントエンド・バックエンド設定
  - データストレージディレクトリ（`DATA_DIR`）

## データストレージ

- 収集・要約されたデータは `DATA_DIR` 環境変数で指定されたディレクトリに保存
- 各サービスごとにサブディレクトリが作成され、日付ごとにMarkdownファイルとして保存
- デフォルトでは `data/` ディレクトリに保存 