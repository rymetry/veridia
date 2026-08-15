# Veridia 運用モデル

- Version: 2.0
- Status: Active

## Veridiaとは

開発の各フェーズに品質の観点を持ち込むための、**対話型Skillとテンプレートのセット**。

Skillは成果物を自動生成する装置ではない。その観点で確認し、人間と対話しながら
一緒に成果物を作り、上流(PRD等)へフィードバックを返す相棒である。

## 原則

1. **対話で作る。** 各フェーズで人間とSkillが対話し、整理しながら成果物を仕上げる。
   全自動化はしない。
2. **成果物はMarkdown。** 人がそのまま読める文書として残す。スキーマやYAMLを
   人間に読ませない。
3. **上流へのフィードバックが第一の価値。** プレモーテムや品質特性チェックの
   最大の成果は、テストの入力ではなくPRDが良くなることである。
4. **「なぜこのテストがあるのか」に遡れる。** この追跡はテスト計画が一元的に持つ。
   計画の各項目は、どの失敗シナリオ・どの品質特性に対応するかを明記する。

## フェーズと成果物

```text
PRD / Figma / Notion などのプロジェクト資料
        │
        ▼
① プレモーテム ──────────────→ premortem.md
        │      └─ PRDへのフィードバック → PRD修正 → 再レビュー
        ▼
② 品質特性チェック ──────────→ quality-characteristics.md
        │      └─ PRDへのフィードバック → PRD修正 → 再レビュー
        ▼
③ テスト計画 ────────────────→ test-plan.md   ★トレーサビリティを持つ
        │                        (何を・なぜ・どの深さで)
        ▼
④ テストアーキテクチャ設計 ──→ test-architecture.md
        │                        (どこで確認するか。重複と漏れを防ぐ)
        ▼
⑤ テスト設計 ────────────────→ test-design.md
        │                        (何を確認するか+パラメーターの絞り方)
        ▼
⑥ テストケース作成 ──────────→ test-cases.md
                                 (実行できるケース+実行順序)
```

各フェーズの成果物は対象プロジェクトのリポジトリに保存する(例: `quality/` 配下)。

## 各フェーズの流れ

どのフェーズも同じ形で進む。

```text
1. Skillを呼ぶ(例: /premortem)
2. SkillがPRD・Figma・Notion・前フェーズの成果物を読む
3. 対話: Skillが問いを出し、人間が答え、一緒に整理する
4. テンプレートに沿って成果物を書き上げる
5. 上流への指摘があれば「フィードバック」節にまとめる
6. 人間がフィードバックを反映(PRD修正など)したら、必要な範囲で再レビュー
```

## 再レビューのタイミング

- PRDや設計が大きく変わったとき
- 外部依存が増えたとき
- リリース前
- 障害・ヒヤリハットが起きたとき

再レビューは全部のやり直しではない。変わった部分と、その影響を受ける成果物だけを
対話で更新する。各成果物の「検討したが外したもの」の節を先に確認し、
同じ議論を繰り返さない。

## テンプレート

`templates/` に各成果物の雛形がある。テンプレートは書式の強制ではなく出発点であり、
プロジェクトに合わせて増減してよい。ただし次の2つの節はどの成果物でも残すこと。

- **上流へのフィードバック** — このフェーズで見つけた上流の問題
- **検討したが外したもの** — 外した理由。次回の再レビューで同じ議論を防ぐ

## Skillの一覧

| Skill | フェーズ | 主な入力 |
|---|---|---|
| premortem | ① | PRD、Figma、Notion、既存の障害記録 |
| quality-characteristics | ② | PRD、premortem.md |
| test-planning | ③ | PRD、premortem.md、quality-characteristics.md、既存テスト資産 |
| test-architecture | ④ | test-plan.md、PRD、システム構成資料 |
| test-design | ⑤ | test-plan.md、test-architecture.md、PRD、Figma |
| test-cases | ⑥ | test-design.md |
| exploratory-testing | ⑤⑥と並行 | test-plan.md、test-design.md |

exploratory-testing はフェーズを持たない横断Skill。テスト計画で探索的テストが
手段に指定された領域、または実行中に「まだ何かありそう」な領域で使う。
発見は欠陥起票・上流フィードバック・premortem・test-cases の4経路へ流す。

規模が小さくテストレベルが単一のプロジェクトでは、④を独立の対話とせず
③の中で「どこで確認するか」を一緒に決めて test-plan.md に書き込んでもよい。
その場合 test-architecture.md は作らない。

## ドメインSkill

特定の領域が関係するとき、コアのフェーズと並行して観点を持ち込むSkill。

**新しい成果物は作らない。** いずれも既存の成果物(premortem / test-plan /
test-architecture / test-design / test-cases)の該当箇所へ書き込む対話ガイドである。

| Skill | 使う契機 | 主な参照 |
|---|---|---|
| performance-testing | 性能が品質特性に採用 / 大量データ・同時アクセスが前提 | ISTQB CT-PT |
| security-testing | 認証・個人情報・決済・外部公開を扱う | ISTQB CT-SEC |
| usability-testing | 使い勝手が価値に直結 / アクセシビリティ要件 | ISTQB CT-UT |
| ai-testing | AI/確率的な振る舞いを含む(オラクルが立てにくい) | ISTQB CT-AI |
| acceptance-testing | 業務部門・発注者の受け入れ判定がある | ISTQB CT-AcT |
| model-based-testing | 状態・分岐が複雑でケース漏れが不安 | ISTQB CT-MBT |
| mobile-testing | モバイルアプリを含む | ISTQB CT-MAT |
| test-automation | 自動回帰が手段に入る / 自動化の投資判断 | ISTQB CTAL-TAE |
| testing-with-genai | AIでテスト成果物を作る場面すべて(常時の規律) | ISTQB CT-GenAI |

どのドメインSkillを使うかは、test-planning の対話の中で決めるのが基本
(品質特性と失敗シナリオが契機を示す)。

testing-with-genai のみ性格が異なり、**Veridiaの運用そのものを律する横断規律**である
(AI出力の無検証採用の禁止・データの扱い・非決定性への対処)。
特定の契機を待たず、全フェーズの前提となる。

自律実行(agent化)は、対話での運用が安定し、必要性が明確になったフェーズから
個別に検討する。最初からは行わない。
