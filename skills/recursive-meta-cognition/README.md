# Multi-LLM Recursive Meta-Cognition — 설치·사용 가이드

서로 다른 벤더의 LLM이 분해→해결→검증→통합→반성 5단계로 고품질 결과를 만드는 워크플로우.
스킬 정의(호출 요약) → [SKILL.md](./SKILL.md)

## 동작 방식

```
[문제] → Decomposer(분해) → Solver(해결) → Verifier(검증) → Integrator(통합) → Reflector(반성) → 최종본
          agy/Gemini3.5      agy/Gemini3.5   claude/opus-4-8  codex/gpt-5.5      codex/gpt-5.5(xhigh)
```
각 단계는 독립 컨텍스트에서 구조화 JSON을 출력하며, 검증의 지적을 통합·반성 단계가 반영한다.

## 설치

### 1. CLI 백엔드 (구독 인증 · API 키 불필요)

| CLI | 단계 | 설치 | 인증 |
|-----|------|------|------|
| `agy` (Antigravity CLI) | 분해·해결 | https://antigravity.google → 설치 후 `agy install` | `agy` 최초 실행 시 OAuth |
| `claude` (Claude Code) | 검증 | `npm i -g @anthropic-ai/claude-code` | `claude` 실행 → 로그인(구독) |
| `codex` (Codex CLI) | 통합·반성 | `npm i -g @openai/codex` | `codex login` (ChatGPT 구독) |

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
<skill-dir>/scripts/run.sh "신제품 출시를 6개월 앞당길 때의 리스크와 완화책을 단계적으로 도출해줘

[컨텍스트]
- 제품 종류·현재 단계·규제 요건 등 알고 있는 제약을 함께 기입"

<skill-dir>/scripts/run.sh --verbose "..."   # 5단계 상세 출력
<skill-dir>/scripts/run.sh --json    "..."   # JSON 출력
```

### 직접 실행 / 모델 오버라이드
```bash
source scripts/.venv/bin/activate
python scripts/main.py "문제" \
    --decomposer-model gemini-3.5-flash \
    --solver-model     gemini-3.5-flash \
    --verifier-model   claude-opus-4-8 \
    --integrator-model gpt-5.5 \
    --reflector-model  gpt-5.5
# 프로바이더 교체: --decomposer-provider {gemini|anthropic|openai|mock}
```

## 환경 변수

| 변수 | 기본 | 용도 |
|------|------|------|
| `MULTILLM_REASONING_EFFORT` | `xhigh` | Codex 추론 강도 (none/low/medium/high/xhigh) |
| `MULTILLM_CLI_TIMEOUT` | `360` | CLI 호출 타임아웃(초) |
| `MULTILLM_AGY_PRINT_TIMEOUT` | `5m` | agy `--print-timeout` |
| `MULTILLM_CLAUDE_MODEL` / `MULTILLM_CODEX_MODEL` | — | 백엔드별 모델 오버라이드 |
| `REFLECTION_{DECOMPOSER,SOLVER,VERIFIER,INTEGRATOR,REFLECTOR}_{PROVIDER,MODEL}` | — | 역할별 오버라이드 |

## 오프라인 계약 테스트 (mock — CLI/네트워크 불필요)
```bash
REFLECTION_DECOMPOSER_PROVIDER=mock REFLECTION_SOLVER_PROVIDER=mock REFLECTION_VERIFIER_PROVIDER=mock \
REFLECTION_INTEGRATOR_PROVIDER=mock REFLECTION_REFLECTOR_PROVIDER=mock \
  python scripts/main.py --no-config "test"
```

## 문제 해결

| 증상 | 대처 |
|------|------|
| `agy/claude/codex: command not found` | 위 설치 + PATH 확인 |
| `... 실패 (exit ...)` / 인증 에러 | 해당 CLI를 대화형으로 1회 실행해 로그인 |
| 타임아웃 (5단계는 길다) | `MULTILLM_CLI_TIMEOUT` 증가 (xhigh는 시간이 걸림) |
| `Prompt file not found` | `assets/prompts/*.txt` 동봉 여부 확인 |
| 출력 비어있음 / JSON 깨짐 | `--verbose`로 각 단계 원시 출력 확인 |

## 아키텍처 (요약)

- `scripts/workflow/providers.py`의 3개 어댑터(Claude/Codex/Antigravity)가 `generate_structured()` 구현. 역할 executor·workflow는 무개조.
- 구조화 출력: claude `--output-format json --json-schema`(네이티브), codex `--output-schema`(네이티브), agy는 평문→JSON 지시+Pydantic 검증.
- 장문은 전부 stdin 경유(ARG_MAX/이스케이프 회피). agy는 tempdir cwd로 격리.
- 구독 인증만 사용, API 키 불필요.
