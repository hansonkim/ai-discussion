"""AI 모델 데이터 클래스"""

from dataclasses import dataclass
from typing import List, Optional


@dataclass
class AIModel:
    """AI 모델 정보를 저장하는 데이터 클래스

    Attributes:
        name: 간단한 모델 이름 (예: "Claude")
        command: CLI 명령어 리스트 (예: ["claude", "-p"])
        display_name: 화면 표시용 전체 이름 (예: "Claude (Anthropic)")
        test_command: 가용성 테스트용 명령어 (예: ["claude", "--version"])
    """
    name: str
    command: List[str]
    display_name: str
    test_command: Optional[List[str]] = None
