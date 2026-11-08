# GitHub の自動チェックと APK 配布

## CI

[CI ワークフロー](../../.github/workflows/ci.yml)は、PR、`main` への push、手動実行で動作する。

- `quality` は Node.js 22 で npm の依存関係を復元し、監査、Markdown の整形確認・lint、品質ツールのテスト、Python のテスト、調査データの検証を行う。
- `android` は JDK 21 と Android SDK を使い、Spotless、Android Lint、単体テスト、Android 16 の管理端末による受け入れテスト、Debug APK のビルドを行う。
- CI ではファイルを書き換えない。受け入れテストの通常実行は `@PendingAcceptance` を除外する。
- PR のチェックには署名鍵の Secrets を使わない。CI の Debug APK は検査用であり、継続署名した配布用 APK と区別する。

ローカルの実行方法と未実装テストの明示実行は[品質チェックと hooks](quality-checks.md)に従う。CI の成功と、ストーリー単位の人間による UI・UX の受け入れは別に確認する。

## GitHub 側の初期設定

ワークフローと設定ファイルを GitHub のリポジトリへ反映し、Actions を有効にする。手動実行用ワークフローは既定ブランチに配置する。

CI の `Quality checks` と `Android checks` の初回成功を確認し、ブランチ保護の必須チェックに指定する。PR のマージは人間が行う。

設定ファイルの検証だけでは、GitHub 上のワークフロー実行や Secrets の登録が完了したことにはしない。初回実行でチェック結果と保存された成果物を確認する。

## 配布用の署名鍵

同じ端末へ上書き更新するときは、applicationId と署名鍵を維持する。署名鍵を CI の実行ごとに作り直さない。

[署名・成果物の準備プログラム](../../scripts/distribution.py)で、初回だけリポジトリ外に鍵を作成する。端末上で次の環境変数を設定してから実行する。パスワードはチャットや Git に記録しない。

- `SEASONAL_DEBUG_STORE_PASSWORD`：キーストアのパスワード。
- `SEASONAL_DEBUG_KEY_ALIAS`：署名鍵のエイリアス。
- `SEASONAL_DEBUG_KEY_PASSWORD`：鍵のパスワード。

```sh
python3 scripts/distribution.py create-key "$HOME/.seasonal-signing/seasonal-debug.jks"
```

既存の鍵は上書きしない。鍵とパスワードをバックアップし、以後の配布でも同じものを使う。

GitHub のリポジトリに、署名用 Secrets の保存先となる Environment `apk-signing` を作る。次の Secrets をこの Environment に登録する。

| 名前                             | 内容                   |
| -------------------------------- | ---------------------- |
| `SEASONAL_DEBUG_KEYSTORE_BASE64` | キーストアの Base64    |
| `SEASONAL_DEBUG_STORE_PASSWORD`  | キーストアのパスワード |
| `SEASONAL_DEBUG_KEY_ALIAS`       | 署名鍵のエイリアス     |
| `SEASONAL_DEBUG_KEY_PASSWORD`    | 鍵のパスワード         |

対象リポジトリを選択した GitHub CLI から登録する場合は、鍵の内容を画面へ出さずに渡す。

```sh
base64 < "$HOME/.seasonal-signing/seasonal-debug.jks" | gh secret set --env apk-signing SEASONAL_DEBUG_KEYSTORE_BASE64
gh secret set --env apk-signing SEASONAL_DEBUG_STORE_PASSWORD
gh secret set --env apk-signing SEASONAL_DEBUG_KEY_ALIAS
gh secret set --env apk-signing SEASONAL_DEBUG_KEY_PASSWORD
```

後ろの3コマンドでは、先ほど鍵の作成に使った値を対話入力する。登録内容は `gh secret list --env apk-signing` で名前だけ確認する。鍵・パスワード・復元したキーストアを Actions の成果物へ含めない。

## 確認用 APK の作成

[Debug APK ワークフロー](../../.github/workflows/distribute.yml)を既定ブランチから手動実行する。入力は次のとおり。

| 入力     | 指定する値                                           |
| -------- | ---------------------------------------------------- |
| `story`  | `docs/stories/<story>/README.md` のあるストーリー ID |
| `commit` | 確認対象コミットの完全な40桁 SHA                     |

対象コミットは既定ブランチに統合済みであることを確認する。ワークフローは品質チェックと未実装の除外なしの受け入れテストを実行し、未実装の指定が残っていないことを確認してから、継続利用する鍵で Debug APK を作成する。

次の `COMMIT_SHA` を確認対象の完全な SHA に置き換えて実行する。

```sh
gh workflow run distribute.yml --ref main -f story=iteration0 -f commit=COMMIT_SHA
```

ワークフローは Secrets から一時領域に鍵を復元し、署名と applicationId・versionCode を検証して APK を保存する。

versionCode は 2025年1月1日 UTC からの経過秒を使う。同じ配布ワークフローは直列に実行し、再実行でも新しい値を採番する。ローカルの通常ビルドの versionCode と、配布用の値を区別する。

保存する成果物は次の3ファイルである。

- `seasonal-<story>-<commit>-v<versionCode>.apk`。
- `manifest.json`：ストーリー、コミット、applicationId、versionCode、APK と署名証明書の SHA-256、ワークフローの実行 URL。
- `SHA256SUMS`：APK のハッシュ。

ワークフローの実行結果から、対象コミットと成果物を特定する。保存期間は90日である。APK をダウンロードし、同じディレクトリで `shasum -a 256 -c SHA256SUMS` を実行して確認する。

## ストーリーの受け入れと端末への配布

人間が、保存された APK を自分の端末で実行し、ストーリー単位で UI・UX を確認する。関連 PR、対象コミット、ワークフローの実行 URL、APK の SHA-256、確認結果をストーリー README とは別の記録に残す。

受け入れ後は、その同じ APK を配布版とする。受け入れた APK、`manifest.json`、`SHA256SUMS` は保存期間が切れる前に手元にも保存する。別のビルド結果を受け入れ済み APK と扱わない。修正した場合は新しい成果物で再確認する。

受け入れたコミットへのタグ付けは人間の確認後に行う。タグは `manifest.json` のコミットを指し、APK・ハッシュ・実行 URL との対応を記録する。ワークフローからタグ作成や PR のマージは行わない。

## Renovate

[Renovate の設定](../../renovate.json)で、Gradle のライブラリ・プラグイン・Wrapper、npm、GitHub Actions の依存関係を更新する。自動マージは使わず、更新 PR の差分と CI の結果を確認して人間がマージする。互換性や画面への影響がある更新では、動作・見た目も確認する。

GitHub の対象リポジトリに Mend Renovate App をインストールし、リポジトリへのアクセスを許可する。設定ファイルの追加だけでは App の接続は完了しない。

## 参考

- [GitHub Actions の Secrets](https://docs.github.com/en/actions/how-tos/write-workflows/choose-what-workflows-do/use-secrets)
- [ワークフローの手動実行](https://docs.github.com/en/actions/how-tos/manage-workflow-runs/manually-run-a-workflow)
- [Renovate の GitHub 接続](https://docs.renovatebot.com/modules/platform/github/)
