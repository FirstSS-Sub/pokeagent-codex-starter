# Prompt: action scorer改善

Goal: PTCG ABC agentの行動選択を、合法手guard + scoring + deterministic tie-breakに整理し、Validation失敗を減らしてください。

Constraints:
- 既存挙動を変える場合は理由をコメント/notesに残す。
- `obs.select.minCount/maxCount` とoption index範囲を必ず守る。
- timeout guardを入れる。
- 攻撃は通常ターン最後にする。
- サポート/グッズ/進化/エネルギー/攻撃/target選択を分けて評価する。

Done when:
- fixture observationで合法indexだけ返す。
- `scripts/package_submission.sh` でtar.gzを作れる。
- 改善前後の期待効果がsummaryにある。
