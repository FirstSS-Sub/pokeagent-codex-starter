# 開始チェックリスト

## 1. アカウント/手続き

- [ ] Kaggleアカウントにログインできる。
- [ ] Kaggleの電話認証/本人確認を済ませた。
- [ ] Simulation CategoryにJoinし、Rulesを承諾した。
- [ ] Strategy CategoryにJoinし、Rulesを承諾した。
- [ ] Teamを作成した。
- [ ] 賞金を狙う場合、Simulation/StrategyでTeam構成を一致させた。
- [ ] Kaggle API tokenを使う場合、credential file または `.env` をローカルに用意した（実値は表示しない/コミットしない）。

## 2. ローカル依存

必須/推奨:

- [ ] Git
- [ ] Python 3.10+
- [ ] curl
- [ ] tar/gzip
- [ ] unzip
- [ ] Codex CLI/App

任意:

- [ ] Kaggle CLI
- [ ] jq
- [ ] Docker
- [ ] GPU/CUDA（学習する場合）

確認:

```bash
./scripts/check_prereqs.sh
```

## 3. 公式情報取得

Dry run:

```bash
./scripts/fetch_public_metadata.sh --dry-run
```

実行:

```bash
./scripts/fetch_public_metadata.sh --out cache/public/latest
```

## 4. 最小提出

```bash
mkdir -p local_submissions/minimal-agent
cp templates/submission_minimal/main.py local_submissions/minimal-agent/main.py
# Kaggle公式Data/Starter Notebookから deck.csv を取得して置く
./scripts/package_submission.sh local_submissions/minimal-agent runs/submission-minimal.tar.gz
```

## 5. Kaggle側で確認

- [ ] Simulation Submissions tabから提出した。
- [ ] Validation EpisodeがErrorになっていない。
- [ ] Error時はagent logをダウンロードした。
- [ ] 変更点、submission id、scoreを `runs/` に記録した。

## 6. Codexに渡す最初のプロンプト

- `prompts/00-research-refresh.md`
- `prompts/01-first-local-eval.md`
- `prompts/02-parallel-ptcg-tasks.md`
