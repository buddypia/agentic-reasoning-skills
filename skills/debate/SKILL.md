---
name: multi-llm-debate
description: 複雑な意思決定・作業向け。複数のLLMが異なる視点（Proponent、Opponent、Moderator）から議論・批判し合い、より正確で多角的な結論を導き出す
---

# Multi-LLM Debate（複数LLM討論）

3つの**異なるベンダーのLLM**（Antigravity CLI / Claude Code / Codex）が賛成派・反対派・中立派の役割で討論し、多角的な結論を導く。**APIキー不要** — 各CLIの購読認証（subscription）を利用する。

各エージェントは互いのコンテキストから隔離され、指定ロールのみに基づいて分析する。

> セキュリティ注意: 討論結果には入力内容に基づく分析が含まれます。機密情報の共有・公開に注意してください。

## ワークフロー

```
[討論テーマ]
   ↓
[Step 1: Proponent（賛成派）]  Antigravity CLI (agy) · Gemini 3.5 Flash
   ↓
[Step 2: Opponent（反対派）]   Claude Code (claude) · claude-opus-4-8   ※賛成派の主張を踏まえる
   ↓
[Step 3: Moderator（中立派）]  Codex (codex) · gpt-5.5（reasoning xhigh）
   ↓
[Step 4: 結果の統合表示]
```

## 前提条件（CLIバックエンド）

3つのCLIがインストール済み・**認証済み**であること（購読認証、APIキー不要）:

| 役割 | CLI | モデル |
|------|-----|--------|
| Proponent（賛成派） | `agy`（Antigravity CLI） | Gemini 3.5 Flash (High) |
| Opponent（反対派）  | `claude`（Claude Code） | `claude-opus-4-8` |
| Moderator（中立派） | `codex`（Codex CLI）    | `gpt-5.5`（reasoning xhigh） |

長文（long-form）入力は全て **stdin 経由**で各CLIに渡され、構造化出力（JSON）で次段へ受け渡される（ARG_MAX/エスケープ問題を回避）。

## venv 環境設定

- [x] venv インストール済み（チェック済みならスキップ）

```bash
cd <skill-dir>/scripts
python3.13 -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt   # pydantic / python-dotenv / pyyaml のみ（LLM SDK 不要）
```

## 使用方法（推奨: run.sh ラッパー）

```bash
# run.sh は venv を自動有効化する
<skill-dir>/scripts/run.sh "AIエージェントを顧客サポートに導入すべきか？"

# コンテキスト付き入力（推奨 — より質の高い討論が得られる）
<skill-dir>/scripts/run.sh "AIエージェントを顧客サポートに導入すべきか？

[コンテキスト]
- B2B SaaS（従業員500名、顧客2000社）
- 平均応答時間: 4時間 / 月間問い合わせ: 約3000件
- 予算: 年間500万円以内 / SOC2準拠必須"

# 詳細出力（3ロール全表示） / JSON出力
<skill-dir>/scripts/run.sh --verbose "ChatGPT を業務に全面導入すべきか？"
<skill-dir>/scripts/run.sh --json "リモートワークを恒久化すべきか？"
```

### 直接実行 / モデル上書き（venv手動有効化）

```bash
python main.py "討論トピック"
# 役割別モデル上書き（任意）
python main.py "トピック" \
    --proponent-model gemini-3.5-flash \
    --opponent-model claude-opus-4-8 \
    --moderator-model gpt-5.5
```

## 環境変数（任意）

| 変数 | 既定 | 用途 |
|------|------|------|
| `MULTILLM_REASONING_EFFORT` | `xhigh` | Codex の推論強度（none/low/medium/high/xhigh） |
| `MULTILLM_CLI_TIMEOUT` | `360` | CLI 呼び出しタイムアウト（秒） |
| `MULTILLM_AGY_PRINT_TIMEOUT` | `5m` | Antigravity CLI の `--print-timeout` |
| `MULTILLM_CLAUDE_MODEL` / `MULTILLM_CODEX_MODEL` | — | バックエンド別モデル上書き |
| `DEBATE_{PROPONENT,OPPONENT,MODERATOR}_MODEL` | — | 役割別モデル上書き |
| `DEBATE_{PROPONENT,OPPONENT,MODERATOR}_PROVIDER` | — | 役割別 provider（gemini/anthropic/openai/mock） |

> オフライン契約テストは `provider=mock`（例: `DEBATE_PROPONENT_PROVIDER=mock`）で実行可能。

## 入力形式（推奨）

討論トピックだけでなく**コンテキスト情報**も入力すると、より質の高い討論結果が得られる。

```
討論トピック

[コンテキスト]
- 背景情報、制約条件、前提条件
- 関連するドメイン知識 / 検討すべき観点・優先事項
```
