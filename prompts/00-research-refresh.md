# Prompt: PTCG ABC 公式情報の再確認

Goal: Pokémon Trading Card Game AI Battle Challenge の現在の参加方法・ルール・leaderboard・starter notebook・episode dataset情報を、公式ソース優先で再確認してください。

Context:
- `docs/research-brief.md`
- `config/sources.txt`
- `scripts/fetch_public_metadata.sh`

Constraints:
- 推測禁止。公式サイト、Kaggle Overview/Rules/Data/Evaluation/Discussion、API docs、公式Notebookを優先。
- Reddit/SNSは参考扱い。戦略の根拠にする場合はKaggle公開情報で裏取り。
- 現在日付を明記し、Simulation部門とStrategy部門の違いを崩さない。
- Kaggle credentialや秘密値は表示しない。

Done when:
- 変更が必要な箇所のdiff案を出す。
- 新しい参加手順・ルール変更・重要baseline更新があれば箇条書きで示す。
- Leaderboard snapshotは取得日時つきで示す。
