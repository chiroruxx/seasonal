---
name: document-writing
description: Create or update Seasonal documentation from a user request and its supporting decisions or specifications. Apply document formats and verify Markdown; use document-review for independent review, not authorship.
---

# 文書作成

`AGENTS.md` と、依頼の目的・対象・変更範囲・根拠を確認する。本文のパスはプロジェクトルート基準。

## 根拠と構成

- 根拠は、ユーザーの明示的な決定、依頼で指定された資料、既存の確定仕様を区別して扱う。曖昧な内容を「合意済み」としない。判断が必要ならメインへ返す。
- 決定事項・提案・経緯・実装済みの事実を混同しない。文書の目的と読み手に必要な情報を記載する。
- 対象ファイルのディレクトリからリポジトリルートまでの祖先にある `FORMAT.md` を確認する。ルート側から読み、近いディレクトリの具体的な指定を優先する。兄弟ディレクトリの形式は適用しない。
- 適用する `FORMAT.md` がなければ、依頼内容と同種の既存文書に沿って構成する。形式の新設・変更は依頼範囲に含まれる場合だけ行う。
- `docs/` のうち `docs/stories/` を除く文書には決定事項を記載し、経緯・比較案・未確定事項を混ぜない。
- `docs/design/` のデザインシステムには、個別ページの表示仕様を混ぜない。

## 編集と検証

- 本文の意味・読みやすさ・用語を整え、関連文書とリンク・画像参照を確認する。
- 改行用の行末スペース2つを保持し、機械的な折り返しで日本語の意味を変えない。
- formatter・linter は hooks が実行するため、手動で重複実行しない。失敗の通知には修正で対応し、hooks が発火しない場合は環境の不備としてメインへ報告する。結果の妥当性は reviewer が確認する。
- formatter の純粋な整形変更は許可される。内容や意味の変更に必要な承認は `AGENTS.md` に従う。
- 生データの収集・加工は文書作成に含めない。調査報告の文章と、取得データを区別する。

変更した文書、根拠、適用した形式、失敗通知への対応、未確認事項を報告し、独立レビューに渡す。
