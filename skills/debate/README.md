# Multi-LLM Debate — 설치·사용 가이드

서로 다른 벤더의 LLM이 찬성·반대·중립 3역으로 토론하는 워크플로우.
스킬 정의(호출 요약) → [SKILL.md](./SKILL.md)

## 동작 방식

```
[주제] → Proponent(찬성) → Opponent(반대) → Moderator(중립 평가) → 통합 표시
          agy/Gemini3.5     claude/opus-4-8   codex/gpt-5.5(xhigh)
```
각 역할은 독립 컨텍스트에서 지정 역할에만 근거해 구조화 JSON을 출력하며, 앞 단계 출력을 다음 단계가 참고한다.

## 설치

### 1. CLI 백엔드 (구독 인증 · API 키 불필요)

| CLI | 역할 | 설치 | 인증 |
|-----|------|------|------|
| `agy` (Antigravity CLI) | 찬성 | https://antigravity.google → 설치 후 `agy install` | `agy` 최초 실행 시 OAuth |
| `claude` (Claude Code) | 반대 | `npm i -g @anthropic-ai/claude-code` | `claude` 실행 → 로그인(구독) |
| `codex` (Codex CLI) | 중립 | `npm i -g @openai/codex` | `codex login` (ChatGPT 구독) |

설치/인증 확인:
```bash
command -v agy claude codex      # 3개 경로가 모두 출력되면 OK
```

### 2. Python venv (최초 1회)

```bash
cd <skill-dir>/scripts
python3.13 -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt   # pydantic / python-dotenv / pyyaml 만 (LLM SDK 불필요)
```
`run.sh` 경유 시 venv는 자동 활성화된다.

## 사용법

### run.sh (권장)
```bash
<skill-dir>/scripts/run.sh "AI를 고객지원에 도입해야 하는가?

[컨텍스트]
- B2B SaaS / 월 문의 3000건 / 예산 연 500만엔 / SOC2 준수 필수"

<skill-dir>/scripts/run.sh --verbose "..."   # 3역 상세 출력
<skill-dir>/scripts/run.sh --json    "..."   # JSON 출력
```

### 직접 실행 / 모델 오버라이드
```bash
source scripts/.venv/bin/activate
python scripts/main.py "주제" \
    --proponent-model gemini-3.5-flash \
    --opponent-model  claude-opus-4-8 \
    --moderator-model gpt-5.5
# 프로바이더 교체: --proponent-provider {gemini|anthropic|openai|mock}
```

## 환경 변수

| 변수 | 기본 | 용도 |
|------|------|------|
| `MULTILLM_REASONING_EFFORT` | `xhigh` | Codex 추론 강도 (none/low/medium/high/xhigh) |
| `MULTILLM_CLI_TIMEOUT` | `360` | CLI 호출 타임아웃(초) |
| `MULTILLM_AGY_PRINT_TIMEOUT` | `5m` | agy `--print-timeout` |
| `MULTILLM_CLAUDE_MODEL` / `MULTILLM_CODEX_MODEL` | — | 백엔드별 모델 오버라이드 |
| `DEBATE_{PROPONENT,OPPONENT,MODERATOR}_{PROVIDER,MODEL}` | — | 역할별 오버라이드 |

## 오프라인 계약 테스트 (mock — CLI/네트워크 불필요)
```bash
DEBATE_PROPONENT_PROVIDER=mock DEBATE_OPPONENT_PROVIDER=mock DEBATE_MODERATOR_PROVIDER=mock \
  python scripts/main.py --no-config "test"
```

## 문제 해결

| 증상 | 대처 |
|------|------|
| `agy/claude/codex: command not found` | 위 설치 + PATH 확인 |
| `... 실패 (exit ...)` / 인증 에러 | 해당 CLI를 대화형으로 1회 실행해 로그인 |
| 타임아웃 | `MULTILLM_CLI_TIMEOUT` 증가 (xhigh는 시간이 걸림) |
| `Prompt file not found` | `assets/prompts/*.txt` 동봉 여부 확인 |
| 출력 비어있음 / JSON 깨짐 | `--verbose`로 각 단계 원시 출력 확인 |

## 아키텍처 (요약)

- `scripts/workflow/providers.py`의 3개 어댑터(Claude/Codex/Antigravity)가 `generate_structured()` 구현. 역할 executor·workflow는 무개조.
- 구조화 출력: claude `--output-format json --json-schema`(네이티브), codex `--output-schema`(네이티브), agy는 평문→JSON 지시+Pydantic 검증.
- 장문은 전부 stdin 경유(ARG_MAX/이스케이프 회피). agy는 tempdir cwd로 격리(`.antigravitycli` litter 방지).
- 구독 인증만 사용, API 키 불필요.
