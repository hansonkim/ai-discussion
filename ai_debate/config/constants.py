"""설정 상수 및 기본값"""

from pathlib import Path
from typing import Dict, List
from ai_debate.models.ai_model import AIModel


# 지원하는 AI 모델 정의
ALL_AI_MODELS: Dict[str, AIModel] = {
    "claude": AIModel(
        name="Claude",
        command=["claude", "-p"],
        display_name="Claude (Anthropic)",
        test_command=["claude", "--version"]
    ),
    "openai": AIModel(
        name="OpenAI",
        command=["codex", "exec", "--skip-git-repo-check"],
        display_name="OpenAI GPT (Codex)",
        test_command=["codex", "--version"]
    ),
    "gemini": AIModel(
        name="Gemini",
        command=["gemini", "-p"],
        display_name="Gemini (Google)",
        test_command=["gemini", "--version"]
    ),
    "grok": AIModel(
        name="Grok",
        command=["grok", "-p"],
        display_name="Grok (xAI)",
        test_command=["grok", "--version"]
    )
}

# 기본 설정값
DEFAULT_CHAR_LIMIT = 500
DEFAULT_NUM_ROUNDS = 5
DEFAULT_NUM_PARTICIPANTS = 2
MIN_PARTICIPANTS = 2
MAX_PARTICIPANTS = 10
MIN_ROUNDS = 2

# 파일 경로
CACHE_FILE = Path(".ai_models_cache.json")

# 입장 이모지
STANCE_EMOJIS: List[str] = [
    "🔵", "🟡", "🟢", "🔴", "🟣",
    "🟠", "⚪", "⚫", "🟤", "🔷"
]

# 타임아웃 설정 (초)
AI_CALL_TIMEOUT = 300  # 5분
MODEL_CHECK_TIMEOUT = 1.0  # 1초

# 글자 수 제한 비율
MIN_CHAR_RATIO = 0.25  # 최소 글자 수 = char_limit * 0.25
