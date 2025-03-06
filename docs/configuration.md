# 設定ガイド

このドキュメントでは、Nookアプリケーションの設定方法について説明します。

## 環境変数

アプリケーションの設定は環境変数で管理されています。`.env.example`ファイルを`.env`にコピーして、必要な設定を行ってください。

```bash
cp .env.example .env
```

### 主な環境変数

| 環境変数 | 説明 | デフォルト値 |
|---------|------|------------|
| `OPENAI_API_KEY` | OpenAI APIのキー | - |
| `OPENWEATHERMAP_API_KEY` | OpenWeatherMap APIのキー | - |
| `GROK_API_KEY` | Grok APIのキー | - |
| `REDDIT_CLIENT_ID` | Reddit APIのクライアントID | - |
| `REDDIT_CLIENT_SECRET` | Reddit APIのクライアントシークレット | - |
| `REDDIT_USER_AGENT` | Reddit APIのユーザーエージェント | - |
| `NEXT_PUBLIC_API_URL` | フロントエンドからバックエンドへのアクセスURL | `http://localhost:8000` |
| `PORT` | バックエンドのポート番号 | `8000` |
| `HOST` | バックエンドのホスト | `0.0.0.0` |
| `DATA_DIR` | データ保存ディレクトリ | `data` |

## データディレクトリ

アプリケーションは、収集したデータを`DATA_DIR`環境変数で指定されたディレクトリに保存します。デフォルトでは`data`ディレクトリが使用されます。

### カスタムデータディレクトリの設定

カスタムのデータディレクトリを使用する場合は、`.env`ファイルに以下のように設定してください：

```
DATA_DIR=custom_data
```

### 複数の環境設定

異なる環境（開発、テスト、本番など）で異なるデータディレクトリを使用したい場合は、複数の環境変数ファイルを作成することができます：

```bash
# 開発環境用
.env.development

# テスト環境用
.env.test

# 本番環境用
.env.production
```

CLIツールを実行する際に`--env-file`オプションで環境変数ファイルを指定することができます：

```bash
# 開発環境で実行
python -m nook.cli.main --env-file .env.development hackernews

# テスト環境で実行
python -m nook.cli.main --env-file .env.test hackernews

# 本番環境で実行
python -m nook.cli.main --env-file .env.production hackernews
```

## プログラムでの設定の使用

アプリケーションのコードから設定を使用するには、`nook.common.config`モジュールをインポートします：

```python
from nook.common.config import get_data_dir

# データディレクトリのパスを取得
data_dir = get_data_dir()
```

環境変数ファイルを明示的に読み込む場合は、`load_env_file`関数を使用します：

```python
from nook.common.config import load_env_file, get_data_dir

# テスト環境の設定を読み込む
load_env_file(".env.test")

# データディレクトリのパスを取得（テスト環境の設定が反映される）
data_dir = get_data_dir()
``` 