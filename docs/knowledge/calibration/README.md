# calibration/ — gate較正記録

gateごとのprecision / false block / 段階昇降格(shadow → warn → block)の判断根拠を記録する(North Star §17.0、§17.2、§19.7)。

## ルール

- 1 gate = 1ファイル(例: `gate-oracle.md`)。計測値、期間、判断、根拠を時系列で追記する
- gate段階・閾値の**現在値の正本は `policies/gate-policy.yaml`**。ここは根拠の記録のみ(値を二重管理しない)
- `policies/CHANGELOG.md` のエントリと相互リンクする
- 昇格条件の初期値: shadow 4週間以上 + precision 90%以上 + 明示的合意(§17.0)。この条件自体の変更もここに記録する
