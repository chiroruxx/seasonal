---
name: code-review
description: Review Seasonal application code, unit tests, build configuration, or automation for correctness, architecture responsibilities, and verified checks. Use for independent code review; use acceptance-test-review for acceptance-test reviews and document-review for prose-only changes.
---

# コードレビュー

本文のパスはプロジェクトルート基準。`AGENTS.md`、対象ストーリー・受け入れ条件・レビュー範囲・基準コミットを確認する。作業担当から独立したエージェントとしてレビューし、依頼がない限り修正しない。

## 確認すること

- 差分だけでなく呼び出し元と既存動作を必要な範囲で追い、受け入れ条件を満たすか確認する。
- `.agents/skills/coding/SKILL.md` の責務と、変更に関係する `docs/design/` の設計を参照する。PR の構成を確認する場合は `.agents/skills/pull-request/SKILL.md` を参照する。
- アーキテクチャの責務範囲を守っているか確認する。特に UI・イベントハンドラーへデータ読み込み、旬の判定、業務処理が集中していないか、ViewModel と Repository の役割が混ざっていないかを追う。
- 不具合、状態・ライフサイクル、例外処理、データ保持、月・年の境界、表示と操作の回帰を優先する。
- 単体テストが変更の振る舞いと境界を検証するか確認する。実装の写しや、受け入れテストを通すための期待値変更・失敗の握りつぶし・無断除外を指摘する。
- hooks の実行結果から、対象変更の整形チェック・linter・必要なテストにエラーがない証拠を確認する。同じ結果に対するチェックを重複実行しない。hooks が未発火・未接続の場合は環境の不備としてメインへ返し、未検証のまま成功としない。
- hooks の存在だけでは成功と判断せず、変更した版と実行結果の対応を確認する。未実装による想定した失敗、回帰、未実行を区別し、対象の受け入れテストが除外された通常実行だけで機能を検証済みにしない。
- 対象の受け入れテストが、実装前は意図した振る舞いの不足で失敗し、実装後は成功することを証拠で確認する。コンパイル・起動・環境エラーをその代用にしない。結果が不足し明示実行が必要な場合は、メインと実行範囲を確認する。
- Stacked Pull Requests は、GitHub のスタック所属と順序を確認する。base ブランチが依存しているだけの PR を正式なスタックとして扱わない。
- 保護対象の変更に必要な承認を確認する。成功確認後の `@PendingAcceptance` 解除と、意味を変えない formatter の整形は共通ルールの例外に従う。
- コードと文書を両方変更した場合は `document-review` も使う。

## 報告

指摘は重要度順に、ファイル・行、再現条件または根拠、影響を添える。推測は未確認と明示し、スタイルの好みを不具合として扱わない。

指摘がない場合も、レビュー範囲、formatter・linter・テストの実行結果、未設定・未実行のチェックを記載する。
