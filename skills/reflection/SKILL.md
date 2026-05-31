---
name: multi-llm-reflection
description: 高品質なコンテンツ生成向け。複数の異なるLLMが Generator→Critic→Refiner の3段階で草案を作り、批判し、改善する自己反省ワークフロー
---

# Multi-LLM Reflection

서로 다른 벤더의 CLI(Antigravity `agy` / Claude Code `claude` / Codex `codex`)를 **생성·비판·개선** 3단계로 실행해 초안을 비판·개선하는 자기반성 워크플로우. **API 키 불필요**(각 CLI의 구독 인증 사용).

## 실행 (이것만)

```bash
<skill-dir>/scripts/run.sh "작성/해결할 작업 (컨텍스트도 함께 적으면 품질↑)"
# 3단계 상세: --verbose   |   JSON 출력: --json
```

`run.sh`가 venv를 자동 활성화한다. **초기 1회 설치**가 필요 → [README.md](./README.md)

## 전제 (미인증이면 실행 불가)

| 단계 | CLI | 기본 모델 |
|------|-----|----------|
| 생성 Generator | `agy` | Gemini 3.5 Flash |
| 비판 Critic | `claude` | claude-opus-4-8 |
| 개선 Refiner | `codex` | gpt-5.5 (reasoning xhigh) |

`command -v agy claude codex` 로 3개가 모두 잡히고 각각 로그인돼 있어야 한다.
**설치·인증·모델/환경변수 오버라이드·문제 해결 → [README.md](./README.md)**

장문 입력은 stdin으로 안전하게 전달되고, 구조화 JSON으로 다음 단계에 넘어간다.
