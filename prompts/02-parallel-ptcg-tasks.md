# Prompt: PTCG ABCを並列に進める

このrepoで、可能ならWorktreeまたはサブエージェントを明示的に使って並列調査してください。変更は親agentが統合するまで行わないでください。

調査単位:

1. Official Notebook Reader
   - Mega Lucario / Dragapult / Iono / Mega Abomasnow / RL+MCTSの構造を読む。
   - action scoring, deck concept, packaging方法を抽出。

2. Episode Data Analyst
   - 日次トップEpisode dataset indexとファイル構成を確認。
   - 20件だけサンプルする安全な設計を作る。
   - deck signature抽出項目を定義。

3. Agent Heuristics Designer
   - `templates/submission_minimal/main.py` を土台に、合法手guard、timeout guard、deterministic tie-breakを設計。
   - 公式Starterと差分を整理。

4. Search API Designer
   - `matsuoinstitute.github.io/cabt/` と公式RL+MCTS notebookを読む。
   - attack候補だけを比較する最小Search API導入案を作る。

5. Strategy Writeup Planner
   - Strategy部門の評価配分（70/20/10）に合わせたWriteupアウトラインを作る。
   - 実験ログから図表化すべき項目を列挙。

各agentの出力:
- 重要URL/ファイル
- 実行コマンド
- 依存/危険操作
- 最初に実装すべき小タスク3つ
- 未確認点

最後に親agentが、勝率とStrategy評価の両方に効く順にタスクを並べてください。
