# AI 토론 시스템 (AI Debate System)

## 프로젝트 개요

이 프로젝트는 여러 AI 모델이 특정 주제에 대해 상반된 입장으로 토론하고 합의점을 찾아가는 자동화된 토론 시스템입니다.

### 핵심 기능

- **다중 AI 모델 지원**: Claude, OpenAI GPT, Gemini, Grok 중 선택 가능
- **자동 입장 생성**: 주제를 분석하여 대립되는 두 입장을 자동으로 생성
- **구조화된 토론**: 초기 주장 → 토론 라운드 → 최종 합의안으로 이어지는 체계적 진행
- **조기 종료 메커니즘**: 양측이 합의 준비가 되면 최대 라운드 전에 토론 종료
- **실시간 기록**: 토론 과정을 마크다운 파일로 실시간 저장
- **글자 수 제한**: 답변 길이를 제한하여 간결한 토론 유지

## 아키텍처

### 주요 클래스

#### `AIModel` (dataclass)
AI 모델의 메타데이터를 저장하는 데이터 클래스
- `name`: 간단한 이름 (예: "Claude")
- `command`: CLI 명령어 리스트 (예: ["claude", "-p"])
- `display_name`: 전체 표시 이름 (예: "Claude (Anthropic)")

#### `AIDebateSystem`
토론 시스템의 메인 클래스

**주요 메서드:**

- `call_ai(prompt, ai_model)`: AI CLI를 subprocess로 호출하여 응답 받기
- `select_ai_for_stance(stance_title)`: 사용자에게 특정 입장에 대한 AI 모델 선택 받기
- `generate_filename_keyword(topic)`: 주제를 파일명용 영어 키워드로 변환
- `analyze_topic_and_create_stances(topic)`: 주제 분석 및 두 가지 상반된 입장 생성
- `check_consensus_ready(debate_setup, speaker, history)`: 합의 준비 여부 확인
- `get_ai_response(debate_setup, speaker, history, instruction)`: 특정 입장에서 AI 응답 생성
- `conduct_debate(debate_setup)`: 전체 토론 진행 (메인 로직)
- `initialize_debate_file(debate_setup)`: 토론 시작 시 마크다운 파일 초기화
- `append_to_debate_file(...)`: 실시간으로 토론 내용 파일에 추가
- `save_conclusion_file(...)`: 최종 합의안을 별도 파일로 저장

## 토론 진행 흐름

```
1. 사용자 입력
   ├─ 주제 입력
   ├─ 글자 수 제한 설정 (기본: 500자)
   └─ 최대 라운드 수 설정 (기본: 5)

2. 주제 분석 (Claude 사용)
   ├─ 토론 주제 명확화
   ├─ 입장 A 생성
   ├─ 입장 B 생성
   ├─ 입장 A용 AI 선택
   └─ 입장 B용 AI 선택

3. 토론 파일 초기화
   └─ {subject_slug}-{timestamp}.md 생성

4. 토론 진행 (라운드별)
   ├─ 라운드 1: 초기 주장
   │   ├─ 입장 A 발언
   │   └─ 입장 B 발언
   │
   ├─ 라운드 2~N-1: 토론
   │   ├─ 입장 A 발언 (반박/질문/합의점 모색)
   │   ├─ 입장 B 발언 (반박/질문/합의점 모색)
   │   └─ [최소 2라운드 후] 양측 합의 준비 확인
   │       └─ 둘 다 준비 완료 → 최종 합의안으로 이동
   │
   └─ 마지막 라운드: 최종 합의안
       ├─ 입장 A 합의안 제안
       └─ 입장 B 합의안 제안

5. 결과 저장
   ├─ 전체 토론 기록: {subject_slug}-{timestamp}.md
   └─ 최종 합의안: {subject_slug}-conclusion-{timestamp}.md
```

## 출력 파일 구조

### 전체 토론 기록 (`{subject_slug}-{timestamp}.md`)
```markdown
# AI 토론 기록

**생성 일시**: YYYY년 MM월 DD일 HH:MM:SS

---

## 📋 토론 주제

[주제 내용]

### 🔵 입장 A: [제목] ([AI 이름])
> [입장 설명]

### 🟡 입장 B: [제목] ([AI 이름])
> [입장 설명]

---

## 💬 토론 내용

### 라운드 1: 초기 주장
#### 🔵 [입장 A] (AI 이름)
[발언 내용]
#### 🟡 [입장 B] (AI 이름)
[발언 내용]

[... 후속 라운드들 ...]
```

### 최종 합의안 (`{subject_slug}-conclusion-{timestamp}.md`)
- 주제, 양측 입장, 최종 합의안만 포함

## 사용 방법

### 기본 실행
```bash
python ai_debate.py
```

### 명령줄 인자로 주제 전달
```bash
python ai_debate.py "주제를 여기에 입력"
```

### 대화형 설정
1. 글자 수 제한 설정 (기본: 500)
2. 최대 라운드 수 설정 (기본: 5, 최소: 2)
3. 토론 주제 입력
4. 각 입장별 AI 모델 선택

## 기술적 세부사항

### AI CLI 호출 방식
- `subprocess.run()`을 사용하여 각 AI CLI 실행
- stdin으로 프롬프트 전달
- stdout에서 응답 수신
- 5분 타임아웃 설정
- UTF-8 인코딩

### 답변 길이 제어
1. AI에게 목표 길이 가이드 제공 (최소: char_limit/4, 최대: char_limit)
2. 너무 짧으면 (< char_limit/4): 확장 요청 (1회)
3. 너무 길면 (> char_limit): 요약 요청 (1회)

### 합의 준비 확인
- 최소 2라운드 후부터 체크
- 양측 AI에게 독립적으로 YES/NO 질문
- 둘 다 YES면 최종 합의안 라운드로 조기 이동

### 지원 AI 모델 및 CLI 명령어

```python
AVAILABLE_AI_MODELS = {
    "claude": ["claude", "-p"],                        # Claude (Anthropic)
    "openai": ["codex", "exec", "--skip-git-repo-check"],  # OpenAI GPT
    "gemini": ["gemini", "-p"],                        # Gemini (Google)
    "grok": ["grok", "-p"]                             # Grok (xAI)
}
```

## 제약사항 및 주의사항

1. **CLI 의존성**: 각 AI 모델의 CLI가 시스템에 설치되어 있어야 함
2. **API 비용**: 각 AI 호출마다 API 비용 발생 가능
3. **응답 시간**: 라운드당 여러 번의 AI 호출로 인해 시간 소요
4. **언어**: 한국어 중심으로 설계됨 (프롬프트 및 출력)
5. **키워드 생성**: 파일명 키워드 생성 실패 시 "debate" 사용

## 프로젝트 파일

- `ai_debate.py`: 메인 시스템 코드
- `README.md`: 프로젝트 설명 문서
- `*.md`: 생성된 토론 기록 및 합의안 파일
- `.gitignore`: Git 제외 파일 설정

## 향후 개선 가능 사항

- [ ] 웹 인터페이스 추가
- [ ] 3명 이상의 다자간 토론 지원
- [ ] 토론 분석 및 통계 기능
- [ ] JSON/HTML 등 다양한 출력 형식 지원
- [ ] 비동기 처리로 성능 개선
- [ ] 토론 중간 저장 및 재개 기능
- [ ] 실시간 스트리밍 출력

## 코드 수정 시 유의사항

### AI 모델 추가 방법
1. `AVAILABLE_AI_MODELS` 딕셔너리에 새 모델 추가
2. `AIModel` 인스턴스 생성 (name, command, display_name 지정)
3. CLI 명령어는 리스트 형태로 제공

### 라운드 구조 수정
- `conduct_debate()` 메서드의 라운드 생성 로직 수정
- 각 라운드는 `name`과 `instruction` 필드 필요

### 프롬프트 수정
- 주제 분석: `analyze_topic_and_create_stances()` 메서드
- 토론 응답: `get_ai_response()` 메서드
- 합의 확인: `check_consensus_ready()` 메서드
- 키워드 생성: `generate_filename_keyword()` 메서드

## 문제 해결

### AI CLI를 찾을 수 없음
- 해당 AI CLI가 시스템 PATH에 설치되어 있는지 확인
- 명령어가 올바른지 확인 (예: `claude -p`)

### 응답 시간 초과
- 기본 타임아웃: 5분
- `call_ai()` 메서드의 `timeout` 파라미터 조정 가능

### JSON 파싱 오류
- `analyze_topic_and_create_stances()`에서 JSON 추출 로직 확인
- AI가 마크다운 코드블록으로 응답할 경우 처리됨
