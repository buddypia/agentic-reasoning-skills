<h1 align="center">🧠 agentic-reasoning-skills</h1>

<p align="center">
  <strong>인지 사고 패턴으로 여러 LLM을 오케스트레이션</strong>
</p>

<p align="center">
  <a href="#-빠른-시작">빠른 시작</a> •
  <a href="#-패턴">패턴</a> •
  <a href="#-설치">설치</a> •
  <a href="#-사용법">사용법</a> •
  <a href="#-설정">설정</a> •
  <a href="./README.md">English</a> •
  <a href="./README_ja.md">日本語</a> •
  <a href="./README_zh.md">中文</a>
</p>

<p align="center">
  <a href="https://github.com/buddypia/agentic-reasoning-skills/blob/main/LICENSE"><img src="https://img.shields.io/badge/license-MIT-blue.svg" alt="License: MIT"></a>
  <a href="https://www.python.org/downloads/"><img src="https://img.shields.io/badge/python-3.13%2B-blue.svg" alt="Python 3.13+"></a>
  <a href="https://github.com/buddypia/agentic-reasoning-skills/stargazers"><img src="https://img.shields.io/github/stars/buddypia/agentic-reasoning-skills.svg?style=social" alt="GitHub Stars"></a>
</p>

---

## agentic-reasoning-skills이란?

**agentic-reasoning-skills**은 여러 LLM(Gemini, Claude, OpenAI)을 인지 사고 패턴에 기반하여 오케스트레이션하는 경량 Python 프레임워크입니다. 무거운 에이전트 프레임워크 의존성이 전혀 없습니다.

단일 LLM에 의존하는 대신, 서로 다른 모델의 강점을 활용하여 구조화된 사고 워크플로우에서 전문적인 역할을 부여합니다:

| 패턴 | 단계 수 | 최적 용도 |
|------|:------:|----------|
| 🪞 **리플렉션** | 3 | 콘텐츠 생성, 품질 향상 |
| ⚔️ **디베이트** | 3 | 의사결정, 리스크 분석 |
| 🧠 **메타인지** | 5 | 복잡한 문제 해결, 설계 |

### 왜 agentic-reasoning-skills인가?

- 🪶 **경량** — LangChain도 CrewAI도 불필요. 순수 Python + 공식 SDK만 사용.
- 🧠 **인지 패턴** — 인지과학에 기반: 리플렉션, 변증법적 사고, 메타인지.
- 🔀 **멀티 프로바이더** — Gemini, Claude, OpenAI를 하나의 파이프라인에. 각 모델의 강점 활용.
- ⚙️ **유연한 설정** — CLI 인수 > 환경 변수 > 설정 파일 > 기본값. 자유롭게 선택.
- 📊 **구조화 출력** — 모든 단계가 Pydantic v2 스키마로 검증된 JSON 반환.

---

## 🚀 빠른 시작

```bash
# 클론
git clone https://github.com/buddypia/agentic-reasoning-skills.git
cd agentic-reasoning-skills

# API 키 설정
export GEMINI_API_KEY="your-key"
export ANTHROPIC_API_KEY="your-key"
export OPENAI_API_KEY="your-key"

# 리플렉션 패턴 실행
cd skills/reflection
pip install -r scripts/requirements.txt
python scripts/main.py "마이크로서비스 vs 모놀리스에 대한 기술 블로그 글을 작성해주세요"

# 디베이트 패턴 실행
cd ../debate
pip install -r scripts/requirements.txt
python scripts/main.py "고객 지원에 AI 에이전트를 도입해야 할까요?"

# 메타인지 패턴 실행
cd ../meta-cognition
pip install -r scripts/requirements.txt
python scripts/main.py "이커머스 플랫폼을 위한 확장 가능한 이벤트 기반 아키텍처를 설계해주세요"
```

---

## 🧩 패턴

### 🪞 리플렉션 (Generator → Critic → Refiner)

인간의 글쓰기 프로세스를 모델링: 초안 작성, 검토, 다듬기.

```
┌──────────────┐     ┌──────────────┐     ┌──────────────┐
│  Generator   │────▶│    Critic     │────▶│   Refiner    │
│  (Gemini)    │     │   (Claude)    │     │  (OpenAI)    │
│              │     │              │     │              │
│ 창의적으로   │     │ 분석하고     │     │ 수정 사항    │
│ 초안 작성    │     │ 문제점 지적   │     │ 적용 및 완성 │
└──────────────┘     └──────────────┘     └──────────────┘
```

**최적 용도**: 기술 블로그, 백서, 비교 보고서, 문서 작성

```bash
python scripts/main.py "WebSocket 보안에 대한 포괄적인 가이드를 작성해주세요"
python scripts/main.py --verbose "프롬프트"     # 전체 3단계 표시
python scripts/main.py --json "프롬프트"        # JSON 출력
python scripts/main.py --raw "프롬프트"         # LLM 원본 데이터 표시
```

### ⚔️ 디베이트 (Proponent → Opponent → Moderator)

변증법적 사고를 모델링: 정(正), 반(反), 합(合).

```
┌──────────────┐     ┌──────────────┐     ┌──────────────┐
│  Proponent   │────▶│   Opponent   │────▶│  Moderator   │
│  (Gemini)    │     │   (Claude)   │     │  (OpenAI)    │
│              │     │              │     │              │
│ 찬성 입장에서│     │ 반대 입장에서│     │ 객관적으로   │
│ 근거 제시    │     │ 리스크 지적  │     │ 판정 및 추천 │
└──────────────┘     └──────────────┘     └──────────────┘
```

**최적 용도**: 사업 판단, 기술 선정, 정책 평가, 리스크 분석

```bash
python scripts/main.py "REST에서 GraphQL로 마이그레이션해야 할까요?"
python scripts/main.py --random-providers "주제"   # 랜덤 역할 할당
python scripts/main.py --shuffle-providers "주제"  # 셔플 (중복 없음)
```

### 🧠 메타인지 (Decompose → Solve → Verify → Integrate → Reflect)

재귀적 메타인지 사고를 모델링: 가장 철저한 분석 파이프라인.

```
┌────────────┐   ┌────────────┐   ┌────────────┐   ┌────────────┐   ┌────────────┐
│ Decomposer │──▶│   Solver   │──▶│  Verifier  │──▶│ Integrator │──▶│ Reflector  │
│  (Gemini)  │   │  (Gemini)  │   │  (Claude)  │   │  (OpenAI)  │   │  (OpenAI)  │
│            │   │            │   │            │   │            │   │            │
│ 과제를     │   │ 각 하위    │   │ 논리 검증  │   │ 전체를     │   │ 성찰과     │
│ 요소 분해  │   │ 작업 해결  │   │ 및 수정    │   │ 통합       │   │ 신뢰도 평가│
└────────────┘   └────────────┘   └────────────┘   └────────────┘   └────────────┘
```

**최적 용도**: 아키텍처 설계, 전략 분석, 포괄적 리서치, 복잡한 계획 수립

```bash
python scripts/main.py "멀티테넌트 SaaS 아키텍처를 설계해주세요"
python scripts/main.py --verbose "프롬프트"              # 전체 5단계 표시
python scripts/main.py --output-schema flat "프롬프트"   # 플랫 JSON 스키마
python scripts/main.py --timeout 300 "복잡한 작업"       # 타임아웃 연장
```

---

## 📦 설치

### 요구 사항

- Python 3.13+
- 최소 1개 프로바이더의 API 키 (3개 모두 권장)

### 패턴별 설치

```bash
# 리플렉션
cd skills/reflection && pip install -r scripts/requirements.txt

# 디베이트
cd skills/debate && pip install -r scripts/requirements.txt

# 메타인지
cd skills/meta-cognition && pip install -r scripts/requirements.txt
```

### 의존성

| 패키지 | 버전 | 용도 |
|--------|------|------|
| `pydantic` | ≥2.12.5 | 타입 검증 & JSON 스키마 |
| `python-dotenv` | ≥1.2.1 | 환경 파일 로딩 |
| `pyyaml` | ≥6.0.3 | YAML 설정 지원 |
| `openai` | ≥2.15.0 | OpenAI API |
| `anthropic` | ≥0.76.0 | Claude API |
| `google-genai` | ≥1.60.0 | Gemini API |

---

## ⚙️ 설정

### API 키

```bash
# 방법 1: 환경 변수
export GEMINI_API_KEY="your-gemini-key"
export ANTHROPIC_API_KEY="your-anthropic-key"
export OPENAI_API_KEY="your-openai-key"

# 방법 2: .env 파일
cp env.example .env
# .env 파일 편집

# 방법 3: 설정 파일
cp config.example config.yaml
# config.yaml 편집
```

### 설정 우선순위

```
CLI 인수  →  환경 변수  →  설정 파일  →  기본값
(최고)                                  (최저)
```

### 커스텀 모델

```bash
# 리플렉션
python scripts/main.py "프롬프트" \
  --generator-model gemini-2.0-flash \
  --critic-model claude-sonnet-4-20250514 \
  --refiner-model gpt-4o

# 디베이트
python scripts/main.py "프롬프트" \
  --proponent-model gemini-2.0-flash \
  --opponent-model claude-sonnet-4-20250514 \
  --moderator-model gpt-4o

# 메타인지
python scripts/main.py "프롬프트" \
  --decomposer-model gemini-2.0-flash \
  --solver-model gemini-2.0-flash \
  --verifier-model claude-sonnet-4-20250514 \
  --integrator-model gpt-4o \
  --reflector-model gpt-4o
```

### 역할별 환경 변수

```bash
# 패턴: REFLECTION_<ROLE>_<SETTING>
REFLECTION_GENERATOR_PROVIDER=gemini
REFLECTION_GENERATOR_MODEL=gemini-2.0-flash
REFLECTION_GENERATOR_API_KEY=your-key
REFLECTION_GENERATOR_TEMPERATURE=0.7
REFLECTION_GENERATOR_TIMEOUT=120
```

---

## 📊 출력 옵션

| 플래그 | 설명 |
|--------|------|
| `--verbose` | 모든 단계의 출력 표시 |
| `--json` | JSON 형식으로 출력 |
| `--raw` | LLM 원본 요청/응답 데이터 표시 |
| `--raw-output <path>` | 원본 데이터를 JSON 파일로 저장 |
| `--output-schema nested\|flat` | JSON 스키마 구조 (메타인지 전용) |

---

## 🏗️ 아키텍처

### 경량 워크플로우 엔진

코어 엔진은 프레임워크 의존성 제로의 약 200줄 Python 코드:

```python
# Executor(단계) 정의
class MyExecutor(Executor):
    @handler
    async def process(self, payload: dict, ctx: Context):
        result = await call_llm(payload)
        ctx.set_shared_state("my_result", result)
        ctx.send_message(result)

# 워크플로우 빌드
workflow = (
    WorkflowBuilder()
    .set_start_executor(stage1)
    .add_edge(stage1, stage2)
    .add_edge(stage2, stage3)
    .build()
)

# 실행
result = await workflow.run({"prompt": "입력 텍스트"})
```

### 프로바이더 추상화

모든 LLM 프로바이더가 통일된 인터페이스를 공유:

```python
# 설정에 따른 자동 프로바이더 선택
response = await providers.call(
    provider="gemini",          # 또는 "anthropic", "openai"
    model="gemini-2.0-flash",
    system_prompt="당신은...",
    user_prompt="분석해주세요...",
    response_schema=MySchema,   # Pydantic 모델 → JSON 스키마
)
```

### 구조화 출력

모든 단계가 JSON 스키마를 사용하여 신뢰할 수 있는 데이터 추출을 구현:

```python
class CriticOutput(BaseModel):
    strengths: list[str]       # 강점
    weaknesses: list[str]      # 약점
    suggestions: list[str]     # 개선 제안
    score: float = Field(ge=0, le=10)        # 점수
    confidence: float = Field(ge=0, le=1)    # 신뢰도
```

---

## 🤝 기여하기

기여를 환영합니다! 다음과 같은 방법으로 참여할 수 있습니다:

- 🐛 **버그 리포트** — 문제를 발견하셨다면 GitHub Issue를 생성해주세요.
- 💡 **새로운 패턴** — 새로운 사고 패턴 아이디어가 있으시면 알려주세요.
- 🔌 **새로운 프로바이더** — Mistral, Cohere, 로컬 모델 지원 추가.
- 📖 **문서** — 문서 개선, 예제 추가, 오타 수정.
- 🧪 **테스트** — 테스트 커버리지 추가.

---

## 📄 라이선스

MIT License — 자세한 내용은 [LICENSE](LICENSE)를 참조하세요.

---

## 🌟 스타 히스토리

이 프로젝트가 유용하다면 스타를 눌러주세요! ⭐

---

<p align="center">
  🧠 <a href="https://github.com/buddypia">buddypia</a>가 만들었습니다
</p>
