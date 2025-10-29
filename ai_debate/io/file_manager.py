"""파일 관리 서비스"""

import time
from pathlib import Path
from typing import Dict, List, Optional
from ai_debate.models.debate_setup import DebateSetup
from ai_debate.exceptions import FileOperationError


class FileManager:
    """마크다운 파일 생성 및 관리

    Attributes:
        base_dir: 파일을 저장할 기본 디렉토리
        current_debate_file: 현재 토론 파일 경로
        current_round: 현재 라운드 번호
        timestamp: 파일명에 사용할 타임스탬프
    """

    def __init__(self, base_dir: Path = Path(".")):
        """
        Args:
            base_dir: 파일 저장 기본 디렉토리
        """
        self.base_dir = base_dir
        self.current_debate_file: Optional[Path] = None
        self.current_round: int = 0
        self.timestamp: Optional[str] = None

    def initialize_debate_file(
        self,
        debate_setup: DebateSetup,
        subject_slug: str
    ) -> Path:
        """토론 파일 초기화 및 헤더 작성

        Args:
            debate_setup: 토론 설정 정보
            subject_slug: 파일명에 사용할 주제 키워드

        Returns:
            생성된 파일 경로

        Raises:
            FileOperationError: 파일 생성 실패 시
        """
        # 타임스탬프 생성 및 저장
        self.timestamp = time.strftime("%Y%m%d-%H%M%S")

        filename = f"{subject_slug}-{self.timestamp}.md"
        filepath = self.base_dir / filename
        self.current_debate_file = filepath

        try:
            with open(filepath, 'w', encoding='utf-8') as f:
                # 마크다운 헤더
                f.write("# AI 토론 기록\n\n")
                f.write(f"**생성 일시**: {time.strftime('%Y년 %m월 %d일 %H:%M:%S')}\n\n")
                f.write(f"**참여자 수**: {len(debate_setup.stances)}명\n\n")
                f.write("---\n\n")

                # 토론 주제 및 입장
                f.write("## 📋 토론 주제\n\n")
                f.write(f"{debate_setup.topic}\n\n")

                # 모든 참여자의 입장 출력
                f.write("## 👥 참여자 입장\n\n")
                for i, stance in enumerate(debate_setup.stances):
                    f.write(f"### {stance.emoji} 참여자 {i+1}: {stance.title} ({stance.ai_model.display_name})\n\n")
                    f.write(f"> {stance.position}\n\n")

                f.write("---\n\n")

                # 토론 내용 섹션 시작
                f.write("## 💬 토론 내용\n\n")

            print(f"💾 토론 기록 파일 생성: {filename}\n")
            return filepath

        except Exception as e:
            raise FileOperationError(f"토론 파일 생성 실패: {e}")

    def append_to_debate_file(
        self,
        debate_setup: DebateSetup,
        speaker_idx: int,
        content: str,
        round_num: int,
        round_name: str
    ) -> None:
        """토론 내용을 실시간으로 파일에 추가

        Args:
            debate_setup: 토론 설정 정보
            speaker_idx: 참여자 인덱스 (0부터 시작)
            content: 발언 내용
            round_num: 라운드 번호
            round_name: 라운드 이름

        Raises:
            FileOperationError: 파일 쓰기 실패 시
        """
        if not self.current_debate_file:
            raise FileOperationError("토론 파일이 초기화되지 않았습니다")

        try:
            with open(self.current_debate_file, 'a', encoding='utf-8') as f:
                # 새 라운드 시작 시 라운드 헤더 추가
                if round_num != self.current_round:
                    self.current_round = round_num
                    f.write(f"### 라운드 {round_num}: {round_name}\n\n")

                stance = debate_setup.stances[speaker_idx]
                f.write(f"#### {stance.emoji} {stance.title} ({stance.ai_model.name})\n\n")
                f.write(f"{content}\n\n")

        except Exception as e:
            raise FileOperationError(f"토론 파일 쓰기 실패: {e}")

    def save_conclusion_file(
        self,
        debate_setup: DebateSetup,
        history: List[Dict],
        subject_slug: str,
        final_round_num: int,
        unified_conclusion: str
    ) -> Path:
        """최종 합의안을 별도 파일로 저장

        Args:
            debate_setup: 토론 설정 정보
            history: 대화 히스토리
            subject_slug: 파일명에 사용할 주제 키워드
            final_round_num: 실제 진행된 마지막 라운드 번호
            unified_conclusion: 통합된 최종 결론

        Returns:
            생성된 결론 파일 경로

        Raises:
            FileOperationError: 파일 생성 실패 시
        """
        # 마지막 라운드(최종 합의안) 내용만 추출
        final_round = [msg for msg in history if msg.get('round') == final_round_num]

        if not final_round:
            print("⚠️  최종 합의안이 없어 conclusion 파일을 생성하지 않습니다.")
            return None

        # 토론 파일과 동일한 타임스탬프 사용
        if not self.timestamp:
            self.timestamp = time.strftime("%Y%m%d-%H%M%S")

        filename = f"{subject_slug}-conclusion-{self.timestamp}.md"
        filepath = self.base_dir / filename

        try:
            with open(filepath, 'w', encoding='utf-8') as f:
                # 마크다운 헤더
                f.write("# 토론 합의안\n\n")
                f.write(f"**생성 일시**: {time.strftime('%Y년 %m월 %d일 %H:%M:%S')}\n\n")
                f.write(f"**참여자 수**: {len(debate_setup.stances)}명\n\n")
                f.write("---\n\n")

                # 토론 주제
                f.write("## 📋 토론 주제\n\n")
                f.write(f"{debate_setup.topic}\n\n")
                f.write("---\n\n")

                # 모든 참여자 입장
                f.write("## 👥 참여자 입장\n\n")
                for i, stance in enumerate(debate_setup.stances):
                    f.write(f"### {stance.emoji} 참여자 {i+1}: {stance.title} ({stance.ai_model.display_name})\n\n")
                    f.write(f"> {stance.position}\n\n")

                f.write("---\n\n")

                # 통합된 최종 결론
                f.write("## 📝 통합 최종 결론\n\n")
                f.write(f"{unified_conclusion}\n\n")
                f.write("---\n\n")

                # 개별 참여자 합의안 (참고용)
                f.write("## 📌 개별 참여자 합의안 (참고)\n\n")

                for msg in final_round:
                    speaker_idx = msg['speaker_idx']
                    stance = debate_setup.stances[speaker_idx]
                    f.write(f"### {stance.emoji} {stance.title} ({stance.ai_model.name})의 제안\n\n")
                    f.write(f"{msg['content']}\n\n")

            print(f"📄 합의안 파일 저장: {filename}")
            return filepath

        except Exception as e:
            raise FileOperationError(f"결론 파일 생성 실패: {e}")
