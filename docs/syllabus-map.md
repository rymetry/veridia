# シラバス調査状況と対応方針

- 最終更新: 2026-08-15 (Specialist系9本+Core系4本の本文精読完了後。未精読はGame/Automotive等のニッチ領域のみ)

Veridia の Skill/テンプレートを ISTQB/JSTQB シラバスと突き合わせた調査の記録。

**方針: 全シラバスの網羅を目的にしない。** コア7 Skillに影響するものは確認し、
特定領域のものは、その領域の案件が来た時点で該当シラバスを参照して
On-demand Skill を検討する(operating-model の思想と同じ)。

## 調査の深さについて(重要)

Core 4本も本文精読済み(精読ノート: test-planning/references/ctfl-v40-notes.md・ctal-tm-notes.md、test-design/references/ctal-ta-notes.md、test-architecture/references/ctal-tta-notes.md)。
Specialist 9本は**本文精読済み**(各Skillの references/syllabus-notes.md に精読ノートあり。要約はAIによる)。
精読で旧ノートの誤り3件を検出・訂正した(PT: 別ソース混入 / MAT: 実在しない出題比重 / MBT: 版年の誤り)。この地図は「何が書いてあるか」の
所在案内であって、内容の要約として信頼しないこと。

## Core(コア資格)

| シラバス | 版 | 確認状況 | v2への影響と対応 |
|---|---|---|---|
| Foundation (CTFL / JSTQB Foundation) | v4.0 (J02, 2024) | **本文精読(2026-08-15)** 1〜6章 | **反映済み**: 探索的テスト、開始/終了基準、確認・回帰、欠陥記録、完了判定 |
| Advanced Test Analyst (CTAL-TA) | v4.0 (2025) | **本文精読(2026-08-15)** 0〜5章+付録 | **反映済み**: セッションベースドテスト(チャーター)、環境・データ準備。メタモルフィック・欠陥分類法等は必要時 |
| Advanced Test Manager (CTAL-TM) | v3.0 (2024) | **本文精読(2026-08-15)** 0〜3章 | **対象外と判断**: 組織レベルのポリシー・見積り・チーム管理は軽量対話ハーネスの範囲外。テスト完了の概念はFoundation経由で反映済み |
| Advanced Technical Test Analyst (CTAL-TTA) | v4.0 (2021) | **本文精読(2026-08-15)** 全章 | **委譲で対応**: ホワイトボックス技法・静的/動的解析・技術的品質特性は開発者側の責務。test-architecture の責務分担(委譲)で扱う。技術検証が重い案件でOn-demand Skill候補 |

## Specialist(特定領域)— ドメインSkill作成済み

| シラバス | 確認状況 | 対応 |
|---|---|---|
| Test Automation Engineering (CTAL-TAE) v2.0 (2024) | **本文精読(2026-08-15)** | **skills/test-automation 作成済み**(投資判断・保守・CI/CD組み込みの対話ガイド) |
| Performance Testing (CT-PT) | **本文精読(2026-08-15)** | **skills/performance-testing 作成済み** |
| Security Tester (CT-SEC) | **本文精読(2026-08-15)** | **skills/security-testing 作成済み** |
| Usability Testing (CT-UT) v1.0 (2018) | **本文精読(2026-08-15)** | **skills/usability-testing 作成済み** |
| AI Testing (CT-AI) v2.0 (2026) | **本文精読(2026-08-15)** | **skills/ai-testing 作成済み**(ISO/IEC 25059参照) |
| Acceptance Testing (CT-AcT) v1.0 (2019) | **本文精読(2026-08-15)** | **skills/acceptance-testing 作成済み** |
| Model-Based Testing (CT-MBT) v1.1 | **本文精読(2026-08-15)** | **skills/model-based-testing 作成済み** |
| Mobile Application Testing (CT-MAT) | **本文精読(2026-08-15)** | **skills/mobile-testing 作成済み** |
| Testing with GenAI (CT-GenAI) v1.0 (2025。現行v1.1=minor update、release note要旨確認済み・影響なし) | **本文精読(2026-08-15)** | **skills/testing-with-genai 作成済み**(AIでテストする側の規律。ai-testingと役割が別) |
| Game Testing / Automotive 等 | 未調査 | 該当ドメインの案件が来たら作成 |

※ Specialist の名称・版は ISTQB のポートフォリオ改訂で変わりうる。
参照時は istqb.org / jstqb.jp の最新一覧を確認すること。

## On-demand Skill を作るときの手順

1. 該当シラバスの目次を取得し、対象案件に関係する章を特定する
2. 既存の7テンプレートで表現できるか先に確認する(新Skillは最後の手段)
3. 新Skillを作る場合も対話ガイド形式(生成装置にしない)とテンプレートの
   「上流へのフィードバック」「検討したが外したもの」の2節は維持する
4. 本ファイルの確認状況を更新する

## 参照

- JSTQB シラバス一覧: https://jstqb.jp/syllabus.html
- ISTQB 資格ポートフォリオ: https://istqb.org/certifications/
- ASTER テスト設計コンテスト チュートリアル(テスト開発プロセスの参照元): https://aster.or.jp/
