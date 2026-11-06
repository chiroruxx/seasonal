# 品質チェックと hooks

## 実行と確認の担当

formatter・linter・テストは hooks が実行し、reviewer が対象の版と結果の対応を確認する。実装・文書作成担当は失敗通知に対応し、成功済みのチェックを手動で重複実行しない。

全ステップの独立レビュー後は、reviewer が `pre-pr-check` で全体の検証結果を確認する。PR の公開可否と、人間によるストーリーの受け入れは別に扱う。

GitHub 上の実行と署名付き APK の保存・配布は[GitHub の自動チェックと APK 配布](github-automation.md)に従う。

## チェックコマンド

Markdown 用のツールは Node.js 22 以上を使い、`npm ci` で lockfile に記録された依存関係をインストールする。

Gradle のデーモンには JDK 21 を使う。JDK 21 をインストールし、[gradle-daemon-jvm.properties](../../gradle/gradle-daemon-jvm.properties) の `toolchainVersion=21` で選択する。機械固有のパスや `JAVA_HOME` の固定は必要ない。Android のチェックには、プロジェクトの `compileSdk` に対応する Android SDK を用意し、SDK の場所をローカル環境で設定する。

| 対象                                  | コマンド                                                       |
| ------------------------------------- | -------------------------------------------------------------- |
| Markdown の整形                       | `npm run format:markdown`                                      |
| Markdown の整形確認                   | `npm run check:markdown`                                       |
| Markdown の lint                      | `npm run lint:markdown`                                        |
| Kotlin・Gradle Kotlin DSL の整形      | `./gradlew spotlessApply`                                      |
| Kotlin・Gradle Kotlin DSL の整形確認  | `./gradlew spotlessCheck`                                      |
| Android Lint                          | `./gradlew :app:lintDebug`                                     |
| 単体テスト                            | `./gradlew :app:testDebugUnitTest`                             |
| Debug APK のビルド                    | `./gradlew :app:assembleDebug`                                 |
| Markdown チェック用プログラムのテスト | `npm run test:quality`                                         |
| hooks 実行プログラムのテスト          | `python3 -m unittest discover -s tests -p test_codex_hooks.py` |

Markdown のコマンドは、引数なしでは Git の追跡対象と未追跡の Markdown ファイルを対象にする。個別ファイルを指定する場合は `npm run check:markdown -- docs/development/quality-checks.md` のように渡す。日本語の段落を機械的に折り返さず、改行用の行末スペース2つを保持する。

## 受け入れテスト

Android 16（API 36）の管理端末 `pixel2Api36` と Compose UI Test を使う。`./gradlew :app:acceptanceTest` で実行し、結果の XML に実行件数があり、失敗・エラー・スキップがないことまで確認する。通常実行では `@PendingAcceptance` の付いたテストを除外する。通常の単体テストや APK ビルドの成功を、受け入れテストの実行証拠として代用しない。

未実装の対象テストを明示実行する場合は、`./gradlew :app:acceptanceTest -PincludePendingAcceptance=true -PacceptanceTestClass=完全修飾クラス名` を使う。ストーリー全体を PR に出す前は `./gradlew :app:acceptanceTest -PincludePendingAcceptance=true` で除外なしに実行し、reviewer が `@PendingAcceptance` の付与が残っていないことも確認する。

## データの検証

`python3 scripts/validate_data.py` は Git の追跡対象と未追跡ファイルから調査データを探索する。ディレクトリを指定する場合は `python3 scripts/validate_data.py <調査ディレクトリ>` を使う。検証器自体のテストは `python3 -m unittest discover -s tests -p test_validate_data.py` で実行する。

対象は確定済みの調査用 `sources.jsonl`・`observations.jsonl`・`issues.jsonl` と原本パス・要約ファイルの存在である。構造、ID と参照、取得日時のタイムゾーン、原本の保存場所と未保存理由を確認する。期間の粒度や原資料の内容を推測して補完しない。実データがない場合は `no_datasets` を明示し、実データを検証済みと扱わない。

アプリ同梱データの形式・画像参照契約は未確定である。アプリの assets 内の JSON・JSONL や、調査形式と判定できない JSONL を検出した場合は未対応として失敗させる。原資料との意味の一致・要約件数・利用条件の妥当性は `data-review` で確認する。

## 設定と実行タイミング

- [hooks.json](../../.codex/hooks.json) に Codex のイベント接続を定義する。
- [checks.json](../../.codex/hooks/checks.json) に対象ファイルとチェックコマンドを定義する。
- [codex_hooks.py](../../scripts/codex_hooks.py) が Git の追跡対象・未追跡ファイル・削除を含む変更を検知し、必要なチェックを選ぶ。
- `PostToolUse` はツール名で絞らず、実際の変更に対応するチェックを実行する。
- `Stop` は蓄積した変更に関係する全体チェックを実行する。通常の受け入れテストでは未実装を除外し、対象の状態が同じ場合は fingerprint により重複実行を省く。
- `--full` の明示実行では全チェックを選び、受け入れテストは未実装の除外なしで実行する。チェック定義の `full` コマンドは、この明示実行だけに適用する。

並行実行中の `PostToolUse` は、チェック未完了の通知を返して元のツール結果を保持する。実行中であることを成功とは扱わず、完了後の証跡を確認する。

失敗・未導入・未実行を成功と扱わない。`Stop` の失敗はエージェントへ返し、修正を促す。継続後も解消しない場合は無限に停止を繰り返さず、不完全な結果を報告する。

## hooks の有効化

プロジェクトの `.codex/` 設定層と hooks は、人間が内容を確認して信頼した後に動作する。CLI では `/hooks`、デスクトップアプリでは `Review hooks` または `Settings > Hooks` を開き、接続するコマンドを確認する。定義の変更後は再確認する。信頼の確認を迂回するオプションは使用しない。

設定ファイルの配置やプログラム単体の成功だけでは、ホストからの自動発火を確認したことにしない。実際の変更とターン終了で hooks が発火し、その版に対応した証跡が生成されることを確認する。仕様は [OpenAI の hooks ドキュメント](https://learn.chatgpt.com/docs/hooks)に従う。

## 証跡

結果は `.quality-results/<runid>/report.json` とチェックごとのログに保存する。Git の `HEAD`、未コミット変更を含むファイルの snapshot・fingerprint、チェック定義の hash、対象パス、実行コマンド、結果を記録する。状態ファイルと排他用の lock も `.quality-results/` に置き、Git には追加しない。

reviewer はコミットだけでなく、未コミット変更とチェック定義が実行時の状態に一致するかを確認する。対象が変わったら必要なチェックをやり直す。`unavailable` は未導入・実行不能を示し、全体結果の `incomplete` は成功ではない。

接続の動作確認や PR 前の全体チェックを明示実行する場合は、リポジトリルートで次を使う。

```sh
printf '%s' '{"hook_event_name":"Stop"}' | python3 scripts/codex_hooks.py --full
```

この入口を直接実行した結果は、ホストからの自動発火を確認した証拠とは区別する。
