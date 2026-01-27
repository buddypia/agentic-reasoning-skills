<h1 align="center">🧠 agentic-reasoning-skills</h1>

<p align="center">
  <strong>Orchestrate multiple LLMs using cognitive thinking patterns</strong>
</p>

<p align="center">
  <a href="#-quick-start">Quick Start</a> •
  <a href="#-patterns">Patterns</a> •
  <a href="#-installation">Installation</a> •
  <a href="#-usage">Usage</a> •
  <a href="#-configuration">Configuration</a> •
  <a href="./README_ja.md">日本語</a> •
  <a href="./README_ko.md">한국어</a> •
  <a href="./README_zh.md">中文</a>
</p>

<p align="center">
  <a href="https://github.com/buddypia/agentic-reasoning-skills/blob/main/LICENSE"><img src="https://img.shields.io/badge/license-MIT-blue.svg" alt="License: MIT"></a>
  <a href="https://www.python.org/downloads/"><img src="https://img.shields.io/badge/python-3.13%2B-blue.svg" alt="Python 3.13+"></a>
  <a href="https://github.com/buddypia/agentic-reasoning-skills/stargazers"><img src="https://img.shields.io/github/stars/buddypia/agentic-reasoning-skills.svg?style=social" alt="GitHub Stars"></a>
</p>

---

## What is agentic-reasoning-skills?

**agentic-reasoning-skills** is a lightweight Python framework that orchestrates multiple LLMs (Gemini, Claude, OpenAI) through cognitive thinking patterns — without any heavy agent framework dependencies.

Instead of relying on a single LLM, it leverages the unique strengths of different models by assigning them specialized roles in structured thinking workflows:

| Pattern | Stages | Best For |
|---------|:------:|----------|
| 🪞 **Reflection** | 3 | Content generation, quality improvement |
| ⚔️ **Debate** | 3 | Decision-making, risk analysis |
| 🧠 **Meta-Cognition** | 5 | Complex problem-solving, architecture design |

### Why agentic-reasoning-skills?

- 🪶 **Lightweight** — No LangChain, no CrewAI, no agent frameworks. Just pure Python + official SDKs.
- 🧠 **Cognitive Patterns** — Based on real cognitive science: reflection, dialectical thinking, and metacognition.
- 🔀 **Multi-Provider** — Gemini, Claude, and OpenAI in a single pipeline. Each model plays to its strengths.
- ⚙️ **Flexible Config** — CLI args > Environment variables > Config files > Defaults. You choose.
- 📊 **Structured Output** — Every stage returns validated JSON via Pydantic v2 schemas.

---

## 🚀 Quick Start

```bash
# Clone
git clone https://github.com/buddypia/agentic-reasoning-skills.git
cd agentic-reasoning-skills

# Set API keys
export GEMINI_API_KEY="your-key"
export ANTHROPIC_API_KEY="your-key"
export OPENAI_API_KEY="your-key"

# Run Reflection pattern
cd skills/reflection
pip install -r scripts/requirements.txt
python scripts/main.py "Write a technical blog post about microservices vs monoliths"

# Run Debate pattern
cd ../debate
pip install -r scripts/requirements.txt
python scripts/main.py "Should our startup adopt AI agents for customer support?"

# Run Meta-Cognition pattern
cd ../meta-cognition
pip install -r scripts/requirements.txt
python scripts/main.py "Design a scalable event-driven architecture for an e-commerce platform"
```

---

## 🧩 Patterns

### 🪞 Reflection (Generator → Critic → Refiner)

Models the human writing process: draft, review, and polish.

```
┌──────────────┐     ┌──────────────┐     ┌──────────────┐
│  Generator   │────▶│    Critic     │────▶│   Refiner    │
│  (Gemini)    │     │   (Claude)    │     │  (OpenAI)    │
│              │     │              │     │              │
│ Draft content│     │ Analyze &    │     │ Apply fixes  │
│ creatively   │     │ find issues  │     │ & polish     │
└──────────────┘     └──────────────┘     └──────────────┘
```

**Best for**: Technical blog posts, white papers, comparative reports, documentation

```bash
python scripts/main.py "Write a comprehensive guide to WebSocket security"
python scripts/main.py --verbose "Your prompt"     # Show all 3 stages
python scripts/main.py --json "Your prompt"        # JSON output
python scripts/main.py --raw "Your prompt"         # Raw LLM data
```

### ⚔️ Debate (Proponent → Opponent → Moderator)

Models dialectical thinking: thesis, antithesis, synthesis.

```
┌──────────────┐     ┌──────────────┐     ┌──────────────┐
│  Proponent   │────▶│   Opponent   │────▶│  Moderator   │
│  (Gemini)    │     │   (Claude)   │     │  (OpenAI)    │
│              │     │              │     │              │
│ Argue FOR    │     │ Argue AGAINST│     │ Judge &      │
│ with evidence│     │ find risks   │     │ recommend    │
└──────────────┘     └──────────────┘     └──────────────┘
```

**Best for**: Business decisions, technology selection, policy evaluation, risk analysis

```bash
python scripts/main.py "Should we migrate from REST to GraphQL?"
python scripts/main.py --random-providers "Topic"   # Random role assignment
python scripts/main.py --shuffle-providers "Topic"  # Shuffle without repeats
```

### 🧠 Meta-Cognition (Decompose → Solve → Verify → Integrate → Reflect)

Models recursive metacognitive thinking: the most thorough analysis pipeline.

```
┌────────────┐   ┌────────────┐   ┌────────────┐   ┌────────────┐   ┌────────────┐
│ Decomposer │──▶│   Solver   │──▶│  Verifier  │──▶│ Integrator │──▶│ Reflector  │
│  (Gemini)  │   │  (Gemini)  │   │  (Claude)  │   │  (OpenAI)  │   │  (OpenAI)  │
│            │   │            │   │            │   │            │   │            │
│ Break down │   │ Solve each │   │ Verify &   │   │ Integrate  │   │ Reflect &  │
│ into parts │   │ sub-task   │   │ correct    │   │ all parts  │   │ assess     │
└────────────┘   └────────────┘   └────────────┘   └────────────┘   └────────────┘
```

**Best for**: Architecture design, strategic analysis, comprehensive research, complex planning

```bash
python scripts/main.py "Design a multi-tenant SaaS architecture"
python scripts/main.py --verbose "Your prompt"              # Show all 5 stages
python scripts/main.py --output-schema flat "Your prompt"   # Flat JSON schema
python scripts/main.py --timeout 300 "Complex task"         # Extended timeout
```

---

## 📦 Installation

### Requirements

- Python 3.13+
- API keys for at least one provider (all three recommended)

### Per-Pattern Install

```bash
# Reflection
cd skills/reflection && pip install -r scripts/requirements.txt

# Debate
cd skills/debate && pip install -r scripts/requirements.txt

# Meta-Cognition
cd skills/meta-cognition && pip install -r scripts/requirements.txt
```

### Dependencies

| Package | Version | Purpose |
|---------|---------|---------|
| `pydantic` | ≥2.12.5 | Type validation & JSON schemas |
| `python-dotenv` | ≥1.2.1 | Environment file loading |
| `pyyaml` | ≥6.0.3 | YAML config support |
| `openai` | ≥2.15.0 | OpenAI API |
| `anthropic` | ≥0.76.0 | Claude API |
| `google-genai` | ≥1.60.0 | Gemini API |

---

## ⚙️ Configuration

### API Keys

```bash
# Option 1: Environment variables
export GEMINI_API_KEY="your-gemini-key"
export ANTHROPIC_API_KEY="your-anthropic-key"
export OPENAI_API_KEY="your-openai-key"

# Option 2: .env file
cp env.example .env
# Edit .env with your keys

# Option 3: Config file
cp config.example config.yaml
# Edit config.yaml
```

### Configuration Priority

```
CLI Arguments  →  Environment Variables  →  Config File  →  Defaults
(highest)                                                   (lowest)
```

### Custom Models

```bash
# Reflection
python scripts/main.py "prompt" \
  --generator-model gemini-2.0-flash \
  --critic-model claude-sonnet-4-20250514 \
  --refiner-model gpt-4o

# Debate
python scripts/main.py "prompt" \
  --proponent-model gemini-2.0-flash \
  --opponent-model claude-sonnet-4-20250514 \
  --moderator-model gpt-4o

# Meta-Cognition
python scripts/main.py "prompt" \
  --decomposer-model gemini-2.0-flash \
  --solver-model gemini-2.0-flash \
  --verifier-model claude-sonnet-4-20250514 \
  --integrator-model gpt-4o \
  --reflector-model gpt-4o
```

### Role-Specific Environment Variables

```bash
# Pattern: REFLECTION_<ROLE>_<SETTING>
REFLECTION_GENERATOR_PROVIDER=gemini
REFLECTION_GENERATOR_MODEL=gemini-2.0-flash
REFLECTION_GENERATOR_API_KEY=your-key
REFLECTION_GENERATOR_TEMPERATURE=0.7
REFLECTION_GENERATOR_TIMEOUT=120
```

---

## 📊 Output Options

| Flag | Description |
|------|-------------|
| `--verbose` | Show output from all stages |
| `--json` | Output in JSON format |
| `--raw` | Show raw LLM request/response data |
| `--raw-output <path>` | Save raw data to JSON file |
| `--output-schema nested\|flat` | JSON schema structure (Meta-Cognition only) |

---

## 🏗️ Architecture

### Lightweight Workflow Engine

The core engine is ~200 lines of Python with zero framework dependencies:

```python
# Define an executor (stage)
class MyExecutor(Executor):
    @handler
    async def process(self, payload: dict, ctx: Context):
        result = await call_llm(payload)
        ctx.set_shared_state("my_result", result)
        ctx.send_message(result)

# Build a workflow
workflow = (
    WorkflowBuilder()
    .set_start_executor(stage1)
    .add_edge(stage1, stage2)
    .add_edge(stage2, stage3)
    .build()
)

# Run
result = await workflow.run({"prompt": "Your input"})
```

### Provider Abstraction

All LLM providers share a unified interface:

```python
# Automatic provider selection based on config
response = await providers.call(
    provider="gemini",          # or "anthropic", "openai"
    model="gemini-2.0-flash",
    system_prompt="You are...",
    user_prompt="Analyze...",
    response_schema=MySchema,   # Pydantic model → JSON Schema
)
```

### Structured Output

Every stage uses JSON Schema for reliable data extraction:

```python
class CriticOutput(BaseModel):
    strengths: list[str]
    weaknesses: list[str]
    suggestions: list[str]
    score: float = Field(ge=0, le=10)
    confidence: float = Field(ge=0, le=1)
```

---

## 🤝 Contributing

We welcome contributions! Here are some ways you can help:

- 🐛 **Bug Reports** — Found an issue? Open a GitHub issue.
- 💡 **New Patterns** — Have a new thinking pattern idea? We'd love to hear it.
- 🔌 **New Providers** — Add support for Mistral, Cohere, or local models.
- 📖 **Documentation** — Improve docs, add examples, fix typos.
- 🧪 **Tests** — Add test coverage.

### Development Setup

```bash
git clone https://github.com/buddypia/agentic-reasoning-skills.git
cd agentic-reasoning-skills
python -m venv .venv
source .venv/bin/activate
pip install -r skills/reflection/scripts/requirements.txt
```

---

## 📄 License

MIT License — see [LICENSE](LICENSE) for details.

---

## 🌟 Star History

If you find this project useful, please consider giving it a star! ⭐

---

<p align="center">
  Made with 🧠 by <a href="https://github.com/buddypia">buddypia</a>
</p>
