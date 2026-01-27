# Contributing to agentic-reasoning-skills

Thank you for your interest in contributing to **agentic-reasoning-skills**! This document provides guidelines and instructions to help you contribute effectively.

## Table of Contents

- [Code of Conduct](#code-of-conduct)
- [How Can I Contribute?](#how-can-i-contribute)
- [Getting Started](#getting-started)
- [Development Workflow](#development-workflow)
- [Project Structure](#project-structure)
- [Coding Guidelines](#coding-guidelines)
- [Adding a New Reasoning Pattern](#adding-a-new-reasoning-pattern)
- [Commit Messages](#commit-messages)
- [Pull Request Process](#pull-request-process)
- [Reporting Bugs](#reporting-bugs)
- [Suggesting Features](#suggesting-features)
- [License](#license)

---

## Code of Conduct

By participating in this project, you agree to maintain a welcoming and respectful environment for everyone. Please be considerate, constructive, and professional in all interactions.

---

## How Can I Contribute?

There are many ways to contribute:

- **Bug Reports** — Found a bug? [Open an issue](https://github.com/buddypia/agentic-reasoning-skills/issues/new?template=bug_report.md).
- **Feature Requests** — Have an idea? [Suggest a feature](https://github.com/buddypia/agentic-reasoning-skills/issues/new?template=feature_request.md).
- **New Reasoning Patterns** — Design a new cognitive thinking pattern.
- **Provider Support** — Add support for additional LLM providers.
- **Documentation** — Improve or translate documentation.
- **Bug Fixes** — Pick up an existing issue and submit a fix.
- **Tests** — Add or improve test coverage.

---

## Getting Started

### Prerequisites

- **Python 3.13+**
- API keys for at least one LLM provider:
  - [Google Gemini](https://ai.google.dev/)
  - [Anthropic Claude](https://console.anthropic.com/)
  - [OpenAI](https://platform.openai.com/)

### Setup

1. **Fork and clone the repository:**

   ```bash
   git clone https://github.com/<your-username>/agentic-reasoning-skills.git
   cd agentic-reasoning-skills
   ```

2. **Create a virtual environment:**

   ```bash
   python -m venv .venv
   source .venv/bin/activate  # macOS/Linux
   # or
   .venv\Scripts\activate     # Windows
   ```

3. **Install dependencies for the skill you're working on:**

   ```bash
   pip install -r skills/reflection/scripts/requirements.txt
   # or
   pip install -r skills/debate/scripts/requirements.txt
   # or
   pip install -r skills/meta-cognition/scripts/requirements.txt
   ```

4. **Set up environment variables:**

   ```bash
   cp skills/reflection/env.example skills/reflection/.env
   # Edit .env with your API keys
   ```

5. **Verify your setup:**

   ```bash
   cd skills/reflection
   python scripts/main.py "Hello, test prompt"
   ```

---

## Development Workflow

1. **Create a feature branch** from `master`:

   ```bash
   git checkout -b feature/your-feature-name
   ```

2. **Make your changes** following the [coding guidelines](#coding-guidelines).

3. **Test your changes** by running the relevant skill:

   ```bash
   python scripts/main.py --verbose "Test prompt for your changes"
   ```

4. **Commit your changes** following the [commit message conventions](#commit-messages).

5. **Push and open a pull request** against `master`.

---

## Project Structure

```
agentic-reasoning-skills/
├── docs/                          # Project-wide documentation
│   └── COMPARISON.md              # Pattern comparison guide
├── skills/                        # Reasoning patterns
│   ├── reflection/                # 3-stage: Generator → Critic → Refiner
│   │   ├── assets/prompts/        # Prompt templates
│   │   ├── scripts/
│   │   │   ├── main.py            # CLI entry point
│   │   │   ├── requirements.txt   # Dependencies
│   │   │   ├── run.sh             # Shell wrapper
│   │   │   └── workflow/          # Core logic modules
│   │   ├── config.example         # YAML config template
│   │   ├── env.example            # Environment variable template
│   │   └── README.md              # Skill-specific docs
│   ├── debate/                    # 3-role: Proponent → Opponent → Moderator
│   │   └── (same structure)
│   └── meta-cognition/            # 5-stage recursive thinking
│       └── (same structure)
├── CONTRIBUTING.md
├── LICENSE
├── README.md
└── README_{ja,ko,zh}.md          # Translations
```

### Key Modules (in `scripts/workflow/`)

| Module | Purpose |
|--------|---------|
| `types.py` | Pydantic v2 models for input/output validation |
| `config.py` | Configuration loading and merging |
| `settings.py` | Settings management with priority resolution |
| `providers.py` | LLM provider adapters (Gemini, Claude, OpenAI) |
| `engine.py` | Minimal workflow engine (~200 lines) |
| `workflow.py` | Pipeline orchestration |
| `prompts.py` | System prompt construction |

---

## Coding Guidelines

### General Principles

- **Keep it lightweight.** This project avoids heavy frameworks. Do not introduce LangChain, CrewAI, or similar dependencies.
- **Use only official SDKs** (`google-genai`, `anthropic`, `openai`) for LLM provider integration.
- **Maintain the existing architecture.** Each skill follows the same directory structure and coding patterns.

### Python Style

- **Python 3.13+** features are welcome.
- Use **type hints** throughout (PEP 484).
- Use **async/await** for all LLM API calls.
- Use **Pydantic v2** for data validation and structured output schemas.
- Follow [PEP 8](https://peps.python.org/pep-0008/) conventions.
- Keep functions focused and reasonably sized.

### Configuration

- All configuration must follow the priority chain: **CLI args > Environment variables > Config files > Defaults**.
- New configuration options must be added to both `env.example` and `config.example`.

### Prompt Templates

- Store prompt templates as `.txt` files in `assets/prompts/`.
- Keep prompts clear, well-structured, and provider-agnostic.

---

## Adding a New Reasoning Pattern

To add a new cognitive reasoning pattern (e.g., `skills/socratic/`):

1. **Create the directory structure:**

   ```
   skills/your-pattern/
   ├── assets/prompts/        # One .txt per role
   ├── scripts/
   │   ├── main.py            # CLI entry point
   │   ├── requirements.txt
   │   ├── run.sh
   │   └── workflow/           # Core modules
   ├── config.example
   ├── env.example
   └── README.md
   ```

2. **Define roles and stages** — Each stage should have a clear cognitive role (e.g., Questioner, Responder, Synthesizer).

3. **Define Pydantic models** in `workflow/types.py` for structured I/O.

4. **Implement stage handlers** — One module per role in `workflow/`.

5. **Reuse shared modules** — `providers.py`, `engine.py`, `config.py`, and `settings.py` are designed to be reusable across patterns.

6. **Document the pattern** — Write a `README.md` explaining the cognitive basis, pipeline stages, and usage examples.

7. **Update the root `README.md`** — Add the new pattern to the patterns table.

---

## Commit Messages

This project follows [Conventional Commits](https://www.conventionalcommits.org/):

```
<type>(<scope>): <description>

[optional body]
[optional footer]
```

### Types

| Type | Description |
|------|-------------|
| `feat` | A new feature |
| `fix` | A bug fix |
| `docs` | Documentation changes |
| `refactor` | Code changes that neither fix a bug nor add a feature |
| `style` | Formatting, missing semicolons, etc. |
| `test` | Adding or updating tests |
| `chore` | Maintenance tasks, CI/CD, dependencies |

### Scope Examples

- `reflection`, `debate`, `meta-cognition` — Skill-specific changes
- `providers` — LLM provider changes
- `engine` — Workflow engine changes
- `config` — Configuration system changes
- `docs` — Documentation changes

### Examples

```
feat(debate): add confidence scoring to moderator output
fix(providers): handle rate limit errors for Gemini API
docs: add Korean translation for README
refactor(engine): simplify handler registration logic
```

---

## Pull Request Process

1. **Ensure your branch is up to date** with `master`.
2. **Fill out the PR template** completely.
3. **Describe what changed and why** — not just what files were modified.
4. **Include test results** — Show that your changes work by including sample output.
5. **Keep PRs focused** — One logical change per PR. Avoid mixing unrelated changes.
6. **Be responsive to feedback** — Address review comments promptly.

### PR Checklist

Before submitting, verify:

- [ ] Code follows the project's coding guidelines
- [ ] Type hints are added for new functions/methods
- [ ] Configuration changes are reflected in `env.example` and `config.example`
- [ ] New prompt templates are stored in `assets/prompts/`
- [ ] Documentation is updated as needed
- [ ] The skill runs successfully with your changes
- [ ] No API keys or secrets are committed

---

## Reporting Bugs

When reporting a bug, please include:

- **Python version** (`python --version`)
- **OS and version**
- **Which skill/pattern** you were running
- **Full command** used to trigger the bug
- **Error message** or unexpected output
- **Expected behavior**
- **Steps to reproduce**

---

## Suggesting Features

When suggesting a feature, please include:

- **Problem statement** — What problem does this solve?
- **Proposed solution** — How should it work?
- **Alternatives considered** — What other approaches did you think of?
- **Use cases** — Who would benefit and how?

---

## License

By contributing to agentic-reasoning-skills, you agree that your contributions will be licensed under the [MIT License](LICENSE).
