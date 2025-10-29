"""사용자 입력 처리"""

from typing import Dict
from ai_debate.models.ai_model import AIModel
from ai_debate.models.debate_setup import Stance, DebateSetup
from ai_debate.services.ai_client import AIClient
from ai_debate.services.prompt_generator import PromptGenerator
from ai_debate.config.constants import (
    DEFAULT_CHAR_LIMIT,
    DEFAULT_NUM_ROUNDS,
    DEFAULT_NUM_PARTICIPANTS,
    MIN_PARTICIPANTS,
    MAX_PARTICIPANTS,
    MIN_ROUNDS,
    STANCE_EMOJIS
)
from ai_debate.exceptions import InvalidInputError


class InputHandler:
    """사용자 입력 처리 클래스"""

    def __init__(self):
        """입력 핸들러 초기화"""
        pass

    def get_topic(self, default: str = None) -> str:
        """토론 주제 입력

        Args:
            default: 기본값 (명령줄 인자 등)

        Returns:
            토론 주제
        """
        if default:
            return default

        while True:
            topic = input("\n토론 주제를 입력하세요: ").strip()
            if topic:
                return topic
            print("⚠️  주제를 입력해주세요.")

    def get_num_participants(
        self,
        default: int = DEFAULT_NUM_PARTICIPANTS
    ) -> int:
        """참여자 수 입력

        Args:
            default: 기본값

        Returns:
            참여자 수
        """
        prompt = f"토론 참여자 수 [기본: {default}, 최소: {MIN_PARTICIPANTS}, 최대: {MAX_PARTICIPANTS}]: "
        input_str = input(prompt).strip()

        if not input_str:
            return default

        try:
            num = int(input_str)
            if num < MIN_PARTICIPANTS:
                print(f"⚠️  참여자 수는 최소 {MIN_PARTICIPANTS}명 이상이어야 합니다. 기본값({default}) 사용")
                return default
            elif num > MAX_PARTICIPANTS:
                print(f"⚠️  참여자 수는 최대 {MAX_PARTICIPANTS}명까지 가능합니다. {MAX_PARTICIPANTS}명으로 설정")
                return MAX_PARTICIPANTS
            return num
        except ValueError:
            print(f"⚠️  올바른 숫자를 입력하세요. 기본값({default}) 사용")
            return default

    def get_char_limit(self, default: int = DEFAULT_CHAR_LIMIT) -> int:
        """글자 수 제한 입력

        Args:
            default: 기본값

        Returns:
            글자 수 제한
        """
        input_str = input(f"답변 글자 수 제한 [기본: {default}]: ").strip()

        if not input_str:
            return default

        try:
            return int(input_str)
        except ValueError:
            print(f"⚠️  올바른 숫자를 입력하세요. 기본값({default}) 사용")
            return default

    def get_num_rounds(
        self,
        default: int = DEFAULT_NUM_ROUNDS
    ) -> int:
        """라운드 수 입력

        Args:
            default: 기본값

        Returns:
            라운드 수
        """
        input_str = input(f"최대 토론 라운드 횟수 [기본: {default}]: ").strip()

        if not input_str:
            return default

        try:
            num = int(input_str)
            if num < MIN_ROUNDS:
                print(f"⚠️  최소 {MIN_ROUNDS}라운드 이상 필요합니다. {MIN_ROUNDS}로 설정")
                return MIN_ROUNDS
            return num
        except ValueError:
            print(f"⚠️  올바른 숫자를 입력하세요. 기본값({default}) 사용")
            return default

    def get_stance_position(self, participant_num: int) -> str:
        """참여자 입장 입력

        Args:
            participant_num: 참여자 번호 (1부터 시작)

        Returns:
            핵심 주장 또는 역할
        """
        while True:
            position = input(f"\n핵심주장 또는 역할: ").strip()
            if position:
                return position
            print("⚠️  핵심주장 또는 역할을 입력해주세요.")

    def select_model(
        self,
        available_models: Dict[str, AIModel],
        stance_title: str
    ) -> AIModel:
        """AI 모델 선택

        Args:
            available_models: 사용 가능한 AI 모델 딕셔너리
            stance_title: 참여자 제목

        Returns:
            선택된 AI 모델
        """
        print(f"\n{'='*60}")
        print(f"🤖 {stance_title}의 AI 선택")
        print(f"{'='*60}\n")

        models = list(available_models.keys())
        for i, key in enumerate(models, 1):
            model = available_models[key]
            print(f"{i}. {model.display_name}")

        print()

        while True:
            try:
                choice = input(f"AI를 선택하세요 (1-{len(models)}) [기본: 1]: ").strip()

                if not choice:
                    choice = "1"

                choice_num = int(choice)
                if 1 <= choice_num <= len(models):
                    selected_key = models[choice_num - 1]
                    selected_model = available_models[selected_key]
                    print(f"✅ {selected_model.display_name} 선택됨\n")
                    return selected_model
                else:
                    print(f"❌ 1부터 {len(models)} 사이의 숫자를 입력하세요.")
            except ValueError:
                print(f"❌ 올바른 숫자를 입력하세요.")
            except KeyboardInterrupt:
                print("\n\n⚠️  기본값 사용")
                return list(available_models.values())[0]

    def create_stances_from_user_input(
        self,
        topic: str,
        num_participants: int,
        available_models: Dict[str, AIModel],
        ai_client: AIClient,
        prompt_generator: PromptGenerator
    ) -> list[Stance]:
        """사용자 입력으로 참여자 입장 생성

        Args:
            topic: 토론 주제
            num_participants: 참여자 수
            available_models: 사용 가능한 AI 모델
            ai_client: AI 클라이언트
            prompt_generator: 프롬프트 생성기

        Returns:
            참여자 입장 리스트
        """
        print(f"\n👥 각 참여자의 핵심 주장을 입력하고 AI 모델을 선택해주세요.")
        print("\n💡 역할/제목은 자동으로 생성됩니다.\n")

        stances = []

        for i in range(num_participants):
            print(f"{'='*60}")
            print(f"📍 참여자 {i+1}/{num_participants}")
            print(f"{'='*60}")

            # 핵심 주장 또는 역할 입력
            position = self.get_stance_position(i + 1)

            # 제목 자동 생성
            print("\n🤖 제목 생성 중...")
            title = self._generate_title(
                topic,
                position,
                ai_client,
                prompt_generator,
                list(available_models.values())[0]
            )
            print(f"✅ 제목: {title}\n")

            # AI 모델 선택
            ai_model = self.select_model(available_models, title)

            # 이모지 할당
            emoji = STANCE_EMOJIS[i % len(STANCE_EMOJIS)]

            # Stance 생성
            stance = Stance(
                title=title,
                position=position,
                emoji=emoji,
                ai_model=ai_model,
                agree_or_disagree="중립"  # 기본값
            )
            stances.append(stance)

            print(f"✅ 참여자 {i+1} 설정 완료: {emoji} {title} ({ai_model.display_name})\n")

        # 발언 순서 최적화 (반대 입장자 우선)
        stances = self._optimize_speaker_order(stances)

        return stances

    def _generate_title(
        self,
        topic: str,
        position: str,
        ai_client: AIClient,
        prompt_generator: PromptGenerator,
        model: AIModel
    ) -> str:
        """제목 생성 (내부 메서드)

        Args:
            topic: 토론 주제
            position: 핵심 주장 또는 역할
            ai_client: AI 클라이언트
            prompt_generator: 프롬프트 생성기
            model: 사용할 AI 모델

        Returns:
            생성된 제목
        """
        prompt = prompt_generator.generate_title_prompt(topic, position)

        try:
            title = ai_client.call_ai(prompt, model)
            # 너무 긴 제목은 잘라냄
            return title[:30]
        except Exception as e:
            print(f"⚠️  제목 생성 실패: {e}")
            return f"참여자"

    def _optimize_speaker_order(self, stances: list[Stance]) -> list[Stance]:
        """발언 순서 최적화 (반대 입장자 우선)

        Args:
            stances: 참여자 입장 리스트

        Returns:
            최적화된 입장 리스트
        """
        # 찬성/반대/중립 구분
        disagree = []
        agree = []
        neutral = []

        for stance in stances:
            position_lower = stance.position.lower()
            if any(word in position_lower for word in ["반대", "거부", "부정", "문제"]):
                stance.agree_or_disagree = "반대"
                disagree.append(stance)
            elif any(word in position_lower for word in ["찬성", "긍정", "동의", "지지"]):
                stance.agree_or_disagree = "찬성"
                agree.append(stance)
            else:
                stance.agree_or_disagree = "중립"
                neutral.append(stance)

        # 반대 → 찬성 → 중립 순서
        return disagree + agree + neutral
