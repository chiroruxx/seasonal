---
name: data-research
description: Research and retrieve source-backed seasonal food data for Seasonal, preserving original definitions, periods, regional distinctions, and provenance. Use for collecting or preparing data; use data-review for independent dataset validation.
---

# 旬データの調査・取得

`AGENTS.md` を読み、食材・対象地域・調査目的・保存先を確認する。本文のパスはプロジェクトルート基準。大量の取得結果は[成果物形式](references/output-format.md)に従って保存する。

## 調査と取得

- 定義と対象範囲を追跡できる一次情報を優先し、検索結果だけでなく資料本体を確認する。
- 出典ごとに発行主体、資料名、URL、取得日、更新日、利用条件、抽出箇所を記録する。不明は不明として保持し、取得日を更新日にしない。
- 原データと加工データを分け、取得ファイル・出典・抽出結果の対応を残す。依頼範囲外の大量取得は行わない。
- 公開閲覧と再配布の可否を区別する。原本を保存できない場合は、その理由と参照箇所を記録する。
- 旬が収穫期・流通期・食べごろの何を指すか、期間の粒度、地域・産地・品種・栽培方法などの区別を保持する。
- 複数の期間、年またぎ、旬のない項目・不明な項目を、都合のよい単一期間や月に変換しない。

## 整理と報告

- 抽出・変換を追跡可能にし、推測や補完を原データの事実に混ぜない。
- 出典間の食い違いは条件とともに残し、推測で統合しない。
- 調査用の中間形式と、アプリの同梱データ形式を分ける。月配列を前提とせず、原データを確認して構造を提案する。
- 全レコードをチャットに貼らず、保存先・件数・対象範囲・不一致・不足・未取得を要約する。
- 調査の依頼だけで本番データや確定スキーマを変更しない。採用判断は人間の確認に渡す。

別のレビューエージェントへ、データは `data-review`、報告文書は `document-review` で確認できるよう引き継ぐ。
