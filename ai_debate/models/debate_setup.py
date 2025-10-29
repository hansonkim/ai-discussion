"""토론 설정 데이터 클래스"""

from dataclasses import dataclass, field
from typing import List
from ai_debate.models.ai_model import AIModel


@dataclass
class Stance:
    """참여자 입장 정보

    Attributes:
        title: 참여자 제목 (예: "찬성파", "반대파")
        position: 핵심 주장 또는 역할
        emoji: 표시할 이모지 (예: "🔵", "🟡")
        ai_model: 사용할 AI 모델
        agree_or_disagree: 찬반 구분 ("찬성", "반대", "중립")
    """
    title: str
    position: str
    emoji: str
    ai_model: AIModel
    agree_or_disagree: str = "중립"


@dataclass
class DebateSetup:
    """토론 전체 설정

    Attributes:
        topic: 토론 주제
        stances: 참여자 입장 리스트
        char_limit: 답변 글자 수 제한
        num_rounds: 최대 라운드 수
    """
    topic: str
    stances: List[Stance]
    char_limit: int = 500
    num_rounds: int = 5
