<h1 align="center">🧠 agentic-reasoning-skills</h1>

<p align="center">
  <strong>通过认知思维模式编排多个大语言模型</strong>
</p>

<p align="center">
  <a href="#-快速开始">快速开始</a> •
  <a href="#-思维模式">思维模式</a> •
  <a href="#-安装">安装</a> •
  <a href="#-使用方法">使用方法</a> •
  <a href="#-配置">配置</a> •
  <a href="./README.md">English</a> •
  <a href="./README_ja.md">日本語</a> •
  <a href="./README_ko.md">한국어</a>
</p>

<p align="center">
  <a href="https://github.com/buddypia/agentic-reasoning-skills/blob/main/LICENSE"><img src="https://img.shields.io/badge/license-MIT-blue.svg" alt="License: MIT"></a>
  <a href="https://www.python.org/downloads/"><img src="https://img.shields.io/badge/python-3.13%2B-blue.svg" alt="Python 3.13+"></a>
  <a href="https://github.com/buddypia/agentic-reasoning-skills/stargazers"><img src="https://img.shields.io/github/stars/buddypia/agentic-reasoning-skills.svg?style=social" alt="GitHub Stars"></a>
</p>

---

## agentic-reasoning-skills 是什么？

**agentic-reasoning-skills** 是一个轻量级 Python 框架，基于认知思维模式编排多个大语言模型（Gemini、Claude、OpenAI），完全不依赖任何重量级 Agent 框架。

它不是依赖单一 LLM，而是充分发挥不同模型的优势，在结构化的思维工作流中为每个模型分配专门角色：

| 模式 | 阶段数 | 最佳用途 |
|------|:-----:|---------|
| 🪞 **反思** | 3 | 内容生成、质量提升 |
| ⚔️ **辩论** | 3 | 决策分析、风险评估 |
| 🧠 **元认知** | 5 | 复杂问题求解、架构设计 |

### 为什么选择 agentic-reasoning-skills？

- 🪶 **轻量级** — 不需要 LangChain，不需要 CrewAI。纯 Python + 官方 SDK。
- 🧠 **认知模式** — 基于认知科学：反思、辩证思维、元认知。
- 🔀 **多供应商** — Gemini、Claude、OpenAI 集成在一个管道中，各展所长。
- ⚙️ **灵活配置** — CLI 参数 > 环境变量 > 配置文件 > 默认值，自由选择。
- 📊 **结构化输出** — 每个阶段通过 Pydantic v2 Schema 返回经过验证的 JSON。

---

## 🚀 快速开始

```bash
# 克隆
git clone https://github.com/buddypia/agentic-reasoning-skills.git
cd agentic-reasoning-skills

# 设置 API 密钥
export GEMINI_API_KEY="your-key"
export ANTHROPIC_API_KEY="your-key"
export OPENAI_API_KEY="your-key"

# 运行反思模式
cd reflection
pip install -r scripts/requirements.txt
python scripts/main.py "请写一篇关于微服务 vs 单体架构的技术博客"

# 运行辩论模式
cd ../debate
pip install -r scripts/requirements.txt
python scripts/main.py "我们是否应该在客户支持中引入 AI 智能体？"

# 运行元认知模式
cd ../meta-cognition
pip install -r scripts/requirements.txt
python scripts/main.py "请为电商平台设计一个可扩展的事件驱动架构"
```

---

## 🧩 思维模式

### 🪞 反思（Generator → Critic → Refiner）

模拟人类的写作过程：起草、审查、打磨。

```
┌──────────────┐     ┌──────────────┐     ┌──────────────┐
│  Generator   │────▶│    Critic     │────▶│   Refiner    │
│  (Gemini)    │     │   (Claude)    │     │  (OpenAI)    │
│              │     │              │     │              │
│ 创造性地     │     │ 分析并       │     │ 应用修改     │
│ 起草内容     │     │ 指出问题     │     │ 完成打磨     │
└──────────────┘     └──────────────┘     └──────────────┘
```

**最佳用途**：技术博客、白皮书、对比报告、文档

```bash
python scripts/main.py "请撰写一份 WebSocket 安全性综合指南"
python scripts/main.py --verbose "提示词"     # 显示全部 3 个阶段
python scripts/main.py --json "提示词"        # JSON 输出
python scripts/main.py --raw "提示词"         # 显示 LLM 原始数据
```

### ⚔️ 辩论（Proponent → Opponent → Moderator）

模拟辩证思维：正（论）、反（论）、合（论）。

```
┌──────────────┐     ┌──────────────┐     ┌──────────────┐
│  Proponent   │────▶│   Opponent   │────▶│  Moderator   │
│  (Gemini)    │     │   (Claude)   │     │  (OpenAI)    │
│              │     │              │     │              │
│ 以支持方立场 │     │ 以反对方立场 │     │ 客观裁决     │
│ 提出论据     │     │ 指出风险     │     │ 并给出建议   │
└──────────────┘     └──────────────┘     └──────────────┘
```

**最佳用途**：商业决策、技术选型、政策评估、风险分析

```bash
python scripts/main.py "我们是否应该从 REST 迁移到 GraphQL？"
python scripts/main.py --random-providers "主题"   # 随机分配角色
python scripts/main.py --shuffle-providers "主题"  # 洗牌分配（不重复）
```

### 🧠 元认知（Decompose → Solve → Verify → Integrate → Reflect）

模拟递归元认知思维：最彻底的分析流水线。

```
┌────────────┐   ┌────────────┐   ┌────────────┐   ┌────────────┐   ┌────────────┐
│ Decomposer │──▶│   Solver   │──▶│  Verifier  │──▶│ Integrator │──▶│ Reflector  │
│  (Gemini)  │   │  (Gemini)  │   │  (Claude)  │   │  (OpenAI)  │   │  (OpenAI)  │
│            │   │            │   │            │   │            │   │            │
│ 将任务     │   │ 逐个解决   │   │ 逻辑验证   │   │ 整合       │   │ 反思与     │
│ 拆解为要素 │   │ 子任务     │   │ 并修正     │   │ 全部结果   │   │ 置信度评估 │
└────────────┘   └────────────┘   └────────────┘   └────────────┘   └────────────┘
```

**最佳用途**：架构设计、战略分析、综合研究、复杂规划

```bash
python scripts/main.py "请设计一个多租户 SaaS 架构"
python scripts/main.py --verbose "提示词"              # 显示全部 5 个阶段
python scripts/main.py --output-schema flat "提示词"   # 扁平化 JSON Schema
python scripts/main.py --timeout 300 "复杂任务"         # 延长超时时间
```

---

## 📦 安装

### 环境要求

- Python 3.13+
- 至少一个供应商的 API 密钥（推荐三个全部配置）

### 按模式安装

```bash
# 反思
cd reflection && pip install -r scripts/requirements.txt

# 辩论
cd debate && pip install -r scripts/requirements.txt

# 元认知
cd meta-cognition && pip install -r scripts/requirements.txt
```

### 依赖项

| 包 | 版本 | 用途 |
|----|------|------|
| `pydantic` | ≥2.12.5 | 类型验证 & JSON Schema |
| `python-dotenv` | ≥1.2.1 | 环境文件加载 |
| `pyyaml` | ≥6.0.3 | YAML 配置支持 |
| `openai` | ≥2.15.0 | OpenAI API |
| `anthropic` | ≥0.76.0 | Claude API |
| `google-genai` | ≥1.60.0 | Gemini API |

---

## ⚙️ 配置

### API 密钥

```bash
# 方式 1：环境变量
export GEMINI_API_KEY="your-gemini-key"
export ANTHROPIC_API_KEY="your-anthropic-key"
export OPENAI_API_KEY="your-openai-key"

# 方式 2：.env 文件
cp env.example .env
# 编辑 .env

# 方式 3：配置文件
cp config.example config.yaml
# 编辑 config.yaml
```

### 配置优先级

```
CLI 参数  →  环境变量  →  配置文件  →  默认值
（最高）                              （最低）
```

### 自定义模型

```bash
# 反思
python scripts/main.py "提示词" \
  --generator-model gemini-2.0-flash \
  --critic-model claude-sonnet-4-20250514 \
  --refiner-model gpt-4o

# 辩论
python scripts/main.py "提示词" \
  --proponent-model gemini-2.0-flash \
  --opponent-model claude-sonnet-4-20250514 \
  --moderator-model gpt-4o

# 元认知
python scripts/main.py "提示词" \
  --decomposer-model gemini-2.0-flash \
  --solver-model gemini-2.0-flash \
  --verifier-model claude-sonnet-4-20250514 \
  --integrator-model gpt-4o \
  --reflector-model gpt-4o
```

### 角色专属环境变量

```bash
# 格式：REFLECTION_<角色>_<设置项>
REFLECTION_GENERATOR_PROVIDER=gemini
REFLECTION_GENERATOR_MODEL=gemini-2.0-flash
REFLECTION_GENERATOR_API_KEY=your-key
REFLECTION_GENERATOR_TEMPERATURE=0.7
REFLECTION_GENERATOR_TIMEOUT=120
```

---

## 📊 输出选项

| 标志 | 说明 |
|------|------|
| `--verbose` | 显示所有阶段的输出 |
| `--json` | 以 JSON 格式输出 |
| `--raw` | 显示 LLM 原始请求/响应数据 |
| `--raw-output <path>` | 将原始数据保存为 JSON 文件 |
| `--output-schema nested\|flat` | JSON Schema 结构（仅元认知模式） |

---

## 🏗️ 架构

### 轻量级工作流引擎

核心引擎是约 200 行零框架依赖的纯 Python 代码：

```python
# 定义 Executor（阶段）
class MyExecutor(Executor):
    @handler
    async def process(self, payload: dict, ctx: Context):
        result = await call_llm(payload)
        ctx.set_shared_state("my_result", result)
        ctx.send_message(result)

# 构建工作流
workflow = (
    WorkflowBuilder()
    .set_start_executor(stage1)
    .add_edge(stage1, stage2)
    .add_edge(stage2, stage3)
    .build()
)

# 执行
result = await workflow.run({"prompt": "输入文本"})
```

### 供应商抽象

所有 LLM 供应商共享统一接口：

```python
# 基于配置自动选择供应商
response = await providers.call(
    provider="gemini",          # 或 "anthropic"、"openai"
    model="gemini-2.0-flash",
    system_prompt="你是...",
    user_prompt="请分析...",
    response_schema=MySchema,   # Pydantic 模型 → JSON Schema
)
```

### 结构化输出

每个阶段使用 JSON Schema 确保可靠的数据提取：

```python
class CriticOutput(BaseModel):
    strengths: list[str]       # 优势
    weaknesses: list[str]      # 不足
    suggestions: list[str]     # 改进建议
    score: float = Field(ge=0, le=10)        # 评分
    confidence: float = Field(ge=0, le=1)    # 置信度
```

---

## 🤝 参与贡献

欢迎各种形式的贡献！您可以通过以下方式参与：

- 🐛 **Bug 报告** — 发现问题？请创建 GitHub Issue。
- 💡 **新模式** — 有新的思维模式想法？我们很乐意听取。
- 🔌 **新供应商** — 添加 Mistral、Cohere 或本地模型的支持。
- 📖 **文档** — 改进文档、添加示例、修复错别字。
- 🧪 **测试** — 增加测试覆盖率。

---

## 📄 开源许可

MIT License — 详见 [LICENSE](LICENSE)。

---

## 🌟 Star 历史

如果您觉得这个项目有用，请给我们一个 Star！⭐

---

<p align="center">
  🧠 由 <a href="https://github.com/buddypia">buddypia</a> 开发
</p>
