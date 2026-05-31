---
name: multi-llm-debate
description: 複雑な意思決定向け。異なるベンダーのLLM（Gemini/Claude/GPT）が賛成・反対・中立の3役で討論し、多角的な結論を導く
---

# Multi-LLM Debate

서로 다른 벤더의 CLI(Antigravity `agy` / Claude Code `claude` / Codex `codex`)를 **찬성·반대·중립** 3역으로 순차 실행해 토론으로 결론을 도출한다. **API 키 불필요**(각 CLI의 구독 인증 사용).

## 실행 (이것만)

```bash
<skill-dir>/scripts/run.sh "토론 주제 (컨텍스트도 함께 적으면 품질↑)"
# 3역 상세: --verbose   |   JSON 출력: --json
```

`run.sh`가 venv를 자동 활성화한다. **초기 1회 설치**가 필요 → [README.md](./README.md)

## 전제 (미인증이면 실행 불가)

| 역할 | CLI | 기본 모델 |
|------|-----|----------|
| 찬성 Proponent | `agy` | Gemini 3.5 Flash |
| 반대 Opponent | `claude` | claude-opus-4-8 |
| 중립 Moderator | `codex` | gpt-5.5 (reasoning xhigh) |

`command -v agy claude codex` 로 3개가 모두 잡히고 각각 로그인돼 있어야 한다.
**설치·인증·모델/환경변수 오버라이드·문제 해결 → [README.md](./README.md)**

장문 입력은 stdin으로 안전하게 전달되고, 구조화 JSON으로 다음 단계에 넘어간다.
