# Pokémon Trading Card Game AI Battle Challenge 調査ブリーフ

調査日: 2026-06-20（JST）

## 0. 先に結論

`https://ptcg-abc.pokemon.co.jp/` は、現在開催中の **Pokémon Trading Card Game AI Battle Challenge（ポケカABC）** の公式サイトです。

以前このrepoにあった「PokéAgent Challenge / Pokémon Showdown / Emerald speedrunning」という理解は誤りです。このコンテストは **ポケモンカードゲーム（TCG）用のAI Training AgentをKaggle上で競わせる大会** です。

重要な構造は2つです。

1. **Simulation Category**
   - Kaggle competition: `pokemon-tcg-ai-battle`
   - `main.py` と `deck.csv` を含む `.tar.gz` を提出。
   - Kaggle環境で他agentと継続的に自動対戦。
   - live leaderboardのSkill Ratingで順位が決まる。
   - 賞金はないがKaggle points/medalsはある。

2. **Strategy Category**
   - Kaggle competition: `pokemon-tcg-ai-battle-challenge-strategy`
   - Simulation部門に提出したAI agentの戦略ロジック、デッキコンセプト、検証をWriteupとして提出。
   - 上位8チームは各$30,000の対象。さらに第二ラウンド参加資格を得る。
   - 評価はModel Score 70%、Deck Score 20%、Report Score 10%。

最短の勝ち筋は、**Simulationで強いデッキ/agentを作りつつ、その意思決定と検証をStrategy Writeupに変換する** ことです。

## 1. このコンテストは何か

ポケモンカードゲームは、60枚デッキ、ドロー順、相手の手札/山札という不完全情報、カード効果、相性、運要素が絡むゲームです。この大会では、その環境で勝てるAI Training Agentを作ります。

AI側の主な難所:

- 固定デッキ内でのプレイ順序最適化
- 相手の手札・山札・Prizeの不完全情報
- サポート/グッズ/スタジアム/エネルギーの使い順
- Prize race（何ターンで何枚取るか）
- タイムアウト回避
- ルール差分・シミュレータ挙動の把握
- メタゲーム（流行デッキ）への適応

公式FAQでは、AIがデッキを自動構築する必要はないと説明されています。つまり、実務上は **人間/Codexがデッキを設計し、agentがそのデッキを高精度にプレイする** 形でよいです。

## 2. Simulation Category

### 基本

- Kaggle URL: <https://www.kaggle.com/competitions/pokemon-tcg-ai-battle>
- 開始: 2026-06-16 11:00 UTC / 2026-06-16 20:00 JST
- 最終提出: 2026-08-16 23:59 UTC / 2026-08-17 08:59 JST
- Entry/Team Merger deadline: 2026-08-09 23:59 UTC
- 最大チーム人数: 5
- 1日最大提出: 5
- 最終評価対象: 最新2 submissionが追跡される。Leaderboardには最良agentが表示される。
- Submission size limit: 20GB
- Identity verification: required

### 提出形式

公式Kaggleページの説明では、提出物は `.tar.gz` で、top-levelに以下を含めます。

```text
main.py
deck.csv
```

`main.py` の `agent(obs_dict)` が、各ステップで選択するoption indexのリストを返します。

初回 `obs.select is None` のときはデッキリストを返します。通常ステップでは、環境が提示する合法optionだけから選びます。

### 評価

- まずValidation Episodeとして、自分自身との対戦で動作確認される。
- 失敗するとSubmissionはErrorになり、agent logsを確認する。
- 成功後、初期Skill Rating `μ0=600` でAll Submissions poolへ入る。
- 近いrating同士でEpisodeが組まれ、勝敗/引き分けでratingが更新される。
- 勝ち方の点差ではなく、Episode結果がrating更新の中心。
- deadline後も約2週間ゲームが継続され、leaderboard収束後にfinal。

### データ

Kaggle Dataページには、カードID、カード名、拡張情報、カード画像参照を含むCSV/PDFが提供されています。

主要ファイル:

- `Card_ID_List_EN.pdf`
- `Card_ID_List_JP.pdf`
- `EN Card Data.csv`
- `JP Card Data.csv`

加えて、Kaggle公式Discussionでは日次トップEpisode datasetのindexが案内されています。

- Index: <https://www.kaggle.com/datasets/kaggle/pokemon-tcg-ai-battle-episodes-index>
- 2026-06-19時点のmanifestでは、日次episode datasetは数GB〜20GB超。
- 全量DLではなく、上位/代表episodeだけサンプリングして解析するのが現実的。

## 3. Strategy Category

- Kaggle URL: <https://www.kaggle.com/competitions/pokemon-tcg-ai-battle-challenge-strategy>
- 開始: 2026-06-16 11:00 UTC / 2026-06-16 20:00 JST
- 最終提出: 2026-09-13 23:59 UTC / 2026-09-14 08:59 JST
- Judging: 2026-09-14 - 2026-10-11 予定
- 賞金: $240,000 total。8 finalistsに各$30,000。
- 完全な提出にはSimulation Categoryへの参加が必要。
- Team構成はSimulation側とStrategy側で一致させる必要がある。
- Hackathon形式のため、各Teamは1 submissionのみ。
- Writeupは2,000語以内。Track選択、タイトル、subtitle、詳細分析、Media Galleryが必要。

評価配分:

```text
Model Score 70%
- 手法の明確さ/独自性/技術的妥当性
- repeated matchesでの安定性
- 特定初期状態/相性/偶然への過依存回避
- Simulation部門での成績

Deck Score 20%
- デッキコンセプトの明確さ
- 主要カード選択とゲームプランへの適合

Report Score 10%
- 論理構成と読みやすさ
- 図表や可視化の有効性
```

## 4. 参加方法

1. Kaggleアカウントを用意する。
2. Kaggleで必要な本人確認/電話認証を済ませる。
3. Simulation CategoryでRulesを承諾し、Joinする。
4. Strategy CategoryにもJoinする。
5. Teamを作る。賞金を狙う場合は両部門でTeam構成を一致させる。
6. Dataページと公式Starter Notebookを確認する。
7. `main.py` と `deck.csv` を作る。
8. `.tar.gz` を作成してSimulationのSubmissions tabから提出する。
9. Validation Episodeが通ることを確認する。
10. Leaderboard/agent logs/episode replaysを見て改善する。
11. Strategy Writeupに、戦略、デッキ、実験、失敗例、改善履歴を整理して提出する。

## 5. ルール/制約の要点

- 使用カードは大会指定リストのカードのみ。
- AIがデッキ構築する必要はない。
- Competition DataはCompetition Use Only。終了後は削除が求められる。
- Competition Dataを非参加者に再配布しない。
- 外部データ/ツール/LLMは、全参加者に合理的にアクセス可能で、ライセンス上問題ないものに限る。
- AutoML/LLM等の自動化ツールは、ルール遵守できるライセンスなら利用可能。
- 勝者はコード/手法/再現手順/環境説明を提出する義務がある。
- 実用上重要な情報はKaggle Discussion/Notebookなど、全員に公開された場で共有する。DMや限定Discord/LINEでの非公開共有は危険。

## 6. 現在のLeaderboard snapshot

取得日時: 2026-06-20 JST、Kaggle公開APIから取得。Leaderboardは常に変動します。

Simulation metadata snapshot:

- total teams: 約2,254
- total joined users: 約6,112
- total submissions: 約4,067

Top 10 snapshot:

```text
#  score   team
1  1315.3  TrustHub hiroingk
2  1294.4  foo_foo
3  1256.0  カドラバ Kadoraba
4  1237.6  vibechu
5  1229.5  Naoki Maeda
6  1225.6  Stagapult
7  1218.6  好吃的台灣拉麵
8  1218.3  blue0620
9  1215.7  graybackcat
10  1208.1  tototo
```

注意: まだ開催4日目程度のため、これは「最終入賞者」ではありません。Objectiveの「上位入賞者の戦略」は、現時点では **上位候補/暫定上位勢の公開リプレイ・公開Notebook・公開Discussionから推定できる戦略** として扱います。

## 7. 現時点で見える上位戦略

### 7.1 まず強いデッキが重要

Kaggle公式Discussionで、agentは基本的に `main.py` と `deck.csv` を一体で提出する形式と説明されています。つまり、評価されるのは「汎用TCGプレイヤー」より **固定デッキを高精度に回すagent** に近いです。

現在の公開トップEpisodeを少量サンプリングしたところ、以下の傾向が見えました。

- **Mega Lucario ex / Fighting Gong / Lillie's Determination / Solrock / Lunatone / Hariyama系** が非常に多い。
- **Alakazam / Abra / Kadabra / Dunsparce-Dudunsparce / Hilda / Battle Cage系** も上位Episodeに出ている。
- 暫定1位 `TrustHub hiroingk` は、観測できた2026-06-19の公開トップEpisodeではAlakazam系を使用していた。
- `DeeperNet` など複数チームはMega Lucario系を使用していた。

ただし、これは公開上位Episodeのサンプルからの推定であり、非公開の最新submissionや最終戦略を意味しません。

### 7.2 ルールベースはまだ強い

公式スターターNotebookは、複数のデッキでrule-based agentを提供しています。

- Iono deck: エネルギー大量展開 + Iono's Voltorbの高打点。
- Dragapult ex deck: Phantom Diveで複数Prizeを狙う。action scoringで行動順を制御。
- Mega Abomasnow ex deck: 基本水エネルギーを大量採用し、Hammer-lancheの火力を狙う。
- Mega Lucario ex deck: Mega Lucario, Hariyama, Solrockを状況で使い分ける。

開催初期は、モデル学習よりも **合法手選択、プレイ順、ターゲット選択、サポート使用タイミング、タイムアウト回避** の差が大きく出ます。

### 7.3 Search API / MCTSは公式に用意されている

公式の「Reinforcement Learning and MCTS sample code」は、Transformer風モデル、Search API、MCTS、self-play trainingのサンプルを含みます。

重要な示唆:

- シミュレータに対して `search_begin`, `search_step`, `search_end` を使い、行動後の実際の結果を見られる。
- 複雑なカード効果の手計算を避け、探索で確認できる。
- 小さい探索回数でも、rule-based scoringに混ぜる価値がある。
- 本格学習より前に、MCTSで「攻撃/サポート/進化/ターゲット」の候補を比較するのが現実的。

### 7.4 メタ解析が毎日必要

Kaggle公式は日次トップEpisode datasetを提供しています。これを使うと、上位で実際に使われているdeck archetype、勝敗、ターン数、キーカード、負け筋を抽出できます。

Codexで作るべき解析:

- `episode_id -> team names -> deck signature -> winner -> turn count`
- card ID頻度、2枚以上採用カード、ace spec、energy比率
- 上位デッキ同士のmatchup matrix
- 負けたゲームの共通原因
  - 展開遅れ
  - エネルギー不足
  - 進化ライン欠損
  - 攻撃せずターン終了
  - タイムアウト/invalid return
  - Prize raceで不利なtarget選択

### 7.5 SNS/Redditから得られる戦略は少ない

Web/SNS/Reddit検索では、2026-06-20時点でこの新コンテストの具体的な上位戦略はほぼ見つかりませんでした。

理由:

- 開催直後で、最終入賞者がまだ存在しない。
- Kaggle公式Discussionで、重要情報はKaggle forum/notebookに公開することが推奨されている。
- 非公開DM/限定SNS共有はPrivate Sharingとして危険。

したがって、現時点で信頼できる戦略情報源は以下です。

1. 公式Kaggle Overview/Rules/Evaluation/Data。
2. 公式Starter Notebook。
3. Kaggle Discussion。
4. Kaggle公開Leaderboard。
5. Kaggle日次トップEpisode dataset。

## 8. Kaggleとは何か / 今回との関係

KaggleはGoogle傘下のデータサイエンス/機械学習コンペ、データセット、Notebook、Discussion、Leaderboardのプラットフォームです。

典型的には、参加者がモデル/コード/提出ファイルを作り、Kaggle上の評価環境やhidden testでスコアが出ます。今回のSimulation部門は通常のCSV提出ではなく、Kaggle Environments系の **agent対戦型Simulation competition** です。

今回Kaggleで使う機能:

- Competition Rulesの承諾
- Team作成/Team merge
- Data download
- Notebook/Starter code
- Submission upload
- Validation Episode
- Leaderboard
- Discussion
- Writeup/Project submission

## 9. Codexで勝つための基本思想

Codexを「対戦中に毎ターン考えるLLM」として使うのは主戦略にしません。

理由:

- 対戦はKaggle環境内で自動実行され、提出物は自己完結した `main.py` である必要がある。
- LLM API呼び出しは外部通信・コスト・遅延・再現性・ルール上の合理的アクセス性でリスクがある。
- 強くなる主因は、デッキ理解、合法手選択、探索、メタ解析、検証ループ。

Codexにやらせるべきこと:

1. 公式情報の差分監視。
2. Starter Notebook読解。
3. リプレイJSON解析。
4. deck archetype抽出。
5. action scoring改善。
6. Search API/MCTSの局所導入。
7. Validation/timeout/invalid return対策。
8. 実験ログ自動整理。
9. Strategy Writeupの素材化。

## 10. 次にやること

1. Kaggleで両部門にJoinし、Rulesを承諾する。
2. `scripts/check_prereqs.sh` を実行する。
3. `scripts/fetch_public_metadata.sh --out cache/public/latest` を実行する。
4. 公式Starter Notebookから、まずMega LucarioまたはAlakazam系に近いdeck/agentを理解する。
5. `templates/submission_minimal/` で提出パッケージの形を確認する。
6. Validation Episodeを通す。
7. 日次トップEpisodeをサンプリングして、現在のメタを毎日更新する。
8. 改善は「デッキ選択 → action scoring → Search API → self-play学習」の順で進める。
