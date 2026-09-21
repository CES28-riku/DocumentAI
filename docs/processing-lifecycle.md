# 処理状態と再実行履歴

## なぜ必要か

Document AIの処理は、ファイルを保存しただけでは終わりません。テキスト抽出、OCR、項目抽出、検証など、失敗する可能性がある処理が続きます。

失敗を単にエラー表示するだけでは、次のことが分かりません。

- どの処理で失敗したか
- いつ失敗したか
- 何回実行したか
- 再実行後に成功したか

そこで「現在の状態」と「各実行の履歴」を分けて保存します。

## 状態遷移とは

状態遷移は、対象が現在どの段階にあり、次にどの状態へ移れるかを決めるルールです。

今回の基本的な流れ：

```text
uploaded → processing → completed
                  ├──→ needs_review
                  └──→ failed

failed ──再実行──→ processing
needs_review ──再実行──→ processing
```

## documents.status

`documents.status` には、その文書の現在状態だけを保存します。

| 状態 | 意味 |
| --- | --- |
| `uploaded` | ファイル登録済み、処理開始前 |
| `processing` | 現在処理中 |
| `completed` | 処理と検証が正常終了 |
| `needs_review` | 結果はあるが人の確認が必要 |
| `failed` | 処理を完了できなかった |

ここには過去の失敗内容を上書きして保存しません。

## processing_runs

`processing_runs` は、処理を実行するたびに1行追加する履歴テーブルです。

主な情報：

- `id`: 実行を識別する番号
- `document_id`: 処理対象の文書ID
- `attempt_number`: 何回目の実行か
- `status`: この実行の結果
- `started_at`: 開始日時
- `finished_at`: 終了日時
- `error_code`: 機械的に判定するエラーコード
- `error_message`: 人が確認するエラー内容

## 最小例

1回目のOCRが失敗し、2回目の再実行で成功した場合：

```text
documents
  id=1, status=completed

processing_runs
  id=1, document_id=1, attempt_number=1, status=failed
  id=2, document_id=1, attempt_number=2, status=completed
```

`documents` を見れば現在は成功していると分かり、`processing_runs` を見れば過去に1度失敗したことも分かります。

## エラーコードとメッセージを分ける理由

例：

```text
error_code    = UNSUPPORTED_FILE_TYPE
error_message = application/zip は処理できません
```

プログラムは安定した `error_code` を使って処理を分岐できます。人は詳しい `error_message` を読んで原因を確認できます。

## 再実行の基本ルール

- `failed` または `needs_review` の文書を再実行できる
- 再実行時は古い履歴を更新せず、新しい実行履歴を追加する
- 同じ文書を再アップロードするのではなく、既存の文書に新しい実行を関連付ける
- 処理開始時に文書の現在状態を `processing` にする
- 処理結果に応じて `completed`、`needs_review`、`failed` のいずれかにする

## 今回は決めないこと

- 処理を同期実行するか、キューで非同期実行するか
- OCRエンジンの種類
- エラーコードの完全な一覧
- 同時実行を防ぐ具体的なデータベース制約
- 人が確認した結果の保存方法

