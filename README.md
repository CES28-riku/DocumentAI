# Technical Document Intelligence

請求書を、確認可能な業務データへ変換するDocument AIポートフォリオです。

## 現在の段階

Phase 1（文書取込基盤）です。現在は、アップロードされたファイルのメタデータとSHA-256を返す最小APIまで実装しています。

現在の設計資料：

- [MVP要件](docs/requirements.md)
- [データモデル設計 1](docs/data-model.md)
- [処理状態と再実行履歴](docs/processing-lifecycle.md)

## ローカルでの実行

```bash
python -m venv .venv
source .venv/bin/activate
pip install -e '.[test]'
uvicorn app.main:app --reload
```

起動後、`http://127.0.0.1:8000/docs` からファイルをアップロードできます。

## テスト

```bash
python -m pytest
```
