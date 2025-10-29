# AI 토론 시스템 (AI Debate System)

## 프로젝트 개요

이 프로젝트는 여러 AI 모델이 특정 주제에 대해 다양한 입장으로 토론하고 합의점을 찾아가는 자동화된 토론 시스템입니다.

### 핵심 기능

- **다중 AI 모델 지원**: Claude, OpenAI GPT, Gemini, Grok 중 선택 가능
- **자동 모델 확인**: 프로그램 시작 시 사용 가능한 AI CLI를 자동으로 감지 및 캐싱
- **N명 토론 지원**: 2~10명의 참여자가 각자의 입장으로 토론 (이전 2명 제한 해제)
- **자동 제목 생성**: 입력한 핵심주장/역할로부터 AI가 자동으로 짧은 제목 생성
- **발언 순서 최적화**: 반대 입장자가 먼저 발언하도록 자동 정렬
- **공격적 토론**: AI가 논리적 오류, 모순점, 근거 부족 등을 적극적으로 지적
- **자연스러운 호칭**: 참여자를 "참여자 1, 2" 대신 실제 제목으로 지칭
- **구조화된 토론**: 초기 주장 → 토론 라운드 → 최종 합의안으로 이어지는 체계적 진행
- **조기 종료 메커니즘**: 모든 참여자가 합의 준비가 되면 최대 라운드 전에 토론 종료
- **통합 결론 생성**: AI가 모든 참여자의 합의안을 종합하여 하나의 통합 결론 작성
- **실시간 기록**: 토론 과정을 마크다운 파일로 실시간 저장
- **타임스탬프 통일**: 토론 기록과 결론 파일에 동일한 타임스탬프 사용
- **글자 수 제한**: 답변 길이를 제한하여 간결한 토론 유지

## 아키텍처

### 주요 클래스

#### `AIModel` (dataclass)
AI 모델의 메타데이터를 저장하는 데이터 클래스
- `name`: 간단한 이름 (예: "Claude")
- `command`: CLI 명령어 리스트 (예: ["claude", "-p"])
- `display_name`: 전체 표시 이름 (예: "Claude (Anthropic)")
- `test_command`: 가용성 테스트용 명령어 (예: ["claude", "--version"]) - *새로 추가*

#### `AIDebateSystem`
토론 시스템의 메인 클래스

**주요 메서드:**

- `call_ai(prompt, ai_model)`: AI CLI를 subprocess로 호출하여 응답 받기
- `select_ai_for_stance(stance_title)`: 사용자에게 특정 입장에 대한 AI 모델 선택 받기
- `generate_filename_keyword(topic)`: 주제를 파일명용 영어 키워드로 변환
- `generate_title_for_position(topic, position)`: 입장으로부터 짧은 제목 자동 생성 - *새로 추가*
- `create_stances_from_user_input(topic, num_participants)`: 사용자 입력으로 N명의 입장 생성 - *새로 추가*
- `check_consensus_ready(debate_setup, speaker, history)`: 합의 준비 여부 확인
- `get_ai_response(debate_setup, speaker, history, instruction)`: 특정 입장에서 AI 응답 생성
- `conduct_debate(debate_setup)`: 전체 토론 진행 (메인 로직)
- `synthesize_final_conclusion(debate_setup, final_proposals)`: 모든 합의안을 통합하여 하나의 결론 생성 - *새로 추가*
- `initialize_debate_file(debate_setup)`: 토론 시작 시 마크다운 파일 초기화
- `append_to_debate_file(...)`: 실시간으로 토론 내용 파일에 추가
- `save_conclusion_file(...)`: 최종 합의안 및 통합 결론을 별도 파일로 저장

**AI 모델 가용성 관련 함수** (모듈 레벨):
- `check_ai_model_availability(model_key, model)`: 특정 AI CLI의 실행 가능 여부 확인 (1초 타임아웃) - *새로 추가*
- `load_cached_models()`: 캐시 파일에서 사용 가능한 모델 목록 로드 - *새로 추가*
- `save_cached_models(available_keys)`: 사용 가능한 모델 목록을 캐시 파일에 저장 - *새로 추가*
- `initialize_available_models(force_refresh)`: 프로그램 시작 시 AI 모델 가용성 확인 및 초기화 - *새로 추가*

### 전역 변수

- `ALL_AI_MODELS`: 지원하는 모든 AI 모델의 정보 (상수)
- `AVAILABLE_AI_MODELS`: 현재 시스템에서 실제 사용 가능한 AI 모델 (런타임 시 초기화)

## AI 모델 자동 확인 시스템

### 동작 방식

프로그램 시작 시 `initialize_available_models()` 함수가 실행되어:

1. **캐시 확인**: `.ai_models_cache.json` 파일 존재 여부 확인
2. **캐시 사용**: 파일이 있으면 저장된 모델 목록 사용 (빠른 시작)
3. **모델 테스트**: 캐시가 없으면 모든 AI CLI의 `--version` 명령 실행
   - 각 테스트마다 1초 타임아웃
   - 성공 시 해당 모델을 `AVAILABLE_AI_MODELS`에 추가
4. **결과 저장**: 테스트 결과를 캐시 파일에 저장
5. **에러 처리**: 사용 가능한 모델이 하나도 없으면 설치 안내 후 종료

### 캐시 파일 구조

`.ai_models_cache.json`:
```json
{
  "available_models": ["claude", "gemini", "grok"],
  "timestamp": "2024-01-29 14:30:22"
}
```

### 캐시 갱신 방법

캐시를 강제로 갱신하려면:
```bash
rm .ai_models_cache.json
python3 ai_debate.py
```

또는 코드에서 `initialize_available_models(force_refresh=True)` 호출

## 토론 진행 흐름

```
1. AI 모델 가용성 확인
   ├─ 캐시 파일 확인 (.ai_models_cache.json)
   ├─ 없으면 모든 AI CLI 테스트 (--version)
   ├─ 사용 가능한 모델만 AVAILABLE_AI_MODELS에 등록
   ├─ 결과 캐시 저장
   └─ 사용 가능한 모델이 없으면 프로그램 종료

2. 사용자 입력
   ├─ 주제 입력
   ├─ 참여자 수 입력 (2~10명)
   ├─ 글자 수 제한 설정 (기본: 500자)
   └─ 최대 라운드 수 설정 (기본: 5)

3. 참여자 설정 (N명 반복)
   ├─ 핵심주장 또는 역할 입력
   ├─ AI가 자동으로 짧은 제목 생성 (예: "찬성파", "반대파")
   └─ AI 모델 선택 (사용 가능한 모델만 표시)

4. 발언 순서 최적화
   └─ 반대 입장자(찬성/반대)가 먼저 발언하도록 정렬

5. 토론 파일 초기화
   ├─ {subject_slug}-{timestamp}.md 생성
   └─ 타임스탬프를 self.timestamp에 저장

6. 토론 진행 (라운드별)
   ├─ 라운드 1: 초기 주장
   │   ├─ 참여자 1 발언
   │   ├─ 참여자 2 발언
   │   └─ ... 참여자 N 발언
   │
   ├─ 라운드 2~N-1: 토론
   │   ├─ 각 참여자가 순서대로 발언 (반박/질문/합의점 모색)
   │   │   └─ 다른 참여자들을 실제 제목으로 지칭 (예: "찬성파가 주장한...")
   │   └─ [최소 2라운드 후] 모든 참여자 합의 준비 확인
   │       └─ 모두 준비 완료 → 최종 합의안으로 이동
   │
   └─ 마지막 라운드: 최종 합의안
       ├─ 참여자 1 합의안 제안
       ├─ 참여자 2 합의안 제안
       ├─ ... 참여자 N 합의안 제안
       └─ AI가 모든 합의안을 종합하여 통합 결론 생성

7. 결과 저장
   ├─ 전체 토론 기록: {subject_slug}-{timestamp}.md
   └─ 최종 결론: {subject_slug}-conclusion-{timestamp}.md
       ├─ 통합된 최종 결론 (AI가 자동 생성)
       └─ 각 참여자별 합의안
```

## 출력 파일 구조

### 전체 토론 기록 (`{subject_slug}-{timestamp}.md`)
```markdown
# AI 토론 기록

**생성 일시**: YYYY년 MM월 DD일 HH:MM:SS

---

## 📋 토론 주제

[주제 내용]

### 🔵 참여자 1: [제목] ([AI 이름])
> [입장 설명]

### 🟡 참여자 2: [제목] ([AI 이름])
> [입장 설명]

### 🟢 참여자 3: [제목] ([AI 이름])
> [입장 설명]

... (N명까지)

---

## 💬 토론 내용

### 라운드 1: 초기 주장
#### 🔵 [제목] (AI 이름)
[발언 내용]
#### 🟡 [제목] (AI 이름)
[발언 내용]

[... 후속 라운드들 ...]
```

### 최종 합의안 (`{subject_slug}-conclusion-{timestamp}.md`)
```markdown
# 토론 결론

**생성 일시**: YYYY년 MM월 DD일 HH:MM:SS (토론 파일과 동일)

---

## 📋 토론 주제
[주제 내용]

## 👥 참여자 입장
[모든 참여자의 입장 요약]

---

## 🎯 통합된 최종 결론

[AI가 자동으로 생성한 통합 결론]
- 모든 참여자의 핵심 제안을 균형있게 반영
- 공통된 합의점 명확히 제시
- 구체적이고 실행 가능한 결론

---

## 📝 참여자별 제안사항

### 🔵 [참여자 1 제목]
[합의안 내용]

### 🟡 [참여자 2 제목]
[합의안 내용]

... (N명까지)
```

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
1. 주제 입력
2. 참여자 수 입력 (2~10명)
3. 각 참여자마다:
   - 핵심주장 또는 역할 입력
   - AI가 자동으로 제목 생성 (예: "찬성파", "현실주의자")
   - AI 모델 선택 (사용 가능한 모델만 표시)
4. 글자 수 제한 설정 (기본: 500)
5. 최대 라운드 수 설정 (기본: 5, 최소: 2)

## 기술적 세부사항

### AI CLI 호출 방식
- `subprocess.run()`을 사용하여 각 AI CLI 실행
- stdin으로 프롬프트 전달
- stdout에서 응답 수신
- 5분 타임아웃 설정
- UTF-8 인코딩

### AI 모델 가용성 테스트
- `--version` 명령으로 실행 가능 여부 확인
- 각 테스트마다 1초 타임아웃
- `FileNotFoundError` 또는 타임아웃 시 해당 모델 제외
- 결과를 `.ai_models_cache.json`에 저장하여 재사용

### 자동 제목 생성
- 사용자가 입력한 "핵심주장 또는 역할"을 기반으로 AI가 2-5 단어 제목 생성
- 예: "원격 근무를 찬성합니다" → "원격 근무 찬성파"
- 예: "CEO 역할" → "CEO"
- 첫 번째 사용 가능한 AI 모델 사용

### 공격적 토론 프롬프트
AI에게 다음 지시사항 제공:
- 반박할 여지가 있다면 적극적으로 반박
- 논리적 오류, 근거 부족, 모순점, 과장 등을 날카롭게 지적
- 상대 주장의 약점을 찾아내고 대안이나 반례 제시
- 쉽게 동의하지 말고 비판적 사고로 면밀히 검토

### 자연스러운 참여자 호칭
- 과거: "참여자 1이 주장한 바와 같이..."
- 현재: "찬성파가 주장한 바와 같이..."
- 모든 프롬프트와 히스토리에서 실제 제목 사용

### 통합 결론 생성
- 모든 참여자의 최종 합의안을 AI에게 제공
- AI가 다음을 포함한 통합 결론 작성:
  - 모든 참여자의 핵심 제안을 균형있게 반영
  - 공통된 합의점 명확히 제시
  - 구체적이고 실행 가능한 결론
  - 각 참여자의 우려사항이나 조건 포함
  - 체계적이고 논리적인 구조 (마크다운 형식)

### 답변 길이 제어
1. AI에게 목표 길이 가이드 제공 (최소: char_limit/4, 최대: char_limit)
2. 너무 짧으면 (< char_limit/4): 확장 요청 (1회)
3. 너무 길면 (> char_limit): 요약 요청 (1회)

### 합의 준비 확인
- 최소 2라운드 후부터 체크
- 모든 참여자에게 독립적으로 YES/NO 질문
- 모두 YES면 최종 합의안 라운드로 조기 이동

### 발언 순서 최적화
참여자의 `agree_or_disagree` 필드를 기반으로 정렬:
1. "반대" 입장 참여자들
2. "찬성" 입장 참여자들
3. "중립" 또는 기타 입장 참여자들

### 타임스탬프 통일
- `__init__`에서 `self.timestamp` 생성 및 저장
- `initialize_debate_file()`과 `save_conclusion_file()` 모두 동일한 타임스탬프 사용
- 토론 기록과 결론 파일의 파일명 및 생성 시각 완전 일치

### 지원 AI 모델 및 CLI 명령어

```python
ALL_AI_MODELS = {
    "claude": AIModel(
        "Claude",
        ["claude", "-p"],
        "Claude (Anthropic)",
        ["claude", "--version"]
    ),
    "openai": AIModel(
        "OpenAI",
        ["codex", "exec", "--skip-git-repo-check"],
        "OpenAI GPT",
        ["codex", "--version"]
    ),
    "gemini": AIModel(
        "Gemini",
        ["gemini", "-p"],
        "Gemini (Google)",
        ["gemini", "--version"]
    ),
    "grok": AIModel(
        "Grok",
        ["grok", "-p"],
        "Grok (xAI)",
        ["grok", "--version"]
    )
}
```

## 제약사항 및 주의사항

1. **CLI 의존성**: 각 AI 모델의 CLI가 시스템에 설치되어 있어야 함
   - 프로그램 시작 시 자동으로 확인하여 사용 가능한 모델만 표시
2. **API 비용**: 각 AI 호출마다 API 비용 발생 가능
3. **응답 시간**: 라운드당 여러 번의 AI 호출로 인해 시간 소요
4. **언어**: 한국어 중심으로 설계됨 (프롬프트 및 출력)
5. **키워드 생성**: 파일명 키워드 생성 실패 시 "debate" 사용
6. **캐시 갱신**: AI CLI를 새로 설치한 경우 캐시 파일 삭제 필요

## 프로젝트 파일

- `ai_debate.py`: 메인 시스템 코드
- `README.md`: 프로젝트 설명 문서 (사용자용)
- `CLAUDE.md`: 기술 문서 (개발자용)
- `.ai_models_cache.json`: AI 모델 가용성 캐시 파일 (자동 생성)
- `debate_log_*.md`: 생성된 토론 기록 파일 (gitignore)
- `*-conclusion-*.md`: 생성된 결론 파일 (gitignore)
- `.gitignore`: Git 제외 파일 설정

## 향후 개선 가능 사항

- [ ] 웹 인터페이스 추가
- [x] ~~3명 이상의 다자간 토론 지원~~ ✅ 완료 (2~10명 지원)
- [ ] 토론 분석 및 통계 기능
- [ ] JSON/HTML 등 다양한 출력 형식 지원
- [ ] 비동기 처리로 성능 개선
- [ ] 토론 중간 저장 및 재개 기능
- [ ] 실시간 스트리밍 출력
- [ ] AI 모델 선택 전략 (예: 찬성파는 항상 Claude 사용 등)
- [ ] 참여자별 발언 시간 및 통계 추적

## 코드 수정 시 유의사항

### AI 모델 추가 방법
1. `ALL_AI_MODELS` 딕셔너리에 새 모델 추가
2. `AIModel` 인스턴스 생성 (name, command, display_name, test_command 지정)
3. CLI 명령어는 리스트 형태로 제공
4. `test_command`는 가용성 확인을 위한 `--version` 명령 등
5. 캐시 파일 삭제 후 재실행하여 새 모델 감지 확인

### 라운드 구조 수정
- `conduct_debate()` 메서드의 라운드 생성 로직 수정
- 각 라운드는 `name`과 `instruction` 필드 필요

### 프롬프트 수정
- 제목 생성: `generate_title_for_position()` 메서드
- 토론 응답: `get_ai_response()` 메서드 (공격적 토론 지시사항 포함)
- 합의 확인: `check_consensus_ready()` 메서드
- 통합 결론: `synthesize_final_conclusion()` 메서드
- 키워드 생성: `generate_filename_keyword()` 메서드

### 참여자 호칭 수정
- `get_ai_response()`에서 다른 참여자를 지칭할 때 `stance['title']` 사용
- 히스토리 표시 시 `speaker_label`에 실제 제목 사용
- "나", "당신" 등의 호칭 대신 구체적인 제목 사용

## 문제 해결

### AI CLI를 찾을 수 없음
- 프로그램 시작 시 자동으로 감지하여 에러 메시지 표시
- 해당 AI CLI를 시스템 PATH에 설치 후 캐시 파일 삭제
```bash
rm .ai_models_cache.json
python3 ai_debate.py
```

### 응답 시간 초과
- 기본 타임아웃: 5분 (AI 호출), 1초 (모델 테스트)
- `call_ai()` 메서드의 `timeout` 파라미터 조정 가능
- `check_ai_model_availability()`의 타임아웃도 필요시 조정

### JSON 파싱 오류
- `generate_filename_keyword()`에서 JSON 추출 로직 확인
- AI가 마크다운 코드블록으로 응답할 경우 처리됨

### 캐시 문제
- AI CLI를 새로 설치했는데 인식되지 않음 → 캐시 파일 삭제
- 잘못된 모델이 캐시에 남아있음 → 캐시 파일 삭제
```bash
rm .ai_models_cache.json
```

## 학술 참고자료

AI 토론 시스템 개발과 관련된 학술 연구:

1. **Multi-Agent Debate**: [Improving Factuality and Reasoning in Language Models through Multiagent Debate](https://arxiv.org/abs/2305.14325)
2. **Consensus Formation**: [Reaching Consensus in Multi-Agent Systems](https://ieeexplore.ieee.org/document/9662293)
3. **AI Argumentation**: [Computational Models of Argument](https://www.cambridge.org/core/books/computational-models-of-argument/1B3B8B8B8B8B8B8B8B8B8B8B8B8B8B8B)

