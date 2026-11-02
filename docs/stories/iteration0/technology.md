# 技術選定

採用する技術と構成を記載する。デザインシステムは Material 3 を使う。

## 食材データの採用方針

最初はアプリ同梱の JSON + kotlinx.serialization を使う。

- 旬のデータ構造は、元データの粒度や意味を確認して決める。月の配列 `seasonMonths` は候補であり、確定ではない。
- JSON は読み込んで解析した結果を保持し、月ごとの抽出のたびには読み直さない。
- 「いまが旬」「そろそろ旬」は、読み込んだ旬の情報から判定する。元データが月単位であれば、現在月・来月を含むかどうかで抽出する。12月の来月は1月とする。
- ファイル読み込みや解析で UI スレッドを長時間占有しないようにする。
- 同梱データの更新はアプリ更新で配布する。

SQLite / Room は初期構成には採用しない。データ量や検索・更新要件に応じて再検討する。読み込み時間は、実際のデータと端末で確認する。

## 対応 SDK とビルド構成

- Android の単一 app モジュール。
- Android Gradle Plugin 9.1.1、Gradle Kotlin DSL、Version Catalog を使用。
- minSdk / targetSdk は 36 のままとする。Android 16 以降を対象とする。
- compileSdk は既存の 36.1 を維持する。

現状は AppCompat と View 向け Material Components に依存する雛形で、アプリの画面は未実装。

## 採用技術

| 項目 | 採用技術・構成 | このアプリでの用途・理由 |
| --- | --- | --- |
| 言語 | Kotlin | Android 向けの実装とテストを統一する |
| UI | Jetpack Compose + Compose Material 3 | 食材一覧、テーマ、モーダルボトムシートを作る |
| 状態管理 | ViewModel + StateFlow | 読み込んだ食材、現在月に応じた表示状態を画面に渡す |
| 非同期処理 | Kotlin Coroutines | データ読み込みを UI から分離する |
| 食材データ | アプリ同梱 JSON + kotlinx.serialization | 旬の月・選び方・出典などを管理し、通信なしで読めるようにする |
| イラスト | アプリ同梱の画像リソース | 一覧用と説明用の絵を表示する |
| データ取得の窓口 | Repository | UI とデータの保存形式を分離する |
| 依存の受け渡し | コンストラクタと小さな手動コンテナ | 現在の規模に合わせて依存関係を明示する |
| テスト | JUnit + Compose UI Test | 月またぎ・年またぎの旬判定、食材の選択とシート表示を確認する |
| 受け入れテスト実行環境 | Gradle 管理の Android 16 エミュレーター | ローカルと CI で同じ条件の UI テストを実行する |
| CI | GitHub Actions | PR のビルド・解析・テストを自動実行する |
| 依存関係の更新 | Renovate | Gradle・npm などの更新 PR を作成する |
| Kotlin の整形 | Spotless + ktfmt | Kotlin・Gradle Kotlin DSL の整形を統一する |
| Android の静的解析 | Android Lint | API・リソースなどを検査する |
| Markdown の検査・整形 | markdownlint-cli2 + Prettier | ドキュメントの記述と整形を統一する |
| エディター設定 | .editorconfig | 改行・インデントなどを統一する |

機能の受け入れ条件は Compose UI Test で自動化する。日付・データを固定した操作テストと、実際の同梱 JSON の確認を分ける。見た目・使いやすさ・情報の正しさは人による確認も行う。詳細は[テスト方針](testing.md)を参照。

静的解析と整形の適用範囲・実行方法は[静的解析と整形](code-quality.md)を参照。

## コードの分け方

単一の app モジュール内で役割を分ける。

- Compose：画面の表示と操作。
- ViewModel + StateFlow：読み込んだ食材や、現在月に応じた表示状態の管理。
- Repository：JSON の読み込みと、読み込んだデータの保持。
- 旬の判定：UI から独立した Kotlin の処理。月またぎ・年またぎを単体テストする。

旬・選び方の出典と旬の詳細なデータ構造は、元データを確認して決める。項目の大枠と確認事項は[食材データの管理](food-data.md)を参照。

初期構成では、画面遷移ライブラリ、サーバー通信ライブラリ、データベース、DI フレームワークは導入しない。検索・保存・更新の要件が増えた時点で必要性を判断する。

## 実装前の確認事項

- 使用するライブラリの互換性・具体的なバージョン。

## 参考

- [Android Developers：Jetpack Compose](https://developer.android.com/develop/ui/compose/documentation)
- [Android Developers：Material 3](https://developer.android.com/develop/ui/compose/designsystems/material3)
- [Android Developers：アーキテクチャの推奨事項](https://developer.android.com/topic/architecture/recommendations)
