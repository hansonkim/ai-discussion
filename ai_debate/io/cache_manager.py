"""캐시 관리 서비스"""

import json
from pathlib import Path
from typing import Optional, List
from ai_debate.exceptions import FileOperationError


class CacheManager:
    """AI 모델 가용성 캐시 관리

    Attributes:
        cache_file: 캐시 파일 경로
    """

    def __init__(self, cache_file: Path = Path(".ai_models_cache.json")):
        """
        Args:
            cache_file: 캐시 파일 경로 (기본: .ai_models_cache.json)
        """
        self.cache_file = cache_file

    def load_cached_models(self) -> Optional[List[str]]:
        """캐시 파일에서 사용 가능한 모델 목록 로드

        Returns:
            캐시된 모델 키 리스트 또는 None (캐시 없음)
        """
        if not self.cache_file.exists():
            return None

        try:
            with open(self.cache_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
                return data.get('available_models', [])
        except Exception as e:
            # 캐시 파일 읽기 실패 시 None 반환 (재확인 유도)
            print(f"⚠️  캐시 파일 읽기 실패: {e}")
            return None

    def save_cached_models(self, available_keys: List[str]) -> None:
        """사용 가능한 모델 목록을 캐시 파일에 저장

        Args:
            available_keys: 사용 가능한 모델 키 리스트

        Raises:
            FileOperationError: 캐시 저장 실패 시
        """
        try:
            import time
            data = {
                'available_models': available_keys,
                'timestamp': time.strftime('%Y-%m-%d %H:%M:%S')
            }
            with open(self.cache_file, 'w', encoding='utf-8') as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
        except Exception as e:
            raise FileOperationError(f"캐시 파일 저장 실패: {e}")

    def clear_cache(self) -> None:
        """캐시 파일 삭제"""
        if self.cache_file.exists():
            try:
                self.cache_file.unlink()
            except Exception as e:
                raise FileOperationError(f"캐시 파일 삭제 실패: {e}")
