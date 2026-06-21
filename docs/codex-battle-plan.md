# CodexでPTCG ABCに勝ちに行く運用計画

## 1. 方針

Codexは対戦中のLLMではなく、**開発チーム全体の加速装置** として使います。

本番提出物はKaggle環境で動く `main.py + deck.csv` です。対戦中にCodexや外部LLMへ毎ターン問い合わせる設計は、遅延・外部通信・再現性・ルール面のリスクが高いため初手では避けます。

Codexの主用途:

1. 公式ページ/Discussion/Leaderboardの差分調査。
2. 公式Starter Notebook読解。
3. リプレイJSON解析。
4. デッキ/メタ解析。
5. ルールベースagent改善。
6. Search API/MCTS導入。
7. ローカル/Validation/提出ログのトリアージ。
8. Strategy Writeup作成。

## 2. 推奨アーキテクチャ

```text
Kaggle observation
  -> state parser / feature extractor
  -> legal option scorer
       - setup score
       - attack/prize score
       - draw/search score
       - energy attachment score
       - switch/retreat score
       - disruption score
  -> optional Search API / MCTS evaluator
  -> deterministic tie-breaker
  -> timeout guard
  -> action return

Offline side
  -> episode downloader/sampler
  -> deck archetype extractor
  -> matchup analyzer
  -> failure classifier
  -> experiment log / writeup notes
```

## 3. まず狙うデッキ/agent

2026-06-20時点の公開トップEpisodeサンプルでは、以下が有力です。

1. **Mega Lucario ex系**
   - Mega Lucario ex / Fighting Gong / Lillie's Determination / Solrock / Lunatone / Hariyama。
   - 公開Starter Notebookがあり、上位Episodeでも頻出。
   - 複数attack planを持てるので、action scoring改善の余地が大きい。

2. **Alakazam系**
   - Abra / Kadabra / Alakazam / Dunsparce-Dudunsparce / Hilda / Battle Cage。
   - 暫定1位の観測Episodeで使用を確認。
   - 進化ラインと展開安定性が重要。

初手はMega Lucario系を推奨します。理由は公式サンプルがあり、公開Episode上の採用数が多く、Codexで改善しやすいheuristic項目が多いためです。

## 4. 7日ロードマップ

### Day 0: 準備

- Kaggle両部門にJoin。
- Rules承諾、本人確認/電話認証。
- `./scripts/check_prereqs.sh`
- `./scripts/fetch_public_metadata.sh --out cache/public/latest`
- 公式Starter Notebookを保存/確認。

### Day 1: Validationを通す

- 公式サンプルまたは `templates/submission_minimal/` から `main.py + deck.csv` を作る。
- `.tar.gz` を作る。
- Validation Episodeを通す。
- agent logsを保存する。

### Day 2: リプレイ解析

- 日次トップEpisode datasetのmanifestを取得。
- 全量ではなく20〜100件だけサンプリング。
- deck signature, winner, turn count, key cardsを抽出。
- `runs/YYYYMMDD-meta/summary.md` に保存。

### Day 3: action scoring改善

- 公式Starter NotebookのMega Lucario agentを読み、score関数を整理。
- 優先度を明文化。
  - 進化できるならする
  - attackerを育てる
  - Prizeを取れる攻撃を選ぶ
  - サポートを無駄撃ちしない
  - 攻撃は原則ターン最後
- invalid return / timeout / no-opを0にする。

### Day 4: Search API導入

- 重要候補だけ `search_begin/search_step` で比較。
- 攻撃候補、target候補、support候補に限定して探索する。
- 全分岐探索ではなく、rule-basedで絞った上位N個だけ評価する。

### Day 5: A/B提出

- 1日5回の提出枠を使い、2〜3案だけ試す。
- 最新2submissionしか追跡されない点に注意。
- 提出名、commit、deck hash、変更点、score推移を記録。

### Day 6: Strategy Writeup素材化

- 仮説、変更、結果、失敗例を整理。
- デッキコンセプト図、decision flow、ablation表を作る。
- Model Score/Deck Score/Report Scoreの配点に合わせる。

### Day 7: 反復ループ確立

- 毎日: leaderboard snapshot取得。
- 毎日: top episode 20〜100件解析。
- 毎日: 負け筋上位3件だけ改善。
- 毎日: writeup素材を追記。

## 5. Codex並列運用

OpenAI Codexの公式マニュアルでは、複雑タスクはGoal/Planで定義し、小さな作業に分割し、検証可能なDone条件を入れるのが有効です。また、Worktreeは同じGit repoで複数タスクを干渉せず進めるために使えます。

推奨Worktree/Thread分割:

```text
main/local
  docs, scripts, final integration only

worktree/meta-analyzer
  episode dataset sampler, deck signature extractor, reports

worktree/agent-heuristics
  main.py scoring, deterministic decisions, timeout guard

worktree/search-api
  Search API/MCTS smoke test and local evaluation

worktree/writeup
  Strategy report outline, charts, experiment logs
```

注意:

- 2つのCodex threadに同じファイルを触らせない。
- `data/`, `cache/`, `runs/`, `local_submissions/` はgit管理しない。
- 公式提出やKaggleへのアップロードはHuman in the Loopで確認する。

## 6. Codexに投げる具体プロンプト

### メタ解析

```text
このrepoで、Kaggle公開日次episode datasetを20件だけサンプリングして、
team名、deck signature、winner、turn count、主要カード頻度を抽出する
Pythonスクリプトを作ってください。

Constraints:
- data/cache/runs はgit管理しない。
- 全量DLしない。manifestから指定件数だけ取る。
- 取得元URLと取得日時をsummaryに残す。
- 既存の scripts/fetch_public_metadata.sh を読んで合わせる。

Done when:
- dry-runできる。
- 20件取得時の見積容量が出る。
- runs/YYYYMMDD-meta/summary.md が生成される。
```

### ルールベース改善

```text
公式Mega Lucario starter agentをベースに、
行動選択を「候補抽出 -> scoring -> tie-break」に分けて読みやすくしてください。

Constraints:
- 対戦挙動を変える前に既存ロジックをテストで固定する。
- invalid optionを返さないguardを必ず入れる。
- timeout guardを入れる。
- 変更理由を docs/agent-notes.md に残す。

Done when:
- sample observation fixtureで合法indexだけ返す。
- package_submission.shでtar.gzを作れる。
```

### Search API

```text
Search APIの公式sampleを読み、攻撃候補だけを比較する最小実装を設計してください。

Constraints:
- 全分岐MCTSはしない。
- attack option上位3件だけsearch_stepで比較。
- Search APIが使えない環境ではrule-basedにfallback。
- 外部通信なし。

Done when:
- 1つのfixtureで、search前後の選択理由がログに残る。
```

## 7. 実験ログ形式

`runs/YYYYMMDD-HHMMSS-experiment-name/summary.md`

必須:

- date/time
- source URLs / fetched files
- commit SHA
- submission name/hash
- deck signature/hash
- agent version
- number of sampled episodes or battles
- win/loss/draw
- timeout count
- invalid return count
- crashes/errors
- leaderboard score before/after
- observed meta shift
- conclusion
- next action

## 8. 公式提出前チェック

- [ ] Rulesを再確認した。
- [ ] `main.py` と `deck.csv` がtar.gz top-levelにある。
- [ ] `deck.csv` は60行/60枚で、指定カードリストに準拠している。
- [ ] 同名4枚制限、ACE SPEC 1枚制限、Basic Pokémonあり。
- [ ] agentは合法option indexだけ返す。
- [ ] `minCount <= len(action) <= maxCount` を守る。
- [ ] duplicate indexなし。
- [ ] `obs.select is None` でdeckを返す。
- [ ] タイムアウトしない。
- [ ] validation logsを確認する。
- [ ] Strategy Writeup用に変更理由を残した。
