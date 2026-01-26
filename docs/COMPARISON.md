# Pattern Comparison Guide

## When to Use Which Pattern?

```
                    Simple                          Complex
                    Content ───────────────────────── Problem
                      │                                │
                      ▼                                ▼
                 🪞 Reflection                   🧠 Meta-Cognition
                 (3-Stage)                       (5-Stage)
                      │
                      │  Decision?
                      ▼
                 ⚔️ Debate
                 (3-Role)
```

## Comparison Matrix

| Aspect | 🪞 Reflection | ⚔️ Debate | 🧠 Meta-Cognition |
|--------|:------------:|:---------:|:-----------------:|
| **Stages** | 3 | 3 | 5 |
| **API Calls** | 3 | 3 | 5 |
| **Cost** | Medium | Medium | High |
| **Latency** | ~30-60s | ~30-60s | ~60-120s |
| **Complexity** | Low | Medium | High |
| **Output Quality** | High | High | Highest |

## Best Use Cases

### 🪞 Reflection
| ✅ Good For | ❌ Not For |
|------------|-----------|
| Technical blog posts | Simple Q&A |
| White papers | Real-time responses |
| Documentation | Tasks needing web search |
| Comparative reports | Quick one-liners |
| Marketing copy | |

### ⚔️ Debate
| ✅ Good For | ❌ Not For |
|------------|-----------|
| Business decisions | Fact-checking |
| Technology selection | Simple summaries |
| Policy evaluation | Creative content |
| Risk analysis | Urgent decisions |
| Ethical judgment | |
| Investment decisions | |

### 🧠 Meta-Cognition
| ✅ Good For | ❌ Not For |
|------------|-----------|
| Architecture design | Simple Q&A |
| Strategic planning | Real-time responses |
| Comprehensive research | Tasks needing web search |
| Complex problem-solving | Cost-sensitive tasks |
| Multi-faceted analysis | |

## Cognitive Science Background

### Reflection — Iterative Improvement
Based on the **writing process model** (Flower & Hayes, 1981): humans improve text through cycles of drafting, reviewing, and revising. Each cycle catches different issues.

### Debate — Dialectical Thinking
Based on **Hegelian dialectics**: thesis (Proponent), antithesis (Opponent), and synthesis (Moderator). Opposing viewpoints reveal blind spots that single-perspective analysis misses.

### Meta-Cognition — Thinking About Thinking
Based on **Flavell's metacognition theory** (1979): monitoring and regulating one's own cognitive processes. The 5-stage pipeline mirrors how expert problem-solvers approach complex tasks:
1. **Decompose** — Break the problem down (task analysis)
2. **Solve** — Apply strategies to each part
3. **Verify** — Monitor for errors (metacognitive monitoring)
4. **Integrate** — Combine partial solutions
5. **Reflect** — Evaluate the overall process (metacognitive evaluation)

## Cost Estimation

Assuming average prompt/completion sizes:

| Pattern | Input Tokens | Output Tokens | Est. Cost (USD) |
|---------|:----------:|:------------:|:---------------:|
| Reflection | ~6K | ~4K | ~$0.15-0.30 |
| Debate | ~6K | ~4K | ~$0.15-0.30 |
| Meta-Cognition | ~12K | ~8K | ~$0.30-0.60 |

*Costs vary by model selection. Using smaller models (e.g., gemini-2.0-flash, gpt-4o-mini) reduces costs significantly.*
