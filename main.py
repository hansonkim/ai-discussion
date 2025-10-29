"""AI 토론 시스템 진입점"""

import sys
from pathlib import Path

from ai_debate.models.debate_setup import DebateSetup
from ai_debate.services.model_manager import ModelManager
from ai_debate.services.ai_client import AIClient
from ai_debate.services.prompt_generator import PromptGenerator
from ai_debate.services.debate_engine import DebateEngine
from ai_debate.io.file_manager import FileManager
from ai_debate.io.cache_manager import CacheManager
from ai_debate.ui.console import Console
from ai_debate.ui.input_handler import InputHandler
from ai_debate.config.constants import CACHE_FILE
from ai_debate.exceptions import (
    AIDebateException,
    NoAvailableModelsError
)


def main():
    """메인 함수"""
    console = Console()
    console.print_header("🎯 AI 토론 시스템")

    print("\n여러 AI 모델을 사용하여 상반된 입장으로 토론하고 합의점을 찾습니다.")
    print("지원 모델: Claude, OpenAI, Gemini, Grok\n")

    try:
        # 의존성 초기화
        cache_manager = CacheManager(CACHE_FILE)
        model_manager = ModelManager(cache_manager)
        ai_client = AIClient()
        prompt_generator = PromptGenerator()
        file_manager = FileManager()
        debate_engine = DebateEngine(ai_client, prompt_generator, file_manager)
        input_handler = InputHandler()

        # AI 모델 가용성 확인 및 초기화
        model_manager.initialize_models()

        # 사용자 입력
        console.print_section("⚙️  토론 설정")

        # 명령줄 인자로 주제 전달 가능
        default_topic = sys.argv[1] if len(sys.argv) > 1 else None

        # 설정 입력
        num_participants = input_handler.get_num_participants()
        char_limit = input_handler.get_char_limit()
        num_rounds = input_handler.get_num_rounds()

        console.print_success(
            f"설정 완료: 참여자={num_participants}명, "
            f"글자 수 제한={char_limit}자, "
            f"최대 라운드={num_rounds}회"
        )
        console.print_info("모든 참여자가 합의하면 최대 라운드 전에 조기 종료될 수 있습니다.\n")

        # 토론 주제 입력
        topic = input_handler.get_topic(default_topic)

        # 참여자 입장 생성 (사용자 입력 기반)
        stances = input_handler.create_stances_from_user_input(
            topic,
            num_participants,
            model_manager.get_available_models(),
            ai_client,
            prompt_generator
        )

        # 토론 설정 객체 생성
        debate_setup = DebateSetup(
            topic=topic,
            stances=stances,
            char_limit=char_limit,
            num_rounds=num_rounds
        )

        # 파일명 키워드 생성
        print("📝 파일명 키워드 생성 중...")
        keyword_prompt = prompt_generator.generate_filename_keyword_prompt(topic)
        subject_slug = ai_client.call_ai(keyword_prompt, stances[0].ai_model)

        # JSON 파싱 (마크다운 코드블록 제거)
        if "```" in subject_slug:
            import re
            json_match = re.search(r'```(?:json)?\s*\n?(.*?)\n?```', subject_slug, re.DOTALL)
            if json_match:
                subject_slug = json_match.group(1).strip()

        # 특수문자 제거
        subject_slug = subject_slug.strip().strip('"').strip("'")
        if not subject_slug or len(subject_slug) > 50:
            subject_slug = "debate"

        console.print_success(f"파일명: {subject_slug}-{{timestamp}}.md\n")

        # 토론 진행
        console.print_header("💬 토론 시작")
        debate_engine.conduct_debate(debate_setup, subject_slug)

        console.print_success("토론이 완료되었습니다!")

    except KeyboardInterrupt:
        console.print_warning("\n사용자가 토론을 중단했습니다.")
        sys.exit(0)
    except NoAvailableModelsError as e:
        console.print_error(str(e))
        sys.exit(1)
    except AIDebateException as e:
        console.print_error(f"토론 중 오류 발생: {e}")
        sys.exit(1)
    except Exception as e:
        console.print_error(f"예기치 않은 오류: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()
