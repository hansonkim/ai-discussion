"""AI 모델 관리 서비스"""

import subprocess
from typing import Dict
from ai_debate.models.ai_model import AIModel
from ai_debate.io.cache_manager import CacheManager
from ai_debate.config.constants import ALL_AI_MODELS, MODEL_CHECK_TIMEOUT
from ai_debate.exceptions import NoAvailableModelsError


class ModelManager:
    """AI 모델 가용성 확인 및 관리

    Attributes:
        cache_manager: 캐시 관리자
        available_models: 사용 가능한 AI 모델 딕셔너리
    """

    def __init__(self, cache_manager: CacheManager):
        """
        Args:
            cache_manager: 캐시 관리자 인스턴스
        """
        self.cache_manager = cache_manager
        self.available_models: Dict[str, AIModel] = {}

    def check_model_availability(
        self,
        model_key: str,
        model: AIModel
    ) -> bool:
        """특정 AI 모델의 CLI가 사용 가능한지 확인

        Args:
            model_key: 모델 키 (예: "claude")
            model: AI 모델 정보

        Returns:
            사용 가능하면 True, 아니면 False
        """
        # 1단계: CLI 설치 확인 (빠른 체크)
        test_cmd = model.test_command or model.command[:1] + ["--version"]

        try:
            result = subprocess.run(
                test_cmd,
                capture_output=True,
                text=True,
                timeout=MODEL_CHECK_TIMEOUT * 2,
                encoding='utf-8'
            )
            # CLI가 없거나 심각한 오류면 즉시 False
            if result.returncode not in [0, 1]:
                return False
        except FileNotFoundError:
            return False
        except subprocess.TimeoutExpired:
            # 타임아웃은 실행은 되지만 응답이 느린 경우
            pass
        except Exception:
            return False

        # 2단계: 실제 API 호출 테스트 (간단한 호출로 크레딧/인증 확인)
        try:
            test_prompt = "ok"
            result = subprocess.run(
                model.command + [test_prompt],
                capture_output=True,
                text=True,
                timeout=10.0,  # AI API 호출은 충분한 시간 필요 (10초)
                encoding='utf-8'
            )

            # stdout과 stderr 모두에서 명확한 에러만 확인
            output = (result.stdout + result.stderr).lower()

            # 크레딧/인증 관련 명확한 에러 키워드
            critical_errors = [
                "doesn't have any credits",
                'purchase credits',
                'no credits',
                'credit balance',
                'billing',
                'payment required'
            ]

            # 명확한 크레딧/결제 에러가 있으면 사용 불가
            if any(error in output for error in critical_errors):
                return False

            # returncode 0이면 성공
            if result.returncode == 0:
                return True

            # 그 외의 경우는 CLI가 설치되어 있으므로 사용 가능으로 간주
            # (API 키 설정 등은 사용자가 실제 사용 시 해결할 문제)
            return True

        except subprocess.TimeoutExpired:
            # 타임아웃 = API가 느리지만 동작함 (사용 가능)
            return True
        except Exception:
            # 기타 에러는 CLI가 설치되어 있으므로 사용 가능으로 간주
            return True

    def initialize_models(self, force_refresh: bool = False) -> None:
        """사용 가능한 AI 모델 확인 및 초기화

        Args:
            force_refresh: True면 캐시 무시하고 강제로 재확인

        Raises:
            NoAvailableModelsError: 사용 가능한 모델이 없을 경우
        """
        # 캐시 확인 (force_refresh가 아닐 때만)
        if not force_refresh:
            cached_keys = self.cache_manager.load_cached_models()
            if cached_keys:
                print("✅ 캐시된 AI 모델 정보 사용")
                self.available_models = {
                    key: ALL_AI_MODELS[key]
                    for key in cached_keys
                    if key in ALL_AI_MODELS
                }
                if self.available_models:
                    model_names = ', '.join(m.display_name for m in self.available_models.values())
                    print(f"🤖 사용 가능한 AI 모델: {model_names}\n")
                    return
                else:
                    print("⚠️  캐시된 모델이 유효하지 않습니다. 재확인합니다...\n")

        # AI 모델 가용성 확인
        print("🔍 AI 모델 가용성 확인 중...")
        print("-" * 60)

        # 초기화 (이전 데이터 제거)
        self.available_models.clear()
        available_keys = []

        for model_key, model in ALL_AI_MODELS.items():
            print(f"  - {model.display_name}...", end=" ", flush=True)

            if self.check_model_availability(model_key, model):
                self.available_models[model_key] = model
                available_keys.append(model_key)
                print("✅ 사용 가능")
            else:
                print("❌ 사용 불가")

        print("-" * 60)

        # 사용 가능한 모델이 없으면 에러
        if not self.available_models:
            error_msg = self._get_installation_guide()
            raise NoAvailableModelsError(error_msg)

        # 캐시 저장
        self.cache_manager.save_cached_models(available_keys)

        print(f"\n✅ {len(self.available_models)}개의 AI 모델 사용 가능")
        model_names = ', '.join(m.display_name for m in self.available_models.values())
        print(f"🤖 사용 가능한 모델: {model_names}\n")

    def get_available_models(self) -> Dict[str, AIModel]:
        """사용 가능한 모델 반환

        Returns:
            사용 가능한 AI 모델 딕셔너리
        """
        return self.available_models

    @staticmethod
    def _get_installation_guide() -> str:
        """AI CLI 설치 안내 메시지 생성

        Returns:
            설치 안내 메시지
        """
        return """
❌ 사용 가능한 AI 모델이 없습니다!

다음 중 하나 이상의 AI CLI를 설치해주세요:

1. Claude (Anthropic)
   - 설치: npm install -g @anthropic-ai/claude-cli
   - 문서: https://docs.anthropic.com/claude/docs/claude-cli

2. OpenAI GPT (Codex)
   - 설치: npm install -g @openai/codex-cli
   - 문서: https://platform.openai.com/docs/codex

3. Gemini (Google)
   - 설치: pip install google-generativeai
   - 문서: https://ai.google.dev/docs

4. Grok (xAI)
   - 설치: pip install grok-cli
   - 문서: https://x.ai/docs

💡 캐시를 강제로 갱신하려면 '.ai_models_cache.json' 파일을 삭제하세요.
"""
