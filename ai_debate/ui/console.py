"""콘솔 출력 유틸리티"""


class Console:
    """콘솔 출력을 위한 유틸리티 클래스"""

    @staticmethod
    def print_header(title: str, width: int = 60) -> None:
        """헤더 출력

        Args:
            title: 헤더 제목
            width: 가로 폭
        """
        print("\n" + "=" * width)
        print(title)
        print("=" * width)

    @staticmethod
    def print_separator(char: str = "=", width: int = 60) -> None:
        """구분선 출력

        Args:
            char: 구분선 문자
            width: 가로 폭
        """
        print(char * width)

    @staticmethod
    def print_section(title: str, width: int = 60) -> None:
        """섹션 헤더 출력

        Args:
            title: 섹션 제목
            width: 가로 폭
        """
        print(f"\n{title}")
        print("-" * width)

    @staticmethod
    def print_success(message: str) -> None:
        """성공 메시지 출력

        Args:
            message: 메시지 내용
        """
        print(f"✅ {message}")

    @staticmethod
    def print_error(message: str) -> None:
        """에러 메시지 출력

        Args:
            message: 메시지 내용
        """
        print(f"❌ {message}")

    @staticmethod
    def print_warning(message: str) -> None:
        """경고 메시지 출력

        Args:
            message: 메시지 내용
        """
        print(f"⚠️  {message}")

    @staticmethod
    def print_info(message: str) -> None:
        """정보 메시지 출력

        Args:
            message: 메시지 내용
        """
        print(f"ℹ️  {message}")
