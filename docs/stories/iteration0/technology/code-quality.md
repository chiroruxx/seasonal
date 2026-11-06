# 静的解析と整形

## 使用するツール

| 対象                      | 役割                                 | ツール            |
| ------------------------- | ------------------------------------ | ----------------- |
| Kotlin・Gradle Kotlin DSL | 自動整形と整形状態の検査             | Spotless + ktfmt  |
| Android                   | API・リソースなどの静的解析          | Android Lint      |
| Markdown                  | 見出し・リスト・リンク表記などの検査 | markdownlint-cli2 |
| Markdown                  | 自動整形と整形状態の検査             | Prettier          |
| エディター                | 改行・インデントなどの統一           | .editorconfig     |

## Markdown のルール

- Prettier で整形し、markdownlint-cli2 で検査する。
- 日本語の文章を機械的に折り返さないよう、Prettier は `proseWrap: preserve` とする。
- エレベーターピッチの行末スペース2つによる明示的な改行を保持する。
- markdownlint の MD009 は `br_spaces: 2` とし、改行用の行末スペースを許可する。
- Markdown の .editorconfig は `trim_trailing_whitespace = false` とし、保存時に改行用スペースを消さない。
- 行長の検査（MD013）は無効にする。日本語の段落・表・URLを文字数で強制的に折り返さない。
- 整形と検査のルールは競合しないようにする。
- `docs/stories/*/README.md` の内容は保護するが、意味を変えない formatter の機械的な整形は許可する。内容や意味を変える修正が必要なら、変更前に人間の承認を得る。
- 生成物・ビルド出力・外部ツールの補助ファイルは対象から除外する。

## 実行方法

ローカルでは hooks が自動整形と検査を実行し、CI では検査だけを行う。CI がファイルを書き換える運用にはしない。

Kotlin は `spotlessApply` で整形し、`spotlessCheck` で検査する。Android の解析は `:app:lintDebug` を実行する。

Markdown は npm scripts に整形・整形チェック・lint のコマンドをまとめる。ツールはプロジェクトの開発用依存としてバージョンを固定し、ロックファイルを管理する。

この文書は採用方針。Gradle・npm・CI の設定は基盤実装で追加する。

## ファイル変更後の hooks

ファイルを変更した場合は、対応する formatter・linter・テストを hooks で実行する。

- コード変更では、対象言語の整形・静的解析と、影響するロジック・UI のテストを実行する。
- ドキュメント変更では Markdown の整形・検査を実行する。
- 食材データや画像参照の変更では、データの検証テストを実行する。
- formatter による変更で hooks が無限に再実行されないようにする。
- 通常チェックと未実装の受け入れテストは[テスト方針](testing.md)に従って分ける。対象の受け入れテストは、未実装指定の有無にかかわらず工程に応じて hooks から明示実行する。
- `docs/stories/*/README.md` と計画開始後の受け入れテストにも、意味を変えない formatter の機械的な整形は許可する。内容や意味を変える変更には事前承認を必要とする。
- チェックの失敗は報告し、成功として扱わない。未実装による想定した失敗は通常チェックの失敗と分けて記録する。
- PR 作成前には hooks が対象ステップの自動チェックを実行する。hooks の限定的なチェックだけで、ストーリー全体の検証を代替しない。

Codex の hooks はイベントを空で定義し、チェックの接続状態を [checks.json](../../../../.codex/hooks/checks.json) に記録する。状態が pending のコマンドは未接続であり、自動チェックは未実施である。未接続・未発火はメインへ報告し、検証成功や工程完了として扱わない。実行コマンドと変更範囲からのテスト選択は基盤実装で接続する。Git のコミット時 hooks だけではファイル変更時の実行要件を満たさない。

レビュー担当は対象コミットと変更範囲に対応する hooks の実行記録から、整形・lint・必要なテストの結果を確認する。証跡が揃っているチェックを重複実行しない。作成担当の手動実行を前提に未接続を補わず、実行環境の不備としてメインへ返す。

## 参考

- [Spotless Gradle plugin](https://github.com/diffplug/spotless/tree/main/plugin-gradle)
- [ktfmt](https://kotlin.github.io/ktfmt/)
- [Android Lint](https://developer.android.com/studio/write/lint)
- [markdownlint-cli2](https://github.com/DavidAnson/markdownlint-cli2)
- [markdownlint MD009](https://github.com/DavidAnson/markdownlint/blob/main/doc/md009.md)
- [Prettier の設定](https://prettier.io/docs/options)
