# Multi-LLM Debate（マルチLLM討論パターン）

> ⚠️ **2026-05 更新**: バックエンドを**購読認証CLI**（Antigravity `agy` / Claude Code `claude` / Codex `codex`）に移行しました。**APIキーは不要**です（各CLIの購読認証を利用）。以下のAPIキー設定は旧バージョンの記述です。最新の利用方法は `SKILL.md` を参照してください。


このREADMEは**プロンプト設計**と**環境設定**のまとめです。実行方法は `SKILL.md` を参照してください。

## 対応状況（Status）

- Claude Code ネイティブ: ✅ 対応（推奨・APIキー不要）
- CLI (Python スクリプト): ✅ 対応（レガシー・APIキー必須）
- DevUI: ❌ 非対応

## 概要（Overview）

このスキルは、複数のLLMエージェントが異なる視点から議論し、最良の解を導き出す**Debate（討論）パターン**を提供します。
意思決定の質を高めるために、**前提・反証・リスク・代替案**を明示する「批判的思考」の型を重視します。

**エージェント構成:**
- **Proponent（賛成派）**: 支持・賛成の視点で分析
- **Opponent（反対派）**: 批判・反対の視点で分析
- **Moderator（中立派）**: 両者を客観的に評価し最終判断

### 実行モード

| モード | 説明 | APIキー | セットアップ |
|--------|------|---------|-------------|
| **Claude Code ネイティブ**（推奨） | Task ツールで3つのサブエージェントを起動 | 不要 | 不要 |
| CLI (Python) | 外部 LLM API を直接呼び出し | 必要 | venv + pip install |

## いつ使うべきか（When to Use）

### 効果的なケース

| シナリオ | 具体例 |
|---------|--------|
| 重要な意思決定 | 「新規事業に参入すべきか？」「M&Aを実行すべきか？」 |
| 技術選定 | 「マイクロサービス vs モノリス」「React vs Vue」 |
| ポリシー策定 | 「リモートワーク導入の是非」「AI利用ガイドライン」 |
| 投資判断 | 「この株に投資すべきか？」「設備投資のタイミング」 |
| リスク分析 | 「新製品リリースのリスク」「海外展開のリスク」 |
| 倫理的判断 | 「顔認証技術の導入」「データ収集の範囲」 |

### 使わない方が良いケース

- 事実確認・情報検索（討論の余地がない）
- 明確な正解がある問題
- クリエイティブな生成（Reflectionパターンの方が適切）
- 単純な要約・翻訳
- 緊急対応（討論している時間がない）

## ワークフロー（Workflow）

```
[ユーザーの討論テーマ]
      ↓
[Proponent（賛成派）] → position, arguments, evidence, benefits
      ↓
[Opponent（反対派）] → counter_arguments, risks, weaknesses, alternatives
      ↓
[Moderator（中立派）] → scores, verdict, recommendation
      ↓
[討論結果]
```

## 批判的思考の指針（Critical Thinking）

以下の観点を含むプロンプト設計を推奨します（業務意思決定の標準的な評価軸に沿った整理）。

- **前提/制約**: 何が事実で、何が仮定か
- **評価基準**: 成功指標・コスト・期限・リスク許容度
- **反証/反例**: 反対意見の最強の根拠
- **代替案**: 第三案・段階導入・限定適用など

## プロンプト設計（Prompts）

### 入力形式（推奨）

> **重要**: 討論トピックだけでなく、**コンテキスト情報**も一緒に入力すると、より質の高い討論結果が得られます。

```
[討論トピック]
質問または議題

[コンテキスト]
- 背景情報、制約条件、前提条件
- 目的・評価基準（KPI、期限、コスト）
- リスク許容度・コンプライアンス要件
- 関連するドメイン知識
- 検討すべき観点や優先事項
```

**入力例:**
```
AIエージェントを顧客サポートに導入すべきか？

[コンテキスト]
- B2B SaaS企業（従業員500名、顧客数2000社）
- 現在の平均応答時間: 4時間
- 月間問い合わせ件数: 約3000件
- 予算制約: 年間500万円以内
- 既存CRMはSalesforceを使用
- セキュリティ要件: SOC2準拠必須
```

### プロンプトのカスタマイズ

各ロールのシステムプロンプトは外部ファイルから読み込みます。

```
assets/prompts/
  proponent.txt
  opponent.txt
  moderator.txt
```

## 注意事項（Security & Privacy）

- 討論結果には入力内容に基づく分析が含まれます。機密情報が含まれる場合は共有・公開に注意してください。
- CLIモード使用時: `.env` や `config.yaml` に API キーを保存する場合は、公開リポジトリへコミットしないようにしてください。

---

## CLIモード（レガシー: APIキー必須）

以下は Python スクリプトによる従来の実行方法です。外部 LLM API (Gemini/Anthropic/OpenAI) を直接呼び出すため、各プロバイダーの API キーが必要です。

### デフォルトプロバイダー

- **Proponent（賛成派）**: Gemini (`gemini-3.5-flash`)
- **Opponent（反対派）**: Anthropic Claude (`claude-opus-4-8`)
- **Moderator（中立派）**: OpenAI (`gpt-5.5`)

### Python バージョン

```bash
cd <skill-dir>/scripts
python3.13 --version  # Python 3.13+ が必要
```

### venv + 依存関係のインストール

```bash
cd <skill-dir>/scripts
python3.13 -m venv .venv
source .venv/bin/activate  # Windows: .venv\Scripts\activate
pip install -r requirements.txt
```

### 環境変数（API キー）

```bash
cp env.example .env
# もしくは必要項目のみ手動で作成
cat > .env << 'EOT'
GEMINI_API_KEY=your_gemini_api_key
ANTHROPIC_API_KEY=your_anthropic_api_key
OPENAI_API_KEY=your_openai_api_key
EOT
```

### 設定ファイル（オプション）

モデルや温度などを固定したい場合は `config.yaml` / `config.json` を作成します。`config.example` を `config.yaml` にコピーして利用できます。

### 設定の優先順位（Configuration Priority）

高い順:
1. **CLI引数**（`--proponent-model`, `--opponent-provider`, etc.）
2. **環境変数**（`DEBATE_<ROLE>_<KEY>` または `<PROVIDER>_API_KEY`）
3. **設定ファイル**（`config.yaml` / `config.json`）
4. **デフォルト値**

### 互換性メモ（Structured Output）

- OpenAI: `response_format: json_schema` を利用します。構造化出力対応モデルを使用してください。
- Anthropic: `beta.messages.parse` による構造化出力を利用します。
- Gemini: `response_json_schema` を利用します。一部モデルは schema の順序に敏感なため内部で補正しています。

## リソース（Resources）

### scripts/

討論ワークフローを実行するPythonスクリプト（CLIモード用）:
- `main.py`: エントリーポイント
  - `requirements.txt`: 依存関係
  - `workflow/`: ワークフロー実装モジュール（軽量エンジン + プロバイダーアダプタ）

### assets/

- `assets/prompts/`: ロール別プロンプト（Claude Code ネイティブモード・CLIモード共通）

## 関連パターン（Related Patterns）

| パターン | 特徴 | 適用例 |
|---------|------|-------|
| **Debate（本スキル）** | 対立する視点から分析 → 中立評価 | 意思決定、リスク分析、技術選定 |
| **Reflection** | 生成 → 批評 → 改善の反復 | 文章生成、コード改善、クリエイティブ作業 |
| **Recursive Meta-Cognition** | 分解→解決→検証→統合→反省の5段階 | 複雑な問題解決、アーキテクチャ設計 |

## License

MIT License. 詳細は `LICENSE` を参照してください。
