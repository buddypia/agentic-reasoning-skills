# Recursive Meta-Cognition（再帰的メタ認知）

> ⚠️ **2026-05 更新**: バックエンドを**購読認証CLI**（Antigravity `agy` / Claude Code `claude` / Codex `codex`）に移行しました。**APIキーは不要**です（各CLIの購読認証を利用）。以下のAPIキー設定は旧バージョンの記述です。最新の利用方法は `SKILL.md` を参照してください。


このREADMEは環境設定・API設定・セットアップ・実行例・参考情報のまとめです。使用方法の詳細と出力例は `SKILL.md` を参照してください。

## セットアップ（Setup）

1. **Pythonバージョンの確認（Python Version）:**

```bash
cd <skill-dir>/scripts
python3.13 --version  # Python 3.13+ が必要
```

2. **仮想環境（venv）+ 依存関係のインストール（Install Dependencies）:**

```bash
cd <skill-dir>/scripts
python3.13 -m venv .venv
source .venv/bin/activate  # Windows: .venv\Scripts\activate
pip install -r requirements.txt
```

3. **環境変数の設定（オプション）:**

環境変数が既に設定されている場合、このステップはスキップ可能。

```bash
cat > .env << 'EOT'
GEMINI_API_KEY=your_gemini_api_key
ANTHROPIC_API_KEY=your_anthropic_api_key
OPENAI_API_KEY=your_openai_api_key
EOT
```

4. **設定ファイル（オプション）:**

```bash
cp <skill-dir>/config.example <skill-dir>/config.yaml
```

設定ファイルの自動探索は **カレントディレクトリ → スキルルート** の順で行います。固定したい場合は `--config` で明示指定してください。

## AI エージェント実行ガイド

このスキルが呼び出されたとき、AIは上記のセットアップが完了している前提で以下を実行すること:

### 実行コマンド

```bash
cd <skill-dir>/scripts
source .venv/bin/activate
python main.py "ユーザーのプロンプトをここに入力"
```

### 出力オプションの選択

| ユーザーの要望 | 推奨オプション |
|--------------|---------------|
| 最終結果のみ必要 | （オプションなし） |
| 各段階の詳細を見たい | `--verbose` |
| プログラムで処理したい | `--json` |
| JSONスキーマをフラットにしたい | `--json --output-schema flat` |
| デバッグが必要 | `--verbose --raw` |

### 実行例（Execution Examples）

```bash
# 基本
python main.py "AIの最新トレンドについて要約してください"

# 詳細出力（5ステージ表示）
python main.py --verbose "ChatGPT vs Claude vs Gemini の比較を調べてまとめて"

# JSON出力（後処理向け）
python main.py --json "プロンプトエンジニアリングのコツをまとめて"

# JSON出力（フラットスキーマ）
python main.py --json --output-schema flat "プロンプトエンジニアリングのコツをまとめて"

# プロバイダー割当（ランダム/シャッフル）
python main.py --random-providers "AIの最新トレンドについて要約してください"
python main.py --shuffle-providers "AIの最新トレンドについて要約してください"

# カスタムモデル指定
python main.py "量子コンピュータの最新動向を調査" \
  --decomposer-model gemini-2.0-flash \
  --solver-model gemini-2.0-flash \
  --verifier-model claude-3-5-sonnet-latest \
  --integrator-model gpt-4o \
  --reflector-model gpt-4o

# DevUIモード（現在は非対応）
python main.py --devui --port 8095
```

DevUIは軽量エンジン移行のため現在サポートされていない。

## 概要

Multi-LLM Reflectionパターンは、5つの異なるLLMエージェント（Agent）が順次処理を行い、
段階的にコンテンツの品質を向上させるワークフロー（Workflow）を実装している。

```
[ユーザープロンプト (User Prompt)]
       │
       ▼
┌─────────────────┐
│ Decomposer      │  ← Gemini（デフォルト）
│ (分解)          │     課題の要素化・論点抽出
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│ Solver          │  ← Gemini（デフォルト）
│ (解決)          │     サブタスクの解決案作成
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│ Verifier        │  ← Claude（デフォルト）
│ (検証)          │     矛盾・飛躍の検出と自律修正
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│ Integrator      │  ← OpenAI（デフォルト）
│ (統合)          │     回答草案の統合・修正反映
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│ Reflector       │  ← OpenAI（デフォルト）
│ (反省)          │     確信度・不確実性・反省を付与
└────────┬────────┘
         │
         ▼
[最終結果 (Final Result)]
```

### 各エージェントの役割

| エージェント | プロバイダー | モデル | 役割 |
|-------------|-------------|--------|------|
| Decomposer | Gemini | gemini-3.5-flash | 課題を分解し、サブタスク・前提・制約を整理 |
| Solver | Gemini | gemini-3.5-flash | サブタスクごとの解決案を作成 |
| Verifier | Claude | claude-opus-4-8 | 論理検証・自己修正の指摘 |
| Integrator | OpenAI | gpt-5.5 | 修正点を反映して統合回答草案を作成 |
| Reflector | OpenAI | gpt-5.5 | 最終回答・確信度・不確実性・反省を出力 |

## クイックスタート（Quick Start）

セットアップ完了後、以下で実行:

```bash
cd <skill-dir>/scripts
source .venv/bin/activate
python main.py "AIの最新トレンドについて要約してください"
```

## 用途

### 適用例

- **リサーチ（Research）**: 技術動向、市場調査、競合分析の整理
- **トレンド分析（Trend Analysis）**: AI/ML動向、ニュース要約
- **比較レポート（Comparison Report）**: 製品比較、技術比較、サービス評価
- **文章作成（Content Creation）**: ブログ記事、レポート、ドキュメント
- **意思決定支援**: 多角的な視点からの分析、リスク評価

### 適したユースケース

| ユースケース | 説明 | 具体例 |
|-------------|------|--------|
| **高品質なコンテンツ** | 複雑なタスクで高品質な出力が必要 | 技術ブログ記事、ホワイトペーパー |
| **客観的なレビュー** | 単一LLMの盲点を補いたい | 提案書のレビュー、設計ドキュメントの評価 |
| **段階的な改善** | 分解→解決→検証→統合→反省のプロセスを再現 | エッセイ、戦略メモ |
| **多角的な視点** | 異なるLLMの特性を活かしたい | 意思決定の根拠まとめ、リスク分析 |

### 不向きなユースケース

| ユースケース | 理由 | 代替案 |
|-------------|------|--------|
| シンプルな質問応答 | 5段階処理はオーバーヘッドが大きい | 単一LLMへの直接クエリ |
| リアルタイム性が必要 | 5回のAPI呼び出しで遅延が発生 | 単一LLM |
| 最新情報が必須 | Web検索機能がない | Web検索付きエージェント |
| コード生成 | 文章生成に最適化されている | コーディングエージェント |

## インストール（Installation）

### 1. 作業ディレクトリの準備

スキルの `scripts/` ディレクトリに移動するか、任意のプロジェクトディレクトリにファイルをコピーする。

```bash
# スキルディレクトリに移動
cd <skill-dir>/scripts

# または任意のディレクトリにコピー
cp -r <skill-dir>/scripts/* /path/to/your/project/
cd /path/to/your/project/
```

### 2. セットアップの実施

上記の **セットアップ（Setup）** に従って仮想環境・依存関係・環境変数・設定ファイルを用意する。

## 設定の優先順位（Configuration Priority）

設定は以下の優先順位で解決される:

1. **CLI引数（CLI Arguments）**（最優先）
2. **環境変数（Environment Variables）**
3. **設定ファイル（Configuration File）**（YAML/JSON）
4. **デフォルト値（Default Values）**（最低優先）

## 環境変数一覧（Environment Variables）

### APIキー

| 環境変数 | 説明 |
|---------|------|
| `GEMINI_API_KEY` | Google Gemini APIキー |
| `ANTHROPIC_API_KEY` | Anthropic Claude APIキー |
| `OPENAI_API_KEY` | OpenAI APIキー |
| `OPENAI_BASE_URL` | OpenAI互換エンドポイント（Azure OpenAI等） |

### モデルID

| 環境変数 | 説明 |
|---------|------|
| `GEMINI_MODEL_ID` | Geminiモデル |
| `ANTHROPIC_MODEL_ID` | Claudeモデル |
| `OPENAI_CHAT_MODEL_ID` | OpenAIモデル |

### ロール別

| 環境変数 | 説明 |
|---------|------|
| `REFLECTION_DECOMPOSER_PROVIDER` | Decomposerプロバイダー |
| `REFLECTION_DECOMPOSER_MODEL` | Decomposerモデル |
| `REFLECTION_DECOMPOSER_API_KEY` | Decomposer APIキー |
| `REFLECTION_SOLVER_PROVIDER` | Solverプロバイダー |
| `REFLECTION_SOLVER_MODEL` | Solverモデル |
| `REFLECTION_SOLVER_API_KEY` | Solver APIキー |
| `REFLECTION_VERIFIER_PROVIDER` | Verifierプロバイダー |
| `REFLECTION_VERIFIER_MODEL` | Verifierモデル |
| `REFLECTION_VERIFIER_API_KEY` | Verifier APIキー |
| `REFLECTION_INTEGRATOR_PROVIDER` | Integratorプロバイダー |
| `REFLECTION_INTEGRATOR_MODEL` | Integratorモデル |
| `REFLECTION_INTEGRATOR_API_KEY` | Integrator APIキー |
| `REFLECTION_REFLECTOR_PROVIDER` | Reflectorプロバイダー |
| `REFLECTION_REFLECTOR_MODEL` | Reflectorモデル |
| `REFLECTION_REFLECTOR_API_KEY` | Reflector APIキー |

### 共通パラメータ

| 環境変数 | 説明 |
|---------|------|
| `REFLECTION_TEMPERATURE` | 温度 (または LLM_TEMPERATURE) |
| `REFLECTION_TIMEOUT` | タイムアウト秒 (または LLM_TIMEOUT_SEC) |
| `REFLECTION_DEVUI_PORT` | DevUIポート (または DEVUI_PORT) ※現在は非対応 |

## ファイル構造（File Structure）

```
scripts/
├── main.py                 # エントリーポイント
├── requirements.txt        # 依存関係
└── workflow/
    ├── engine.py          # 軽量ワークフローエンジン
    ├── providers.py       # プロバイダーアダプタ
    ├── prompts.py         # プロンプトローダ
    ├── __init__.py
    ├── config.py          # エージェント設定
    ├── settings.py        # 設定管理
    ├── types.py           # 型定義
    ├── raw.py             # RAWデータ処理
    ├── anthropic_utils.py # Anthropic用ユーティリティ
    ├── decomposer.py      # 分解
    ├── solver.py          # 解決
    ├── verifier.py        # 検証
    ├── integrator.py      # 統合
    └── reflector.py       # 反省

assets/
└── prompts/
    ├── decomposer.txt
    ├── solver.txt
    ├── verifier.txt
    ├── integrator.txt
    └── reflector.txt

config.example             # 設定ファイルテンプレート
```

## プロバイダー別モデル選択ガイド

### Gemini（Decomposer/Solver推奨）

| モデル | 特徴 | 用途 |
|--------|------|------|
| `gemini-3.5-flash` | 最高性能、創造性高い | 高品質な分解・解決 |
| `gemini-2.0-flash` | 高速、コスト効率良 | 迅速な分解・解決 |
| `gemini-1.5-pro` | 長文対応、安定 | 長いコンテンツ |

### Claude（Verifier推奨）

| モデル | 特徴 | 用途 |
|--------|------|------|
| `claude-opus-4-8` | 最高分析力 | 詳細な検証 |
| `claude-3-5-sonnet-latest` | バランス良好 | 一般的な検証 |
| `claude-3-5-haiku-latest` | 高速、低コスト | 簡易な検証 |

### OpenAI（Integrator/Reflector推奨）

| モデル | 特徴 | 用途 |
|--------|------|------|
| `gpt-5.5` | 最高品質 | 最終統合・反省 |
| `gpt-4o` | 高性能、安定 | 一般的な統合・反省 |
| `gpt-4o-mini` | 高速、低コスト | 簡易な統合・反省 |

## エラー時の対処法

### APIキーが設定されていない

```
エラー: Decomposer のAPIキーが見つかりません（provider=gemini）。
```

**対処法:**
```bash
# .env ファイルを確認
cat .env

# または環境変数を直接設定
export GEMINI_API_KEY=your_key_here
```

### タイムアウトエラー

```
Error: Request timed out
```

**対処法:**
```bash
# タイムアウトを延長（デフォルト120秒）
python main.py --timeout 300 "長い処理が必要なプロンプト"
```

### モデルが見つからない

```
Error: Model 'xxx' not found
```

**対処法:**
1. モデルIDが正しいか確認（上記モデル選択ガイド参照）
2. `--show-config` で現在の設定を確認
3. プロバイダーのAPIダッシュボードでモデルのアクセス権限を確認

## 変更履歴

| バージョン | 日付 | 変更内容 |
|-------------|------|---------|
| 1.1.0 | 2026-01 | 5段階プロセス（分解/解決/検証/統合/反省）に対応 |
| 1.0.0 | 2026-01 | 初期リリース。3段階ワークフロー |

## 参考: 設計思想

### なぜ5段階にするのか？

1. **分解による構造化**: 複雑な課題を要素化し、抜け漏れを防ぐ。
2. **解決と検証の分離**: 解決案と検証を分け、論理的な飛躍や矛盾を検出しやすくする。
3. **統合と反省の分離**: 統合で一貫性を確保し、反省で死角と確信度を明示する。

### トレードオフ

| メリット | デメリット |
|---------|----------|
| 高品質な出力 | 処理時間が長い（5回のAPI呼び出し） |
| 多角的な視点 | コストが高い（複数APIを使用） |
| 自動的な品質改善 | 複数のAPIキーが必要 |
