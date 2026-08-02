# ADR-0009: 契約の正本をどちらが持つかは列挙ではなく原則で決める

- status: accepted
- date: 2026-08-02

## Context(何を決める必要があったか)

[ADR-0007](adr-0007-sqk-core-contract-consumption.md) は「veridia が自前で定義する契約は、sqk-core が扱わない**実行系固有のもの**に限る」と原則を述べたうえで、「具体的には `ExecutionEvidence` / `GateDecision` / `GatePolicy`、および `RunRecord`」と**4件を列挙**した。Consequences にも「veridiaが定義する契約は 27 → 4 になる」と書いた。

T-028(W1 の出力契約 `SourceMap`、North Star §6.2)に着手する段で、この列挙が判断を止めた。

- `SourceMap` に相当する契約は sqk-core に**存在しない**。sqk-core は ISO/IEC/IEEE 29119-2 / JSTQB v4.0 接地の11工程モデル(テストプロセス)を正典化しており、source grounding は veridia の ingestion 固有の関心でその外側にある
- したがって ADR-0007 の**原則**には合致する(実行系固有 かつ sqk-core が持たない)が、**列挙**とは食い違う
- 列挙のまま運用すると、同種の判断が来るたびに「4つと書いてあるが」で止まる。実際に止まった

すなわち、ADR-0007 が原則と、その時点での適用結果(列挙)を、同じ強さで書いてしまっていた。

あわせて `SourceMap` は `trust_level`(`trusted` / `untrusted` / `external`)を持つ。learning-log 2026-08-02「信頼ラベルをLLMに生成させるとtrust gateが自己申告で迂回できる」により、この field を**誰が決めるか**を契約定義と同時に決める必要があった。

## Decision(何を決めたか)

### 1. 契約の正本は原則で判定する。ADR-0007 の列挙は「採択時点の適用結果」として読む

```text
sqk-core が正本を持つ  … テストプロセス成果物(sqk-core 11工程モデルの工程0〜8)
                          veridia は複製・再定義しない(ADR-0007)

veridia が正本を持つ  … 実行系固有のもの。すなわち以下のいずれかで、
                          かつ sqk-core に相当物が無いもの
                          - 実行の記録・監査(run / evidence / trace)
                          - 判定と統制(gate / policy)
                          - 取り込み境界(ingestion / source grounding)
```

新しい契約を足すときは**この原則に照らす**。ADR-0007 の4件の列挙を閉じた集合として扱わない。原則に照らして veridia 側と判定した契約は、`schemas/README.md` のルールに従って定義する。

本 ADR により `SourceMap` は veridia が定義する5件目の契約になる。

### 2. `trust_level` の authority は ingestion 層に置く。LLM の出力を採用しない

`SourceMap.trust_level` の値は `source_connector`(取り込み境界)が供給する。source-grounding skill(T-029)が出力した値は**採用しない**。

- 設定で対象repoを指すという行為そのものが信頼の付与である。したがって `TargetRepository` が `trust_level` を持ち、`ChangeSet` がそれを運ぶ
- 対象repo以外から来たもの(外部ドキュメント、issue本文、third party資料)は明示的にラベル付けする。既定へ落とさない
- skill の出力に `trust_level` が含まれていた場合、runtime はそれを ingestion 層の値で**上書きする**(T-029 で配線する)

### 却下した代替案

| 代替案 | 却下理由 |
|---|---|
| ADR-0007 を編集して列挙を直す | ADR は上書きせず新しい ADR で supersede する(`docs/decisions/README.md`)。また ADR-0007 の判断自体は正しく、誤りは「原則と適用結果を同じ強さで書いた」ことなので supersede でもない |
| `SourceMap` を定義せず、T-026 の `ChangeSet` で当面代替する | `ChangeSet` は取得結果であって artifact ではない(`trust_level` も `extracted_items` も持たない)。W1 の出力契約が無いと T-029 の skill は出力を検証できず、W1 を skill 化できない |
| sqk-core へ `SourceMap` 相当を起票して上流に持たせる | grounding は veridia の ingestion 固有の関心で、sqk-core の11工程モデルの外側にある。sqk-core は4プラットフォームへ供給する設計であり、1 consumer の取り込み境界を正典へ持ち込むことになる(ADR-0007 で同じ理由により却下した案と同型) |
| `trust_level` を skill に生成させ、値域だけ schema で縛る | 値域の検証は「誰が言ったか」を検証しない。信頼ラベルの生成主体と、それを信頼する主体が同じなら、gate は自己申告で迂回できる(learning-log 2026-08-02) |

## Consequences(トレードオフ、影響)

- **利点(判断の再現性)**: 次に同種の契約が現れたとき、原則へ照らすだけで済む。ADR-0007 の「4つ」で止まらない
- **利点(trust の位置)**: 信頼ラベルの authority が実装上の1箇所(`source_connector`)に固定される。上書きの配線を T-029 でテストできる
- **コスト(契約数の主張が変わる)**: ADR-0007 Consequences の「27 → 4」は採択時点の値であり、増える。ただし増やす条件が原則として書かれたので、§6 が27へ膨張した時のような無制限な増加にはならない
- **コスト(判定の余地)**: 「実行系固有か」の判定に幅がある。境界が曖昧な契約が出たら、その判断自体を ADR に書く
- **North Star への影響**: §6.2 の `SourceMap` は field 構成を一部読み替えて実装する(`version` の意味衝突、必須度)。差分と理由は `schemas/source-map.schema.json` の `description` に記す。**変更ルール1に従い North Star 本文は改訂しない**(§6 の扱いを改める提案は learning-log に `northstar-proposal` として起票済み)
