---
name: multi-llm-recursive-meta-cognition
description: Recursive Meta-Cognition（再帰的メタ認知）を使用したワークフローを実行するスキル。複数の異なるLLMを順次組み合わせて、高品質なコンテンツを生成する（5段階 分解→解決→検証→統合→反省）。
---

# Multi-LLM Recursive Meta-Cognition

서로 다른 벤더의 CLI(Antigravity `agy` / Claude Code `claude` / Codex `codex`)를 **분해→해결→검증→통합→반성** 5단계로 순차 실행하는 재귀적 메타인지 워크플로우. **API 키 불필요**(각 CLI의 구독 인증 사용).

## 실행 (이것만)

```bash
<skill-dir>/scripts/run.sh "해결/작성할 문제 (컨텍스트도 함께 적으면 품질↑)"
# 5단계 상세: --verbose   |   JSON 출력: --json
```

`run.sh`가 venv를 자동 활성화한다. **초기 1회 설치**가 필요 → [README.md](./README.md)

## 전제 (미인증이면 실행 불가)

| 단계 | CLI | 기본 모델 |
|------|-----|----------|
| 분해 Decomposer / 해결 Solver | `agy` | Gemini 3.5 Flash |
| 검증 Verifier | `claude` | claude-opus-4-8 |
| 통합 Integrator / 반성 Reflector | `codex` | gpt-5.5 (reasoning xhigh) |

`command -v agy claude codex` 로 3개가 모두 잡히고 각각 로그인돼 있어야 한다.
**설치·인증·모델/환경변수 오버라이드·문제 해결 → [README.md](./README.md)**

> ⚠️ 5단계라 **완료까지 수 분** 걸릴 수 있다(진행 중 출력이 없을 수 있음). 장문 입력은 stdin으로 전달된다.
