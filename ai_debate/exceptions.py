"""커스텀 예외 정의"""


class AIDebateException(Exception):
    """AI 토론 시스템 기본 예외"""
    pass


class AIModelNotFoundError(AIDebateException):
    """AI 모델 CLI를 찾을 수 없음"""
    pass


class AIResponseError(AIDebateException):
    """AI 응답 오류"""
    pass


class AITimeoutError(AIResponseError):
    """AI 응답 타임아웃"""
    pass


class NoAvailableModelsError(AIDebateException):
    """사용 가능한 AI 모델이 없음"""
    pass


class InvalidInputError(AIDebateException):
    """유효하지 않은 입력"""
    pass


class FileOperationError(AIDebateException):
    """파일 작업 오류"""
    pass
