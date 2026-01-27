# 🪞 Reflection Pattern

**Generator → Critic → Refiner** — A 3-stage iterative content improvement pipeline.

```
┌──────────────┐     ┌──────────────┐     ┌──────────────┐
│  Generator   │────▶│    Critic     │────▶│   Refiner    │
│  (Gemini)    │     │   (Claude)    │     │  (OpenAI)    │
│              │     │              │     │              │
│ Draft content│     │ Analyze &    │     │ Apply fixes  │
│ creatively   │     │ find issues  │     │ & polish     │
└──────────────┘     └──────────────┘     └──────────────┘
```

## Quick Start

```bash
# Set API keys
export GEMINI_API_KEY="your-key"
export ANTHROPIC_API_KEY="your-key"
export OPENAI_API_KEY="your-key"

# Install & Run
pip install -r scripts/requirements.txt
python scripts/main.py "Write a technical blog post about microservices vs monoliths"
```

## Options

```bash
python scripts/main.py --verbose "prompt"    # Show all 3 stages
python scripts/main.py --json "prompt"       # JSON output
python scripts/main.py --raw "prompt"        # Raw LLM data

# Custom models
python scripts/main.py "prompt" \
  --generator-model gemini-2.0-flash \
  --critic-model claude-sonnet-4-20250514 \
  --refiner-model gpt-4o
```

## Best For

✅ Technical blog posts, white papers, comparative reports, documentation
❌ Simple Q&A, real-time responses, web search tasks

## Stages

| Stage | Role | Default Provider | Output |
|-------|------|-----------------|--------|
| **Generator** | Creative draft | Gemini | `draft`, `key_points`, `confidence` |
| **Critic** | Analysis & feedback | Claude | `strengths`, `weaknesses`, `suggestions`, `score` |
| **Refiner** | Polish & finalize | OpenAI | `final_content`, `improvements_made`, `quality_score` |

---

📖 Full documentation: [Main README](../../README.md) | [日本語](../../README_ja.md) | [한국어](../../README_ko.md)
