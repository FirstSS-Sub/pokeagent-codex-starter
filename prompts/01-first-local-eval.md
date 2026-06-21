# Prompt: 最小提出/ローカル検証導線を作る

Goal: PTCG ABC Simulation部門でValidation Episodeを通すための最小 `main.py + deck.csv + tar.gz` 導線を作ってください。

Context:
- `AGENTS.md`
- `docs/setup-checklist.md`
- `templates/submission_minimal/main.py`
- 公式Starter Notebook（Kaggle URLは `config/sources.txt`）

Constraints:
- まず `rg --files` で構成把握。
- package installや大量DLが必要なら、実行前に必要性・容量・コマンドを明示。
- Kaggle提出はユーザー確認なしに行わない。
- credentialsや秘密値は表示しない。
- Competition Dataは `data/` または `local_submissions/` に置き、git管理しない。

Done when:
- `main.py` と `deck.csv` をtar.gz top-levelに含めるコマンドがある。
- deck validationで起きうるエラー（invalid card ID / 4枚制限 / Basicなし / ACE SPEC制限）を確認できる。
- どこまでローカルで確認でき、どこからKaggle Validationが必要かが明確。
