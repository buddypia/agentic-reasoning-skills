<h1 align="center">🧠 agentic-reasoning-skills</h1>

<p align="center">
  <strong>認知思考パターンで複数のLLMをオーケストレーション</strong>
</p>

<p align="center">
  <a href="#-クイックスタート">クイックスタート</a> •
  <a href="#-パターン">パターン</a> •
  <a href="#-インストール">インストール</a> •
  <a href="#-使い方">使い方</a> •
  <a href="#-設定">設定</a> •
  <a href="./README.md">English</a> •
  <a href="./README_ko.md">한국어</a> •
  <a href="./README_zh.md">中文</a>
</p>

<p align="center">
  <a href="https://github.com/buddypia/agentic-reasoning-skills/blob/main/LICENSE"><img src="https://img.shields.io/badge/license-MIT-blue.svg" alt="License: MIT"></a>
  <a href="https://www.python.org/downloads/"><img src="https://img.shields.io/badge/python-3.13%2B-blue.svg" alt="Python 3.13+"></a>
  <a href="https://github.com/buddypia/agentic-reasoning-skills/stargazers"><img src="https://img.shields.io/github/stars/buddypia/agentic-reasoning-skills.svg?style=social" alt="GitHub Stars"></a>
</p>

---

## agentic-reasoning-skills とは？

**agentic-reasoning-skills** は、複数のLLM（Gemini、Claude、OpenAI）を認知思考パターンに基づいてオーケストレーションする軽量Pythonフレームワークです。重いエージェントフレームワークへの依存は一切ありません。

単一のLLMに頼るのではなく、異なるモデルの強みを活かし、構造化された思考ワークフローの中で専門的な役割を割り当てます：

| パターン | ステージ数 | 最適な用途 |
|---------|:---------:|----------|
| 🪞 **リフレクション** | 3 | コンテンツ生成、品質向上 |
| ⚔️ **ディベート** | 3 | 意思決定、リスク分析 |
| 🧠 **メタ認知** | 5 | 複雑な問題解決、設計 |

### なぜ agentic-reasoning-skills？

- 🪶 **軽量** — LangChainもCrewAIも不要。純粋なPython + 公式SDKのみ。
- 🧠 **認知パターン** — 認知科学に基づく：リフレクション、弁証法的思考、メタ認知。
- 🔀 **マルチプロバイダー** — Gemini、Claude、OpenAIを1つのパイプラインに。各モデルの強みを活かす。
- ⚙️ **柔軟な設定** — CLI引数 > 環境変数 > 設定ファイル > デフォルト値。自由に選択。
- 📊 **構造化出力** — 全ステージがPydantic v2スキーマで検証済みJSONを返却。

---

## 🚀 クイックスタート

```bash
# クローン
git clone https://github.com/buddypia/agentic-reasoning-skills.git
cd agentic-reasoning-skills

# APIキー設定
export GEMINI_API_KEY="your-key"
export ANTHROPIC_API_KEY="your-key"
export OPENAI_API_KEY="your-key"

# リフレクションパターン実行
cd skills/reflection
pip install -r scripts/requirements.txt
python scripts/main.py "マイクロサービスvsモノリスについて技術ブログ記事を書いてください"

# ディベートパターン実行
cd ../debate
pip install -r scripts/requirements.txt
python scripts/main.py "カスタマーサポートにAIエージェントを導入すべきか？"

# メタ認知パターン実行
cd ../meta-cognition
pip install -r scripts/requirements.txt
python scripts/main.py "ECプラットフォーム向けのスケーラブルなイベント駆動アーキテクチャを設計してください"
```

---

## 🧩 パターン

### 🪞 リフレクション（Generator → Critic → Refiner）

人間の執筆プロセスをモデル化：初稿作成、レビュー、推敲。

```
┌──────────────┐     ┌──────────────┐     ┌──────────────┐
│  Generator   │────▶│    Critic     │────▶│   Refiner    │
│  (Gemini)    │     │   (Claude)    │     │  (OpenAI)    │
│              │     │              │     │              │
│ 創造的に     │     │ 分析して     │     │ 修正を適用   │
│ 初稿作成     │     │ 問題点を指摘  │     │ して仕上げ   │
└──────────────┘     └──────────────┘     └──────────────┘
```

**最適な用途**: 技術ブログ、ホワイトペーパー、比較レポート、ドキュメント

```bash
python scripts/main.py "WebSocketセキュリティに関する包括的なガイドを作成してください"
python scripts/main.py --verbose "プロンプト"     # 全3ステージ表示
python scripts/main.py --json "プロンプト"        # JSON出力
python scripts/main.py --raw "プロンプト"         # LLM生データ表示
```

### ⚔️ ディベート（Proponent → Opponent → Moderator）

弁証法的思考をモデル化：テーゼ、アンチテーゼ、ジンテーゼ。

```
┌──────────────┐     ┌──────────────┐     ┌──────────────┐
│  Proponent   │────▶│   Opponent   │────▶│  Moderator   │
│  (Gemini)    │     │   (Claude)   │     │  (OpenAI)    │
│              │     │              │     │              │
│ 賛成の立場で │     │ 反対の立場で │     │ 客観的に判定 │
│ 根拠を提示   │     │ リスクを指摘 │     │ して推奨     │
└──────────────┘     └──────────────┘     └──────────────┘
```

**最適な用途**: 事業判断、技術選定、政策評価、リスク分析

```bash
python scripts/main.py "RESTからGraphQLに移行すべきか？"
python scripts/main.py --random-providers "トピック"   # ランダム役割割当
python scripts/main.py --shuffle-providers "トピック"  # シャッフル（重複なし）
```

### 🧠 メタ認知（Decompose → Solve → Verify → Integrate → Reflect）

再帰的メタ認知思考をモデル化：最も徹底的な分析パイプライン。

```
┌────────────┐   ┌────────────┐   ┌────────────┐   ┌────────────┐   ┌────────────┐
│ Decomposer │──▶│   Solver   │──▶│  Verifier  │──▶│ Integrator │──▶│ Reflector  │
│  (Gemini)  │   │  (Gemini)  │   │  (Claude)  │   │  (OpenAI)  │   │  (OpenAI)  │
│            │   │            │   │            │   │            │   │            │
│ 課題を     │   │ 各サブ     │   │ 論理検証   │   │ 全体を     │   │ 反省と     │
│ 要素分解   │   │ タスク解決 │   │ して修正   │   │ 統合       │   │ 信頼度評価 │
└────────────┘   └────────────┘   └────────────┘   └────────────┘   └────────────┘
```

**最適な用途**: アーキテクチャ設計、戦略分析、包括的リサーチ、複雑な計画策定

```bash
python scripts/main.py "マルチテナントSaaSアーキテクチャを設計してください"
python scripts/main.py --verbose "プロンプト"              # 全5ステージ表示
python scripts/main.py --output-schema flat "プロンプト"   # フラットJSONスキーマ
python scripts/main.py --timeout 300 "複雑なタスク"         # タイムアウト延長
```

---

## 📦 インストール

### 要件

- Python 3.13+
- 最低1つのプロバイダーのAPIキー（3つ全て推奨）

### パターン別インストール

```bash
# リフレクション
cd skills/reflection && pip install -r scripts/requirements.txt

# ディベート
cd skills/debate && pip install -r scripts/requirements.txt

# メタ認知
cd skills/meta-cognition && pip install -r scripts/requirements.txt
```

### 依存関係

| パッケージ | バージョン | 用途 |
|-----------|-----------|------|
| `pydantic` | ≥2.12.5 | 型検証 & JSONスキーマ |
| `python-dotenv` | ≥1.2.1 | 環境ファイル読み込み |
| `pyyaml` | ≥6.0.3 | YAML設定サポート |
| `openai` | ≥2.15.0 | OpenAI API |
| `anthropic` | ≥0.76.0 | Claude API |
| `google-genai` | ≥1.60.0 | Gemini API |

---

## ⚙️ 設定

### APIキー

```bash
# 方法1: 環境変数
export GEMINI_API_KEY="your-gemini-key"
export ANTHROPIC_API_KEY="your-anthropic-key"
export OPENAI_API_KEY="your-openai-key"

# 方法2: .envファイル
cp env.example .env
# .envを編集

# 方法3: 設定ファイル
cp config.example config.yaml
# config.yamlを編集
```

### 設定の優先順位

```
CLI引数  →  環境変数  →  設定ファイル  →  デフォルト値
（最高）                                  （最低）
```

### カスタムモデル

```bash
# リフレクション
python scripts/main.py "プロンプト" \
  --generator-model gemini-2.0-flash \
  --critic-model claude-sonnet-4-20250514 \
  --refiner-model gpt-4o

# ディベート
python scripts/main.py "プロンプト" \
  --proponent-model gemini-2.0-flash \
  --opponent-model claude-sonnet-4-20250514 \
  --moderator-model gpt-4o

# メタ認知
python scripts/main.py "プロンプト" \
  --decomposer-model gemini-2.0-flash \
  --solver-model gemini-2.0-flash \
  --verifier-model claude-sonnet-4-20250514 \
  --integrator-model gpt-4o \
  --reflector-model gpt-4o
```

### ロール固有の環境変数

```bash
# パターン: REFLECTION_<ROLE>_<SETTING>
REFLECTION_GENERATOR_PROVIDER=gemini
REFLECTION_GENERATOR_MODEL=gemini-2.0-flash
REFLECTION_GENERATOR_API_KEY=your-key
REFLECTION_GENERATOR_TEMPERATURE=0.7
REFLECTION_GENERATOR_TIMEOUT=120
```

---

## 📊 出力オプション

| フラグ | 説明 |
|-------|------|
| `--verbose` | 全ステージの出力を表示 |
| `--json` | JSON形式で出力 |
| `--raw` | LLMの生リクエスト/レスポンスを表示 |
| `--raw-output <path>` | 生データをJSONファイルに保存 |
| `--output-schema nested\|flat` | JSONスキーマ構造（メタ認知のみ） |

---

## 🏗️ アーキテクチャ

### 軽量ワークフローエンジン

コアエンジンはフレームワーク依存ゼロの約200行のPython：

```python
# Executor（ステージ）を定義
class MyExecutor(Executor):
    @handler
    async def process(self, payload: dict, ctx: Context):
        result = await call_llm(payload)
        ctx.set_shared_state("my_result", result)
        ctx.send_message(result)

# ワークフローを構築
workflow = (
    WorkflowBuilder()
    .set_start_executor(stage1)
    .add_edge(stage1, stage2)
    .add_edge(stage2, stage3)
    .build()
)

# 実行
result = await workflow.run({"prompt": "入力テキスト"})
```

### プロバイダー抽象化

全LLMプロバイダーが統一インターフェースを共有：

```python
# 設定に基づく自動プロバイダー選択
response = await providers.call(
    provider="gemini",          # or "anthropic", "openai"
    model="gemini-2.0-flash",
    system_prompt="あなたは...",
    user_prompt="分析して...",
    response_schema=MySchema,   # Pydanticモデル → JSONスキーマ
)
```

### 構造化出力

全ステージがJSONスキーマを使用して信頼性の高いデータ抽出を実現：

```python
class CriticOutput(BaseModel):
    strengths: list[str]       # 強み
    weaknesses: list[str]      # 弱み
    suggestions: list[str]     # 改善提案
    score: float = Field(ge=0, le=10)        # スコア
    confidence: float = Field(ge=0, le=1)    # 確信度
```

---

## 🤝 コントリビューション

コントリビューションを歓迎します！以下の方法でご参加いただけます：

- 🐛 **バグ報告** — 問題を発見されたら、GitHub Issueを作成してください。
- 💡 **新パターン** — 新しい思考パターンのアイデアがあれば、ぜひお聞かせください。
- 🔌 **新プロバイダー** — Mistral、Cohere、ローカルモデルへの対応追加。
- 📖 **ドキュメント** — ドキュメント改善、例の追加、タイポ修正。
- 🧪 **テスト** — テストカバレッジの追加。

---

## 📄 ライセンス

MIT License — 詳細は [LICENSE](LICENSE) をご確認ください。

---

## 🌟 スター履歴

このプロジェクトが役に立ったら、ぜひスターをお願いします！ ⭐

---

<p align="center">
  🧠 <a href="https://github.com/buddypia">buddypia</a> が作りました
</p>
