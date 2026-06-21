# Prompt: 日次トップEpisodeメタ解析

Goal: Kaggle公開日次トップEpisode datasetを少量サンプリングし、現在の上位デッキ傾向を抽出してください。

Constraints:
- 全量DLしない。
- まずmanifestとファイルサイズを確認し、20件だけ取得する。
- `cache/` と `runs/` に保存し、git管理しない。
- 取得元URL、取得日時、対象ファイルをsummaryに残す。
- team名、winner、deck signature、主要カード頻度、turn countを抽出する。

Done when:
- `runs/YYYYMMDD-meta/summary.md` ができる。
- top archetypeとキーカード頻度が見える。
- 次に改善すべきデッキ/agent仮説が3つ出る。
