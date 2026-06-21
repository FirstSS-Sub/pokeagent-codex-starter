# Prompt: Search API / MCTS導入計画

Goal: 公式RL+MCTS sampleをもとに、PTCG ABC agentへ局所的なSearch API評価を導入する計画を作ってください。

Constraints:
- いきなり全分岐MCTSをしない。
- attack候補、target候補、support候補など上位N件だけ評価する。
- Search APIが使えない場合はrule-basedへfallbackする。
- タイムアウトを最優先で避ける。
- 外部通信なし。

Done when:
- 1時間以内に作れるsmoke testが定義される。
- 必要なfixtureとログ項目が明確。
- 期待される勝率改善仮説と失敗リスクが整理される。
