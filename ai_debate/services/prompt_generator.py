"""프롬프트 생성 서비스"""

from typing import List, Dict
from ai_debate.models.debate_setup import DebateSetup


class PromptGenerator:
    """토론 시스템에서 사용하는 모든 프롬프트 생성"""

    def generate_filename_keyword_prompt(self, topic: str) -> str:
        """파일명 키워드 생성 프롬프트

        Args:
            topic: 토론 주제

        Returns:
            프롬프트 텍스트
        """
        return f"""다음 주제를 파일명으로 사용할 수 있는 짧은 영어 키워드로 변환해주세요.

주제: "{topic}"

요구사항:
- 3-5개의 영어 단어로 구성
- 소문자만 사용
- 단어는 하이픈(-)으로 연결
- 특수문자 사용 금지
- 파일명으로 적합하게

예시:
주제: "원격 근무와 사무실 근무 중 어느 것이 더 생산적인가?"
답변: remote-vs-office-productivity

다른 텍스트 없이 키워드만 답변해주세요."""

    def generate_title_prompt(self, topic: str, position: str) -> str:
        """참여자 제목 생성 프롬프트

        Args:
            topic: 토론 주제
            position: 핵심 주장 또는 역할

        Returns:
            프롬프트 텍스트
        """
        return f"""다음 토론 주제와 입장을 보고, 이 입장을 대표하는 짧은 제목을 생성해주세요.

토론 주제: {topic}
핵심 주장: {position}

요구사항:
- 2-5 단어로 구성된 짧은 제목
- 입장의 핵심을 명확하게 표현
- 예시: "찬성파", "반대파", "중도파", "신중론자", "급진론자", "현실주의자" 등

다른 설명 없이 제목만 답변해주세요."""

    def generate_debate_prompt(
        self,
        debate_setup: DebateSetup,
        speaker_idx: int,
        history: List[Dict],
        instruction: str
    ) -> str:
        """토론 프롬프트 생성

        Args:
            debate_setup: 토론 설정
            speaker_idx: 발언자 인덱스
            history: 대화 히스토리
            instruction: 현재 라운드 지시사항

        Returns:
            프롬프트 텍스트
        """
        stance = debate_setup.stances[speaker_idx]

        # 다른 참여자들의 입장 정리
        other_stances = []
        for i, s in enumerate(debate_setup.stances):
            if i != speaker_idx:
                other_stances.append(f"{s.title}: {s.position}")

        other_stances_text = "\n".join(other_stances)

        prompt = f"""당신은 "{stance.title}"입니다.

토론 주제: {debate_setup.topic}

당신의 입장: {stance.position}

다른 참여자들의 입장:
{other_stances_text}

토론 규칙:
- 자신의 입장을 강력하게 방어하세요
- 다른 참여자의 주장에 반박할 여지가 있다면 적극적으로 반박하세요
- 상대의 논리적 오류, 근거 부족, 모순점, 과장, 일반화의 오류 등을 날카롭게 지적하세요
- 논리적이고 구체적인 반론과 근거를 제시하세요
- 감정적이거나 인신공격적인 표현은 피하되, 논리적으로는 강하게 반박하세요
- 쉽게 동의하지 말고, 비판적 사고로 상대 주장을 면밀히 검토하세요
- 타당한 지적만 수용하고, 반박 가능한 부분은 절대 놓치지 마세요
- 상대 주장의 약점을 찾아내고, 대안이나 반례를 제시하세요

현재 지시사항: {instruction}

한국어로 자연스럽게 답변해주세요."""

        # 대화 히스토리 추가
        if history:
            prompt += "\n\n지금까지의 토론 내용:\n\n"
            for msg in history:
                if msg['speaker_idx'] == speaker_idx:
                    speaker_label = "나"
                else:
                    other_stance = debate_setup.stances[msg['speaker_idx']]
                    speaker_label = other_stance.title
                prompt += f"{speaker_label}: {msg['content']}\n\n"

        return prompt

    def generate_consensus_check_prompt(
        self,
        debate_setup: DebateSetup,
        speaker_idx: int,
        history: List[Dict]
    ) -> str:
        """합의 준비 확인 프롬프트

        Args:
            debate_setup: 토론 설정
            speaker_idx: 발언자 인덱스
            history: 대화 히스토리

        Returns:
            프롬프트 텍스트
        """
        stance = debate_setup.stances[speaker_idx]

        # 다른 참여자들의 최근 발언 정리
        recent_messages = history[-len(debate_setup.stances):] if len(history) >= len(debate_setup.stances) else history

        other_positions = []
        for msg in recent_messages:
            if msg['speaker_idx'] != speaker_idx:
                other_stance = debate_setup.stances[msg['speaker_idx']]
                other_positions.append(f"{other_stance.title}: {msg['content'][:200]}...")

        other_positions_text = "\n\n".join(other_positions)

        return f"""당신은 "{stance.title}"입니다.

토론 주제: {debate_setup.topic}
당신의 입장: {stance.position}

다른 참여자들의 최근 발언:
{other_positions_text}

질문: 이제 최종 합의안을 도출할 준비가 되셨습니까?

- YES: 충분히 토론했고, 합의점을 찾을 수 있다고 판단되면
- NO: 아직 더 논의가 필요하거나, 상대의 주장에 반박할 점이 남아있으면

**중요**: 'YES' 또는 'NO' 중 하나만 정확히 답변하세요. 다른 설명은 필요 없습니다."""

    def generate_synthesis_prompt(
        self,
        debate_setup: DebateSetup,
        final_proposals: List[Dict]
    ) -> str:
        """최종 결론 종합 프롬프트

        Args:
            debate_setup: 토론 설정
            final_proposals: 최종 합의안 목록

        Returns:
            프롬프트 텍스트
        """
        # 각 참여자의 합의안 정리
        proposals_text = ""
        for msg in final_proposals:
            speaker_idx = msg['speaker_idx']
            stance = debate_setup.stances[speaker_idx]
            proposals_text += f"\n[{stance.title}의 제안]\n{msg['content']}\n"

        return f"""다음은 "{debate_setup.topic}" 주제에 대한 {len(debate_setup.stances)}명의 참여자들이 토론 후 제시한 최종 합의안입니다.

{proposals_text}

**당신의 역할:**
위의 모든 합의안을 종합하여 하나의 통합된 최종 결론을 작성해주세요.

**작성 요구사항:**
1. 모든 참여자의 핵심 제안을 균형있게 반영
2. 공통된 합의점을 명확히 제시
3. 구체적이고 실행 가능한 결론으로 작성
4. 각 참여자의 우려사항이나 조건을 적절히 포함
5. 체계적이고 논리적인 구조로 정리
6. 1000자 이내로 간결하게 작성
7. 요구사항에 없는 내용은 작성하지 않는다.

**형식:**
- 마크다운 형식 사용
- 섹션 구분 (## 헤더 사용)
- 필요시 불릿 포인트나 번호 목록 활용

통합된 최종 결론만 출력하세요 (다른 설명 없이)."""
