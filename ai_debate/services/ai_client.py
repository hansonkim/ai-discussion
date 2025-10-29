"""AI CLI 호출 서비스"""

import subprocess
from ai_debate.models.ai_model import AIModel
from ai_debate.config.constants import AI_CALL_TIMEOUT
from ai_debate.exceptions import AIResponseError, AITimeoutError, AIModelNotFoundError


class AIClient:
    """AI CLI를 통한 AI 모델 호출 서비스"""

    def __init__(self, timeout: int = AI_CALL_TIMEOUT):
        """
        Args:
            timeout: AI 호출 타임아웃 (초)
        """
        self.timeout = timeout

    def call_ai(self, prompt: str, ai_model: AIModel) -> str:
        """AI CLI를 호출하여 응답 받기

        Args:
            prompt: AI에게 전달할 프롬프트
            ai_model: 사용할 AI 모델 정보

        Returns:
            AI의 응답 텍스트

        Raises:
            AIModelNotFoundError: AI CLI를 찾을 수 없음
            AITimeoutError: 응답 타임아웃
            AIResponseError: 기타 AI 응답 오류
        """
        try:
            result = subprocess.run(
                ai_model.command,
                input=prompt,
                capture_output=True,
                text=True,
                timeout=self.timeout,
                encoding='utf-8'
            )

            if result.returncode != 0:
                error_msg = result.stderr.strip() if result.stderr else "알 수 없는 오류"
                raise AIResponseError(
                    f"{ai_model.name} 응답 오류 (코드 {result.returncode}): {error_msg}"
                )

            response = result.stdout.strip()

            if not response:
                raise AIResponseError(f"{ai_model.name}로부터 빈 응답을 받았습니다")

            return response

        except FileNotFoundError:
            raise AIModelNotFoundError(
                f"{ai_model.name} CLI를 찾을 수 없습니다. "
                f"명령어: {' '.join(ai_model.command)}"
            )
        except subprocess.TimeoutExpired:
            raise AITimeoutError(
                f"{ai_model.name} 응답 타임아웃 ({self.timeout}초 초과)"
            )
        except (AIModelNotFoundError, AITimeoutError, AIResponseError):
            # 이미 처리된 예외는 그대로 전파
            raise
        except Exception as e:
            raise AIResponseError(f"{ai_model.name} 호출 중 예외 발생: {e}")

    def call_ai_with_retry(
        self,
        prompt: str,
        ai_model: AIModel,
        max_retries: int = 3
    ) -> str:
        """재시도 로직을 포함한 AI 호출

        Args:
            prompt: AI에게 전달할 프롬프트
            ai_model: 사용할 AI 모델 정보
            max_retries: 최대 재시도 횟수

        Returns:
            AI의 응답 텍스트

        Raises:
            AIResponseError: 모든 재시도 실패 시
        """
        last_exception = None

        for attempt in range(max_retries):
            try:
                return self.call_ai(prompt, ai_model)
            except AITimeoutError as e:
                last_exception = e
                if attempt < max_retries - 1:
                    print(f"⚠️  타임아웃 발생, 재시도 중... ({attempt + 1}/{max_retries})")
                    continue
            except AIResponseError as e:
                last_exception = e
                if attempt < max_retries - 1:
                    print(f"⚠️  오류 발생, 재시도 중... ({attempt + 1}/{max_retries})")
                    continue
            except AIModelNotFoundError:
                # CLI가 없는 경우는 재시도해도 소용없음
                raise

        # 모든 재시도 실패
        raise AIResponseError(
            f"AI 호출 실패 (총 {max_retries}회 시도): {last_exception}"
        )
