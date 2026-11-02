# 静的解析と整形

## 使用するツール

| 対象 | 役割 | ツール |
| --- | --- | --- |
| Kotlin・Gradle Kotlin DSL | 自動整形と整形状態の検査 | Spotless + ktfmt |
| Android | API・リソースなどの静的解析 | Android Lint |
| Markdown | 見出し・リスト・リンク表記などの検査 | markdownlint-cli2 |
| Markdown | 自動整形と整形状態の検査 | Prettier |
| エディター | 改行・インデントなどの統一 | .editorconfig |

## Markdown のルール

- Prettier で整形し、markdownlint-cli2 で検査する。
- 日本語の文章を機械的に折り返さないよう、Prettier は `proseWrap: preserve` とする。
- エレベーターピッチの行末スペース2つによる明示的な改行を保持する。
- markdownlint の MD009 は `br_spaces: 2` とし、改行用の行末スペースを許可する。
- Markdown の .editorconfig は `trim_trailing_whitespace = false` とし、保存時に改行用スペースを消さない。
- 行長の検査（MD013）は無効にする。日本語の段落・表・URLを文字数で強制的に折り返さない。
- 整形と検査のルールは競合しないようにする。
- README.md はユーザー指定の変更対象外として、自動整形の対象から除外する。検査で問題が出た場合も自動修正せず、除外・ルールの適用範囲で扱う。
- 生成物・ビルド出力・外部ツールの補助ファイルは対象から除外する。

## 実行方法

ローカルでは自動整形を実行できるようにし、CI では検査だけを行う。CI がファイルを書き換える運用にはしない。

Kotlin は `spotlessApply` で整形し、`spotlessCheck` で検査する。Android の解析は `:app:lintDebug` を実行する。

Markdown は npm scripts に整形・整形チェック・lint のコマンドをまとめる。ツールはプロジェクトの開発用依存としてバージョンを固定し、ロックファイルを管理する。

この文書は採用方針。Gradle・npm・CI の設定は基盤実装で追加する。

## 参考

- [Spotless Gradle plugin](https://github.com/diffplug/spotless/tree/main/plugin-gradle)
- [ktfmt](https://kotlin.github.io/ktfmt/)
- [Android Lint](https://developer.android.com/studio/write/lint)
- [markdownlint-cli2](https://github.com/DavidAnson/markdownlint-cli2)
- [markdownlint MD009](https://github.com/DavidAnson/markdownlint/blob/main/doc/md009.md)
- [Prettier の設定](https://prettier.io/docs/options)
