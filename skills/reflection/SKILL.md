---
name: multi-llm-reflection
description: 高品質なコンテンツ生成向け。複数の異なるLLMが Generator→Critic→Refiner の3段階で草案を作り、批判し、改善する自己反省ワークフロー
---

# Multi-LLM Reflection（複数LLM自己反省）

3つの**異なるベンダーのLLM**（Antigravity CLI / Claude Code / Codex）が Generator・Critic・Refiner の役割で、生成→批判→改善の3段階リフレクションを実行する。**APIキー不要** — 各CLIの購読認証（subscription）を利用する。

各エージェントは独立したコンテキストで、指定ロールのみに基づいて処理する。

> セキュリティ注意: 出力には入力内容に基づく分析が含まれます。機密情報の共有・公開に注意してください。

## ワークフロー

```
[タスク/質問]
   ↓
[Step 1: Generator（生成）]  Antigravity CLI (agy) · Gemini 3.5 Flash    → 初回ドラフト
   ↓
[Step 2: Critic（批判）]     Claude Code (claude) · claude-opus-4-8       → 強み・弱み・改善提案
   ↓
[Step 3: Refiner（改善）]    Codex (codex) · gpt-5.5（reasoning xhigh）   → 批判を反映した最終版
```

## 前提条件（CLIバックエンド）

3つのCLIがインストール済み・**認証済み**であること（購読認証、APIキー不要）:

| 役割 | CLI | モデル |
|------|-----|--------|
| Generator（生成） | `agy`（Antigravity CLI） | Gemini 3.5 Flash (High) |
| Critic（批判）    | `claude`（Claude Code） | `claude-opus-4-8` |
| Refiner（改善）   | `codex`（Codex CLI）    | `gpt-5.5`（reasoning xhigh） |

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
<skill-dir>/scripts/run.sh "リモートワークが生産性に与える影響を説明して"

# コンテキスト付き入力（推奨 — より質の高い出力が得られる）
<skill-dir>/scripts/run.sh "新規SaaSの技術アーキテクチャを設計して

[コンテキスト]
- B2B請求管理システム / 想定規模: 初年度1000社
- 制約: AWS、SOC2準拠必須 / 予算: インフラ月額50万円以内"

# 詳細出力（3段階全表示） / JSON出力
<skill-dir>/scripts/run.sh --verbose "プロンプトエンジニアリングのコツをまとめて"
<skill-dir>/scripts/run.sh --json "効果的なコードレビューの観点を整理して"
```

### 直接実行 / モデル上書き（venv手動有効化）

```bash
python main.py "タスク/質問"
# 役割別モデル上書き（任意）
python main.py "タスク" \
    --generator-model gemini-3.5-flash \
    --critic-model claude-opus-4-8 \
    --refiner-model gpt-5.5
```

## 環境変数（任意）

| 変数 | 既定 | 用途 |
|------|------|------|
| `MULTILLM_REASONING_EFFORT` | `xhigh` | Codex の推論強度（none/low/medium/high/xhigh） |
| `MULTILLM_CLI_TIMEOUT` | `360` | CLI 呼び出しタイムアウト（秒） |
| `MULTILLM_AGY_PRINT_TIMEOUT` | `5m` | Antigravity CLI の `--print-timeout` |
| `MULTILLM_CLAUDE_MODEL` / `MULTILLM_CODEX_MODEL` | — | バックエンド別モデル上書き |
| `REFLECTION_{GENERATOR,CRITIC,REFINER}_MODEL` | — | 役割別モデル上書き |
| `REFLECTION_{GENERATOR,CRITIC,REFINER}_PROVIDER` | — | 役割別 provider（gemini/anthropic/openai/mock） |

> オフライン契約テストは `provider=mock`（例: `REFLECTION_GENERATOR_PROVIDER=mock`）で実行可能。

## 入力形式（推奨）

タスクだけでなく**コンテキスト情報**も入力すると、より質の高い出力が得られる。

```
[タスク/質問]
解決したい問題や作成したい内容

[コンテキスト]
- 背景情報、制約条件、前提条件
- 関連するドメイン知識 / 期待する出力形式・優先事項
```
