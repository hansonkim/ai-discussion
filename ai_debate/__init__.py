"""
AI 토론 시스템 패키지

여러 AI 모델을 사용하여 주제에 대해 다자간 토론하고 합의점을 찾는 시스템
"""

__version__ = "2.0.0"
__author__ = "AI Debate System"

# 공개 API
from ai_debate.models.ai_model import AIModel
from ai_debate.models.debate_setup import Stance, DebateSetup
from ai_debate.exceptions import (
    AIDebateException,
    AIModelNotFoundError,
    AIResponseError,
    AITimeoutError,
    NoAvailableModelsError,
    InvalidInputError,
    FileOperationError,
)

__all__ = [
    # Models
    "AIModel",
    "Stance",
    "DebateSetup",
    # Exceptions
    "AIDebateException",
    "AIModelNotFoundError",
    "AIResponseError",
    "AITimeoutError",
    "NoAvailableModelsError",
    "InvalidInputError",
    "FileOperationError",
]
