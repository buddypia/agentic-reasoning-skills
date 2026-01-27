# ⚔️ Debate Pattern

**Proponent → Opponent → Moderator** — A 3-role dialectical analysis pipeline.

```
┌──────────────┐     ┌──────────────┐     ┌──────────────┐
│  Proponent   │────▶│   Opponent   │────▶│  Moderator   │
│  (Gemini)    │     │   (Claude)   │     │  (OpenAI)    │
│              │     │              │     │              │
│ Argue FOR    │     │ Argue AGAINST│     │ Judge &      │
│ with evidence│     │ find risks   │     │ recommend    │
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
python scripts/main.py "Should we migrate from REST to GraphQL?"
```

## Options

```bash
python scripts/main.py --verbose "prompt"           # Show all 3 roles
python scripts/main.py --json "prompt"              # JSON output
python scripts/main.py --random-providers "prompt"  # Random role assignment
python scripts/main.py --shuffle-providers "prompt" # Shuffle (no repeats)

# Custom models
python scripts/main.py "prompt" \
  --proponent-model gemini-2.0-flash \
  --opponent-model claude-sonnet-4-20250514 \
  --moderator-model gpt-4o
```

## Best For

✅ Business decisions, technology selection, policy evaluation, risk analysis, ethical judgment
❌ Fact-checking, simple summaries, creative generation (use Reflection instead)

## Roles

| Role | Purpose | Default Provider | Output |
|------|---------|-----------------|--------|
| **Proponent** | Argue in favor | Gemini | `position`, `arguments`, `evidence`, `benefits` |
| **Opponent** | Argue against | Claude | `counter_arguments`, `risks`, `weaknesses`, `alternatives` |
| **Moderator** | Judge & recommend | OpenAI | `proponent_score`, `opponent_score`, `verdict`, `recommendation` |

## Provider Strategies

| Flag | Behavior |
|------|----------|
| `--random-providers` | Each role gets a random provider (may repeat) |
| `--shuffle-providers` | 3 providers shuffled across 3 roles (no repeats) |

---

📖 Full documentation: [Main README](../../README.md) | [日本語](../../README_ja.md) | [한국어](../../README_ko.md)
