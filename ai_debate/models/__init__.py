"""데이터 모델 패키지"""

from ai_debate.models.ai_model import AIModel
from ai_debate.models.debate_setup import Stance, DebateSetup

__all__ = ["AIModel", "Stance", "DebateSetup"]
