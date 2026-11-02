# 開発フローと CI

## CI

GitHub Actions を使用する。

PR では以下を検査する。

- Spotless、Android Lint、markdownlint-cli2、Prettier。
- 単体テストと同梱データの検証。
- Debug APK のビルド。
- Gradle 管理の Android 16 エミュレーターによる受け入れ済みシナリオの回帰検証。

実装前に作成する未実装シナリオは、通常のチェックから明示的に分ける。開発中の実行方法と受け入れ済みへの移行は[テスト方針](testing.md)に従う。

## ストーリーの進め方

1. 対象ストーリーの受け入れ条件を定義する。
2. 実装前に受け入れテストを作成し、未実装シナリオとして登録する。
3. 対象テストを明示実行し、意図した未実装の振る舞いにより失敗することを確認する。
4. 機能を実装し、対象テストが成功することを確認する。
5. 未実装の指定を外し、通常チェックの回帰検証に含める。
6. 対象ストーリーの全受け入れテストと通常チェックの成功、人による確認を経て完了とする。

実行用の Gradle 設定と GitHub Actions ワークフローは、基盤実装で追加する。

## 依存関係の更新

Renovate を使用して依存関係の更新 PR を作成する。

- Gradle のライブラリとプラグインは `gradle/libs.versions.toml` でバージョンを管理する。
- Gradle Wrapper も更新対象にする。
- Markdown 用の開発ツールは `package.json` とロックファイルでバージョンを固定し、両方を更新する。
- 更新 PR では通常の CI を実行する。
- 自動マージはせず、変更内容と CI の結果を確認して取り込む。画面に影響する更新は見た目も確認する。
- 破壊的変更と、AGP・Kotlin・Compose などの互換性を確認する。

Renovate の設定ファイルと GitHub 側の接続は、基盤実装で用意する。

### 参考

- [Renovate：Gradle](https://docs.renovatebot.com/modules/manager/gradle/)
- [Renovate：npm](https://docs.renovatebot.com/modules/manager/npm/)
