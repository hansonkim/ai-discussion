"""토론 진행 엔진"""

import time
from typing import List, Dict, Tuple
from ai_debate.models.debate_setup import DebateSetup
from ai_debate.services.ai_client import AIClient
from ai_debate.services.prompt_generator import PromptGenerator
from ai_debate.io.file_manager import FileManager
from ai_debate.config.constants import MIN_CHAR_RATIO
from ai_debate.exceptions import AIResponseError


class DebateEngine:
    """토론 진행 핵심 엔진

    Attributes:
        ai_client: AI 호출 클라이언트
        prompt_generator: 프롬프트 생성기
        file_manager: 파일 관리자
    """

    def __init__(
        self,
        ai_client: AIClient,
        prompt_generator: PromptGenerator,
        file_manager: FileManager
    ):
        """
        Args:
            ai_client: AI 호출 클라이언트
            prompt_generator: 프롬프트 생성기
            file_manager: 파일 관리자
        """
        self.ai_client = ai_client
        self.prompt_generator = prompt_generator
        self.file_manager = file_manager

    def conduct_debate(
        self,
        debate_setup: DebateSetup,
        subject_slug: str
    ) -> List[Dict]:
        """전체 토론 진행 (N명 참여)

        Args:
            debate_setup: 토론 설정 정보
            subject_slug: 파일명에 사용할 주제 키워드

        Returns:
            대화 히스토리
        """
        # 토론 파일 초기화
        self.file_manager.initialize_debate_file(debate_setup, subject_slug)

        num_participants = len(debate_setup.stances)
        num_rounds = debate_setup.num_rounds

        # 라운드 생성
        rounds = self._create_rounds(debate_setup.num_rounds, debate_setup.char_limit)

        conversation_history = []
        actual_round_num = 0
        min_rounds = 2  # 최소 진행 라운드
        last_ready_status = None

        for i, round_info in enumerate(rounds):
            actual_round_num = i + 1

            print(f"\n{'='*60}")
            print(f"📍 라운드 {actual_round_num}: {round_info['name']}")
            print(f"{'='*60}\n")

            # 발언 순서 결정
            speaker_order = self._determine_speaker_order(
                num_participants,
                last_ready_status
            )

            # 모든 참여자 발언
            for speaker_idx in speaker_order:
                stance = debate_setup.stances[speaker_idx]
                ai_model = stance.ai_model
                emoji = stance.emoji

                print(f"{emoji} {stance.title} ({ai_model.name}) 발언 중...")
                response = self.get_ai_response(
                    debate_setup,
                    speaker_idx,
                    conversation_history,
                    round_info['instruction']
                )

                print(f"\n{emoji} {stance.title} ({ai_model.name}):")
                print(f"{'-'*60}")
                print(response)
                print(f"{'-'*60}\n")

                conversation_history.append({
                    'speaker_idx': speaker_idx,
                    'content': response,
                    'round': actual_round_num
                })

                # 실시간으로 파일에 저장
                self.file_manager.append_to_debate_file(
                    debate_setup,
                    speaker_idx,
                    response,
                    actual_round_num,
                    round_info['name']
                )

                time.sleep(1)  # API 호출 간격

            # 최종 합의안 라운드면 종료
            if round_info['name'] == '최종 합의안':
                break

            # 합의 준비 확인
            if actual_round_num >= min_rounds and i < len(rounds) - 1:
                all_ready, ready_status = self._check_all_consensus_ready(
                    debate_setup,
                    conversation_history
                )

                if all_ready:
                    # 최종 합의안 라운드로 이동
                    print("🎉 모든 참여자가 합의 준비를 완료했습니다!")
                    print("📝 최종 합의안 도출을 시작합니다.\n")

                    final_round_info = {
                        'name': '최종 합의안',
                        'instruction': f'최종 합의안을 간결하고 구체적으로 제안해주세요. ({debate_setup.char_limit}자 이내)',
                    }

                    # 최종 합의안 라운드 진행
                    for speaker_idx in range(num_participants):
                        stance = debate_setup.stances[speaker_idx]
                        emoji = stance.emoji
                        ai_model = stance.ai_model

                        print(f"{emoji} {stance.title} ({ai_model.name}) 최종 합의안 작성 중...")
                        final_response = self.get_ai_response(
                            debate_setup,
                            speaker_idx,
                            conversation_history,
                            final_round_info['instruction']
                        )

                        print(f"\n{emoji} {stance.title} ({ai_model.name}):")
                        print(f"{'-'*60}")
                        print(final_response)
                        print(f"{'-'*60}\n")

                        conversation_history.append({
                            'speaker_idx': speaker_idx,
                            'content': final_response,
                            'round': actual_round_num + 1
                        })

                        self.file_manager.append_to_debate_file(
                            debate_setup,
                            speaker_idx,
                            final_response,
                            actual_round_num + 1,
                            final_round_info['name']
                        )
                        time.sleep(1)

                    actual_round_num += 1
                    break
                else:
                    last_ready_status = ready_status
                    not_ready_count = sum(1 for r in ready_status if not r)
                    print("➡️  토론을 계속 진행합니다.\n")
                    print(f"ℹ️  다음 라운드에서는 반론 제기자({not_ready_count}명)가 먼저 발언합니다.\n")
                    time.sleep(1)

        # 최종 합의안 통합
        final_round = [msg for msg in conversation_history if msg['round'] == actual_round_num]
        unified_conclusion = self.synthesize_conclusion(debate_setup, final_round)

        # 결론 파일 저장
        self.file_manager.save_conclusion_file(
            debate_setup,
            conversation_history,
            subject_slug,
            actual_round_num,
            unified_conclusion
        )

        print(f"\n{'='*60}")
        print(f"✅ 토론이 완료되었습니다! (총 {actual_round_num}라운드 진행)")
        print(f"📄 토론 전체 기록: {self.file_manager.current_debate_file.name}")
        print(f"{'='*60}\n")

        return conversation_history

    def get_ai_response(
        self,
        debate_setup: DebateSetup,
        speaker_idx: int,
        history: List[Dict],
        instruction: str
    ) -> str:
        """특정 참여자의 AI 응답 생성 (글자 수 검증 포함)

        Args:
            debate_setup: 토론 설정
            speaker_idx: 발언자 인덱스
            history: 대화 히스토리
            instruction: 현재 라운드 지시사항

        Returns:
            AI 응답 텍스트
        """
        stance = debate_setup.stances[speaker_idx]
        ai_model = stance.ai_model

        # 프롬프트 생성
        prompt = self.prompt_generator.generate_debate_prompt(
            debate_setup,
            speaker_idx,
            history,
            instruction
        )

        try:
            response = self.ai_client.call_ai(prompt, ai_model)

            # 글자 수 검증
            char_count = len(response)
            min_limit = int(debate_setup.char_limit * MIN_CHAR_RATIO)

            # 너무 짧은 경우 (1회만 재요청)
            if char_count < min_limit:
                print(f"⚠️  답변이 {char_count}자로 너무 짧습니다. 더 상세한 답변을 요청합니다... (최소 권장: {min_limit}자)")

                expand_prompt = f"""다음 답변이 {char_count}자로 너무 짧습니다.

원본 답변:
{response}

**더 상세하게 작성해주세요:**
- 구체적인 근거와 예시를 추가하세요
- 논점을 더 명확하게 설명하세요
- 목표: {min_limit}-{debate_setup.char_limit}자 정도
- 하지만 {debate_setup.char_limit}자는 넘지 마세요

상세한 답변만 출력하세요 (다른 설명 없이)."""

                response = self.ai_client.call_ai(expand_prompt, ai_model)
                char_count = len(response)
                print(f"✅ 확장 완료: {char_count}자")

            return response

        except Exception as e:
            print(f"❌ AI 응답 생성 중 오류: {e}")
            return "응답 생성 중 오류가 발생했습니다."

    def check_consensus_ready(
        self,
        debate_setup: DebateSetup,
        speaker_idx: int,
        history: List[Dict]
    ) -> bool:
        """특정 참여자의 합의 준비 여부 확인

        Args:
            debate_setup: 토론 설정
            speaker_idx: 발언자 인덱스
            history: 대화 히스토리

        Returns:
            준비 완료 여부 (True/False)
        """
        stance = debate_setup.stances[speaker_idx]
        prompt = self.prompt_generator.generate_consensus_check_prompt(
            debate_setup,
            speaker_idx,
            history
        )

        try:
            response = self.ai_client.call_ai(prompt, stance.ai_model)
            response_upper = response.strip().upper()
            return "YES" in response_upper or "준비" in response
        except Exception as e:
            print(f"⚠️  {stance.title} 합의 확인 실패: {e}")
            return False

    def synthesize_conclusion(
        self,
        debate_setup: DebateSetup,
        final_proposals: List[Dict]
    ) -> str:
        """모든 참여자의 최종 합의안을 종합하여 통합된 결론 생성

        Args:
            debate_setup: 토론 설정
            final_proposals: 최종 합의안 목록

        Returns:
            통합된 최종 결론
        """
        prompt = self.prompt_generator.generate_synthesis_prompt(
            debate_setup,
            final_proposals
        )

        try:
            # 첫 번째 사용 가능한 모델로 통합 결론 생성
            first_model = debate_setup.stances[0].ai_model
            print("🤖 최종 합의안 종합 중...")
            unified_conclusion = self.ai_client.call_ai(prompt, first_model)
            print("✅ 통합 결론 생성 완료\n")
            return unified_conclusion
        except Exception as e:
            print(f"⚠️  통합 결론 생성 실패: {e}")
            return "통합 결론 생성 중 오류가 발생했습니다."

    def _create_rounds(self, num_rounds: int, char_limit: int) -> List[Dict]:
        """라운드 정보 생성

        Args:
            num_rounds: 총 라운드 수
            char_limit: 글자 수 제한

        Returns:
            라운드 정보 리스트
        """
        rounds = []
        for i in range(num_rounds):
            if i == 0 and num_rounds >= 2:
                # 첫 번째 라운드: 초기 주장
                round_info = {
                    'name': '초기 주장',
                    'instruction': f'핵심 주장을 간결하게 제시해주세요. ({char_limit}자 이내)',
                }
            elif i == num_rounds - 1:
                # 마지막 라운드: 최종 합의안
                round_info = {
                    'name': '최종 합의안',
                    'instruction': f'최종 합의안을 간결하고 구체적으로 제안해주세요. ({char_limit}자 이내)',
                }
            else:
                # 중간 라운드: 토론
                round_info = {
                    'name': f'토론 {i}',
                    'instruction': f'다른 참여자의 주장에 대해 반박하거나 질문하고, 타당한 지적은 인정하며, 합의점을 찾아가세요. ({char_limit}자 이내)',
                }
            rounds.append(round_info)
        return rounds

    def _determine_speaker_order(
        self,
        num_participants: int,
        last_ready_status: List[bool] = None
    ) -> List[int]:
        """발언 순서 결정

        Args:
            num_participants: 참여자 수
            last_ready_status: 이전 합의 준비 상태

        Returns:
            발언 순서 (인덱스 리스트)
        """
        if last_ready_status is not None:
            # 준비 안 된 참여자(반론 제기자) 먼저, 준비된 참여자 나중에
            not_ready_indices = [idx for idx, ready in enumerate(last_ready_status) if not ready]
            ready_indices = [idx for idx, ready in enumerate(last_ready_status) if ready]
            speaker_order = not_ready_indices + ready_indices

            if not_ready_indices:
                print(f"💬 반론 제기자 우선 발언: {len(not_ready_indices)}명\n")
        else:
            # 기본 순서
            speaker_order = list(range(num_participants))

        return speaker_order

    def _check_all_consensus_ready(
        self,
        debate_setup: DebateSetup,
        history: List[Dict]
    ) -> Tuple[bool, List[bool]]:
        """모든 참여자의 합의 준비 상태 확인

        Args:
            debate_setup: 토론 설정
            history: 대화 히스토리

        Returns:
            (모두 준비 완료 여부, 개별 준비 상태 리스트)
        """
        print(f"\n{'~'*60}")
        print("🤝 모든 참여자의 합의 준비 상태를 확인합니다...")
        print(f"{'~'*60}\n")

        ready_status = []

        for i, stance in enumerate(debate_setup.stances):
            is_ready = self.check_consensus_ready(debate_setup, i, history)
            ready_status.append(is_ready)

            emoji = stance.emoji
            status_icon = "✅ 준비 완료" if is_ready else "⏳ 토론 계속"
            print(f"{emoji} {stance.title}: {status_icon}")

        print()

        all_ready = all(ready_status)
        return all_ready, ready_status
