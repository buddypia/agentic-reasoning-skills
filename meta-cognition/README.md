# 🧠 Meta-Cognition Pattern

**Decompose → Solve → Verify → Integrate → Reflect** — A 5-stage recursive metacognitive pipeline.

```
┌────────────┐   ┌────────────┐   ┌────────────┐   ┌────────────┐   ┌────────────┐
│ Decomposer │──▶│   Solver   │──▶│  Verifier  │──▶│ Integrator │──▶│ Reflector  │
│  (Gemini)  │   │  (Gemini)  │   │  (Claude)  │   │  (OpenAI)  │   │  (OpenAI)  │
│            │   │            │   │            │   │            │   │            │
│ Break down │   │ Solve each │   │ Verify &   │   │ Integrate  │   │ Reflect &  │
│ into parts │   │ sub-task   │   │ correct    │   │ all parts  │   │ assess     │
└────────────┘   └────────────┘   └────────────┘   └────────────┘   └────────────┘
```

## Quick Start

```bash
# Set API keys
export GEMINI_API_KEY="your-key"
export ANTHROPIC_API_KEY="your-key"
export OPENAI_API_KEY="your-key"

# Install & Run
pip install -r scripts/requirements.txt
python scripts/main.py "Design a multi-tenant SaaS architecture"
```

## Options

```bash
python scripts/main.py --verbose "prompt"              # Show all 5 stages
python scripts/main.py --json "prompt"                 # JSON output
python scripts/main.py --output-schema flat "prompt"   # Flat JSON schema
python scripts/main.py --output-schema nested "prompt" # Nested (default)
python scripts/main.py --timeout 300 "prompt"          # Extended timeout
python scripts/main.py --random-providers "prompt"     # Random assignment
python scripts/main.py --shuffle-providers "prompt"    # Cyclic shuffle (5 roles)

# Custom models
python scripts/main.py "prompt" \
  --decomposer-model gemini-2.0-flash \
  --solver-model gemini-2.0-flash \
  --verifier-model claude-sonnet-4-20250514 \
  --integrator-model gpt-4o \
  --reflector-model gpt-4o
```

## Best For

✅ Architecture design, strategic analysis, comprehensive research, complex planning
❌ Simple Q&A, real-time responses, web search tasks

## Stages

| Stage | Role | Default Provider | Output |
|-------|------|-----------------|--------|
| **Decomposer** | Break into sub-tasks | Gemini | `subtasks`, `assumptions`, `constraints`, `confidence` |
| **Solver** | Solve each sub-task | Gemini | `solutions`, `open_questions`, `risks`, `confidence` |
| **Verifier** | Verify & self-correct | Claude | `issues`, `corrections`, `self_corrections`, `confidence` |
| **Integrator** | Integrate all parts | OpenAI | `integrated_answer`, `applied_corrections`, `confidence` |
| **Reflector** | Assess & reflect | OpenAI | `final_response`, `confidence_score`, `uncertainties` |

## Output Schema

| Schema | Description |
|--------|-------------|
| `nested` (default) | Hierarchical — each stage result nested in the next |
| `flat` | All fields at top level — easier for parsing |

---

📖 Full documentation: [Main README](../README.md) | [日本語](../README_ja.md) | [한국어](../README_ko.md)
