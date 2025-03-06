# Nook - 改善計画

## 1. データストレージ設定の問題と修正

### 現在の問題点

`.env` ファイルで `DATA_DIR` 環境変数を設定しても、以下のサービスでファイルが指定したディレクトリに保存されない問題がありました：

- `github_trending`
- `paper_summarizer`
- `tech_feed`

### 原因

各サービスクラスの初期化時に、デフォルト値として `storage_dir = "data"` が設定されていました。これにより、環境変数 `DATA_DIR` の設定が反映されず、常にデフォルトの `"data"` ディレクトリにファイルが保存されていました。

`LocalStorage` クラスは、`base_dir` パラメータが `None` の場合にのみ環境変数から設定を取得します：

```python
def __init__(self, base_dir: Optional[str] = None):
    if base_dir is None:
        self.base_dir = get_data_dir()  # 環境変数から取得
    else:
        self.base_dir = Path(base_dir)  # 指定されたパスを使用
```

### 実施した修正

以下のファイルを修正して、各サービスクラスの初期化時に `storage_dir=None` を渡すようにしました：

1. `nook/services/run_services.py`
2. `nook/cli/main.py`

修正例：
```python
# 修正前
github_trending = GithubTrending()

# 修正後
github_trending = GithubTrending(storage_dir=None)
```

## 2. 今後の改善計画

### 2.1 コード構造の改善

#### 2.1.1 基底クラスの導入

各サービスクラスに共通する機能を持つ基底クラス `ServiceBase` を導入します：

```python
class ServiceBase:
    """
    サービスの基底クラス。
    
    Parameters
    ----------
    storage_dir : Optional[str], default=None
        ストレージディレクトリのパス。指定しない場合は環境変数から取得。
    """
    
    def __init__(self, storage_dir: Optional[str] = None):
        """
        ServiceBaseを初期化します。
        
        Parameters
        ----------
        storage_dir : Optional[str], default=None
            ストレージディレクトリのパス。指定しない場合は環境変数から取得。
        """
        self.storage = LocalStorage(storage_dir)
```

各サービスクラスはこの基底クラスを継承することで、共通の機能を再利用できます：

```python
class GithubTrending(ServiceBase):
    def __init__(self, storage_dir: Optional[str] = None):
        super().__init__(storage_dir)
        # 追加の初期化処理
```

#### 2.1.2 サービスクラスのデフォルト値の修正

各サービスクラスのデフォルト値を `storage_dir: Optional[str] = None` に変更します：

```python
# 修正前
def __init__(self, storage_dir: str = "data"):
    self.storage = LocalStorage(storage_dir)

# 修正後
def __init__(self, storage_dir: Optional[str] = None):
    self.storage = LocalStorage(storage_dir)
```

これにより、明示的に `storage_dir=None` を指定しなくても環境変数から設定を取得できるようになります。

### 2.2 設定管理の改善

#### 2.2.1 設定管理クラスの導入

環境変数の読み込みと設定の取得を一元管理するための設定管理クラスを導入します：

```python
class AppConfig:
    """
    アプリケーション設定を管理するクラス。
    """
    
    def __init__(self, env_file: Optional[str] = None):
        """
        AppConfigを初期化します。
        
        Parameters
        ----------
        env_file : Optional[str], default=None
            環境変数ファイルのパス。指定しない場合はデフォルトの.envを使用。
        """
        self.load_env_file(env_file)
    
    def load_env_file(self, env_file: Optional[str] = None) -> None:
        """
        環境変数ファイルを読み込みます。
        
        Parameters
        ----------
        env_file : Optional[str], default=None
            環境変数ファイルのパス。指定しない場合はデフォルトの.envを使用。
        """
        if env_file and os.path.exists(env_file):
            load_dotenv(env_file, override=True)
        else:
            load_dotenv(override=True)
    
    def get_data_dir(self) -> Path:
        """
        データディレクトリのパスを取得します。
        
        Returns
        -------
        Path
            データディレクトリのパス
        """
        data_dir = Path(os.getenv("DATA_DIR", "data"))
        data_dir.mkdir(parents=True, exist_ok=True)
        return data_dir
    
    # その他の設定項目を追加
```

#### 2.2.2 設定の検証機能の追加

環境変数の設定が正しいかどうかを検証する機能を追加します：

```python
def validate_config(self) -> List[str]:
    """
    設定を検証します。
    
    Returns
    -------
    List[str]
        検証エラーのリスト。エラーがない場合は空のリスト。
    """
    errors = []
    
    # データディレクトリの検証
    data_dir = self.get_data_dir()
    if not data_dir.exists():
        errors.append(f"データディレクトリが存在しません: {data_dir}")
    elif not os.access(data_dir, os.W_OK):
        errors.append(f"データディレクトリに書き込み権限がありません: {data_dir}")
    
    # APIキーの検証
    if not os.getenv("GROK_API_KEY"):
        errors.append("GROK_API_KEYが設定されていません")
    
    # その他の設定項目の検証
    
    return errors
```

### 2.3 テストの改善

#### 2.3.1 ユニットテストの追加

設定の読み込みと保存先ディレクトリの動作を自動的に検証するためのユニットテストを追加します：

```python
def test_local_storage_with_env_var():
    """
    環境変数を使用したLocalStorageのテスト。
    """
    # 環境変数を一時的に設定
    os.environ["DATA_DIR"] = "/tmp/test_data"
    
    # LocalStorageを初期化
    storage = LocalStorage()
    
    # 保存先ディレクトリが環境変数の値と一致することを確認
    assert str(storage.base_dir) == "/tmp/test_data"
    
    # ファイルを保存
    content = "# テスト\n\nこれはテストファイルです。"
    file_path = storage.save_markdown(content, "test_service")
    
    # ファイルが存在することを確認
    assert file_path.exists()
    
    # ファイルの内容が正しいことを確認
    with open(file_path, "r", encoding="utf-8") as f:
        assert f.read() == content
```

#### 2.3.2 統合テストの追加

各サービスクラスが正しくデータを保存できることを検証する統合テストを追加します：

```python
def test_service_integration():
    """
    サービスクラスの統合テスト。
    """
    # 環境変数を一時的に設定
    os.environ["DATA_DIR"] = "/tmp/test_data"
    
    # GitHubTrendingのテスト
    github_trending = GithubTrending()
    
    # モックデータを作成
    repositories_by_language = [
        ("python", [
            type("Repository", (), {"name": "テストリポジトリ", "link": "https://github.com/test/repo", 
                                  "description": "テスト用リポジトリ", "stars": "100"})()
        ])
    ]
    
    # 保存処理を実行
    github_trending._store_summaries(repositories_by_language)
    
    # ファイルが存在することを確認
    file_path = Path("/tmp/test_data/github_trending")
    assert file_path.exists()
    assert any(file_path.glob("*.md"))
```

### 2.4 エラーハンドリングの改善

#### 2.4.1 例外処理の強化

ファイル操作時の例外処理を強化します：

```python
def save_markdown(self, content: str, service_name: str, date: Optional[datetime] = None) -> Path:
    """
    Markdownコンテンツを保存します。
    
    Parameters
    ----------
    content : str
        保存するMarkdownコンテンツ。
    service_name : str
        サービス名（ディレクトリ名）。
    date : datetime, optional
        日付。指定しない場合は現在の日付。
        
    Returns
    -------
    Path
        保存されたファイルのパス。
        
    Raises
    ------
    IOError
        ファイルの保存に失敗した場合。
    """
    if date is None:
        date = datetime.now()
    
    date_str = date.strftime("%Y-%m-%d")
    service_dir = self.base_dir / service_name
    
    try:
        service_dir.mkdir(parents=True, exist_ok=True)
        
        file_path = service_dir / f"{date_str}.md"
        
        with open(file_path, "w", encoding="utf-8") as f:
            f.write(content)
        
        return file_path
    except IOError as e:
        logging.error(f"ファイルの保存に失敗しました: {str(e)}")
        raise
```

#### 2.4.2 ロギングの強化

詳細なログ出力を追加して、問題の診断を容易にします：

```python
def __init__(self, base_dir: Optional[str] = None):
    """
    LocalStorageを初期化します。
    
    Parameters
    ----------
    base_dir : str, optional
        ベースディレクトリのパス。指定しない場合は環境変数から取得。
    """
    if base_dir is None:
        self.base_dir = get_data_dir()
        logging.info(f"環境変数から取得したデータディレクトリ: {self.base_dir}")
    else:
        self.base_dir = Path(base_dir)
        logging.info(f"指定されたデータディレクトリ: {self.base_dir}")
    
    try:
        self.base_dir.mkdir(parents=True, exist_ok=True)
        logging.info(f"データディレクトリを確認/作成しました: {self.base_dir}")
    except Exception as e:
        logging.error(f"データディレクトリの作成に失敗しました: {str(e)}")
        raise
```

## 3. 実装スケジュール

1. **フェーズ1: 基本的な修正**（1週間）
   - サービスクラスのデフォルト値の修正
   - 基底クラスの導入

2. **フェーズ2: 設定管理の改善**（1週間）
   - 設定管理クラスの導入
   - 設定の検証機能の追加

3. **フェーズ3: テストの追加**（2週間）
   - ユニットテストの追加
   - 統合テストの追加

4. **フェーズ4: エラーハンドリングの改善**（1週間）
   - 例外処理の強化
   - ロギングの強化

5. **フェーズ5: ドキュメントの更新**（1週間）
   - コードドキュメントの更新
   - ユーザーマニュアルの更新 