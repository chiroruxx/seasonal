---
name: coding
description: Implement Seasonal Android features and unit tests using the project architecture, and address review findings. Use code-review for independent verification and pull-request for reviewed change publication.
---

# コーディング

本文のパスはプロジェクトルート基準。`AGENTS.md`、依頼された計画・ストーリー・受け入れ条件と変更範囲を確認する。デザインは `docs/design/principles.md` を入口に、変更に関係するルールを読む。

## 実装と責務

- Kotlin、Jetpack Compose、Compose Material 3 を使い、単一の app モジュール内で役割を分ける。
- Compose とイベントハンドラーは表示・操作の通知を担当する。データ読み込み、旬の判定、業務処理を集中させない。
- ViewModel + StateFlow は画面の状態と操作の調整を担当し、UI からデータ取得の詳細を分離する。
- Repository は同梱 JSON の読み込みと解析済みデータの保持を担当する。kotlinx.serialization を使い、月を切り替えるたびにファイルを読み直さない。
- 旬の判定は UI やファイル読み込みから独立した Kotlin の処理にする。期間の保存形式は元データに合わせ、月配列を勝手に確定しない。
- 各責務は必要な範囲で分離する。不要な層や抽象化を増やさない。
- 本番コードに加え、変更した振る舞い・境界条件を確かめる単体テストを実装する。テストを実装の写しにせず、低影響の変更へ形式的にテストを増やさない。
- 人間が確認した受け入れテストを実装に合わせて緩めない。意味を変えない formatter の整形は共通ルールに従って許可する。

## 変更後の進め方

formatter・linter・テストの実行は hooks が担当し、結果の妥当性は reviewer が確認する。同じチェックを手動で重複実行しない。失敗の通知には修正で対応し、hooks が発火しない場合は環境の不備としてメインへ報告する。

変更内容、受け入れ条件との対応、発生した失敗通知と対応、未確認事項を reviewer に引き継ぐ。対象テストの成功が reviewer またはメインから確認された後に、`@PendingAcceptance` を外す。本文・期待値・操作・データを変える必要があれば、変更前に人間の承認を得る。

レビュー指摘への修正も担当する。コミットはメインの依頼範囲で意味のある小さな単位に分ける。PR の作成・更新は、レビュー完了後にメインが別の作業エージェントへ `pull-request` スキルで依頼する。
