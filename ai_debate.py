#!/usr/bin/env python3
"""
AI 토론 시스템
주제를 입력하면 여러 AI 모델이 상반된 입장으로 토론하고 합의점을 찾습니다.

지원 AI 모델:
- Claude (Anthropic)
- OpenAI GPT (Codex)
- Gemini (Google)
- Grok (xAI)

각 입장별로 다른 AI 모델을 선택할 수 있습니다.
"""

import json
import sys
from typing import Dict, List, Optional
import time
import subprocess
import re
from dataclasses import dataclass
from pathlib import Path


@dataclass
class AIModel:
    """AI 모델 정보"""
    name: str           # 표시 이름 (예: "Claude")
    command: List[str]  # CLI 명령어 (예: ["claude", "code", "-p"])
    display_name: str   # 화면 표시용 전체 이름 (예: "Claude (Anthropic)")
    test_command: Optional[List[str]] = None  # 가용성 테스트용 명령어


# 지원하는 AI 모델 정의 (초기 전체 목록)
ALL_AI_MODELS = {
    "claude": AIModel(
        name="Claude",
        command="claude -p".split(),
        display_name="Claude (Anthropic)",
        test_command=["claude", "--version"]
    ),
    "openai": AIModel(
        name="OpenAI",
        command="codex exec --skip-git-repo-check".split(),
        display_name="OpenAI GPT (Codex)",
        test_command=["codex", "--version"]
    ),
    "gemini": AIModel(
        name="Gemini",
        command="gemini -p".split(),
        display_name="Gemini (Google)",
        test_command=["gemini", "--version"]
    ),
    "grok": AIModel(
        name="Grok",
        command="grok -p".split(),
        display_name="Grok (xAI)",
        test_command=["grok", "--version"]
    )
}

# 실제 사용 가능한 AI 모델 (프로그램 시작 시 초기화)
AVAILABLE_AI_MODELS: Dict[str, AIModel] = {}

# 캐시 파일 경로
CACHE_FILE = Path(".ai_models_cache.json")


def check_ai_model_availability(model_key: str, model: AIModel) -> bool:
    """
    특정 AI 모델의 CLI가 사용 가능한지 확인

    Args:
        model_key: 모델 키 (예: "claude")
        model: AI 모델 정보

    Returns:
        사용 가능하면 True, 아니면 False
    """
    test_cmd = model.test_command or model.command[:1] + ["--version"]

    try:
        result = subprocess.run(
            test_cmd,
            capture_output=True,
            text=True,
            timeout=1.0,
            encoding='utf-8'
        )
        # 명령어가 실행되고 심각한 오류가 없으면 사용 가능
        return result.returncode in [0, 1]  # 일부 CLI는 --version이 없어 1 반환
    except FileNotFoundError:
        return False
    except subprocess.TimeoutExpired:
        # 타임아웃은 실행은 되지만 응답이 느린 경우
        return True
    except Exception:
        return False


def load_cached_models() -> Optional[List[str]]:
    """
    캐시 파일에서 사용 가능한 모델 목록 로드

    Returns:
        캐시된 모델 키 리스트 또는 None (캐시 없음)
    """
    if not CACHE_FILE.exists():
        return None

    try:
        with open(CACHE_FILE, 'r', encoding='utf-8') as f:
            data = json.load(f)
            return data.get('available_models', [])
    except Exception as e:
        print(f"⚠️  캐시 파일 읽기 실패: {e}")
        return None


def save_cached_models(available_keys: List[str]):
    """
    사용 가능한 모델 목록을 캐시 파일에 저장

    Args:
        available_keys: 사용 가능한 모델 키 리스트
    """
    try:
        data = {
            'available_models': available_keys,
            'timestamp': time.strftime('%Y-%m-%d %H:%M:%S')
        }
        with open(CACHE_FILE, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
    except Exception as e:
        print(f"⚠️  캐시 파일 저장 실패: {e}")


def initialize_available_models(force_refresh: bool = False):
    """
    사용 가능한 AI 모델 확인 및 초기화

    Args:
        force_refresh: True면 캐시 무시하고 강제로 재확인

    Raises:
        SystemExit: 사용 가능한 모델이 없을 경우
    """
    global AVAILABLE_AI_MODELS

    # 캐시 확인 (force_refresh가 아닐 때만)
    if not force_refresh:
        cached_keys = load_cached_models()
        if cached_keys:
            print("✅ 캐시된 AI 모델 정보 사용")
            AVAILABLE_AI_MODELS = {
                key: ALL_AI_MODELS[key]
                for key in cached_keys
                if key in ALL_AI_MODELS
            }
            if AVAILABLE_AI_MODELS:
                print(f"🤖 사용 가능한 AI 모델: {', '.join(m.display_name for m in AVAILABLE_AI_MODELS.values())}\n")
                return
            else:
                print("⚠️  캐시된 모델이 유효하지 않습니다. 재확인합니다...\n")

    # AI 모델 가용성 확인
    print("🔍 AI 모델 가용성 확인 중...")
    print("-" * 60)

    # 초기화 (이전 데이터 제거)
    AVAILABLE_AI_MODELS.clear()
    available_keys = []

    for model_key, model in ALL_AI_MODELS.items():
        print(f"  - {model.display_name}...", end=" ", flush=True)

        if check_ai_model_availability(model_key, model):
            AVAILABLE_AI_MODELS[model_key] = model
            available_keys.append(model_key)
            print("✅ 사용 가능")
        else:
            print("❌ 사용 불가")

    print("-" * 60)

    # 사용 가능한 모델이 없으면 에러
    if not AVAILABLE_AI_MODELS:
        print("\n❌ 사용 가능한 AI 모델이 없습니다!")
        print("\n다음 중 하나 이상의 AI CLI를 설치해주세요:\n")
        print("1. Claude (Anthropic)")
        print("   - 설치: npm install -g @anthropic-ai/claude-cli")
        print("   - 문서: https://docs.anthropic.com/claude/docs/claude-cli\n")
        print("2. OpenAI GPT (Codex)")
        print("   - 설치: npm install -g @openai/codex-cli")
        print("   - 문서: https://platform.openai.com/docs/codex\n")
        print("3. Gemini (Google)")
        print("   - 설치: pip install google-generativeai")
        print("   - 문서: https://ai.google.dev/docs\n")
        print("4. Grok (xAI)")
        print("   - 설치: pip install grok-cli")
        print("   - 문서: https://x.ai/docs\n")
        print("💡 캐시를 강제로 갱신하려면 '.ai_models_cache.json' 파일을 삭제하세요.\n")
        sys.exit(1)

    # 캐시 저장
    save_cached_models(available_keys)

    print(f"\n✅ {len(AVAILABLE_AI_MODELS)}개의 AI 모델 사용 가능")
    print(f"🤖 사용 가능한 모델: {', '.join(m.display_name for m in AVAILABLE_AI_MODELS.values())}\n")


class AIDebateSystem:
    def __init__(self, char_limit: int = 500, num_rounds: int = 5):
        """
        AI 토론 시스템 초기화
        Claude Code CLI를 사용합니다.

        Args:
            char_limit: 답변 글자 수 제한 (기본값: 500)
            num_rounds: 토론 라운드 횟수 (기본값: 5)
        """
        self.conversation_history = []
        self.debate_filename = None
        self.current_round = 0
        self.subject_slug = None
        self.char_limit = char_limit
        self.num_rounds = num_rounds
        self.timestamp = None  # 파일명에 사용할 타임스탬프

    def call_ai(self, prompt: str, ai_model: AIModel) -> str:
        """
        AI CLI를 호출하여 응답 받기

        Args:
            prompt: AI에게 전달할 프롬프트
            ai_model: 사용할 AI 모델

        Returns:
            AI 응답 텍스트
        """
        try:
            # AI CLI 호출 (stdin으로 프롬프트 전달)
            result = subprocess.run(
                ai_model.command,
                input=prompt,
                capture_output=True,
                text=True,
                encoding='utf-8',
                timeout=300  # 5분 타임아웃
            )

            if result.returncode != 0:
                raise Exception(f"{ai_model.name} CLI 오류: {result.stderr}")

            return result.stdout.strip()

        except FileNotFoundError:
            raise Exception(
                f"{ai_model.name} CLI를 찾을 수 없습니다. "
                f"{ai_model.display_name}이(가) 설치되어 있는지 확인해주세요."
            )
        except subprocess.TimeoutExpired:
            raise Exception(f"{ai_model.name} 응답 시간 초과 (5분)")
        except Exception as e:
            raise Exception(f"{ai_model.name} 호출 중 오류: {e}")

    def select_ai_for_stance(self, stance_title: str) -> AIModel:
        """
        특정 입장에 대해 AI 모델 선택

        Args:
            stance_title: 입장 제목

        Returns:
            선택된 AI 모델
        """
        print(f"\n{'='*60}")
        print(f"🤖 {stance_title}의 AI 선택")
        print(f"{'='*60}\n")

        models = list(AVAILABLE_AI_MODELS.keys())
        for i, key in enumerate(models, 1):
            model = AVAILABLE_AI_MODELS[key]
            print(f"{i}. {model.display_name}")

        print()

        while True:
            try:
                choice = input(f"AI를 선택하세요 (1-{len(models)}) [기본: 1]: ").strip()

                if not choice:
                    choice = "1"

                choice_num = int(choice)
                if 1 <= choice_num <= len(models):
                    selected_key = models[choice_num - 1]
                    selected_model = AVAILABLE_AI_MODELS[selected_key]
                    print(f"✅ {selected_model.display_name} 선택됨\n")
                    return selected_model
                else:
                    print(f"❌ 1부터 {len(models)} 사이의 숫자를 입력하세요.")
            except ValueError:
                print(f"❌ 올바른 숫자를 입력하세요.")
            except KeyboardInterrupt:
                print("\n\n⚠️  기본값 사용")
                return list(AVAILABLE_AI_MODELS.values())[0]

    def generate_filename_keyword(self, topic: str) -> str:
        """
        주제를 짧은 영어 키워드로 변환

        Args:
            topic: 토론 주제

        Returns:
            영어 키워드 (3-5개 단어, 하이픈으로 연결)
        """
        prompt = f"""다음 주제를 파일명으로 사용할 수 있는 짧은 영어 키워드로 변환해주세요.

주제: "{topic}"

요구사항:
- 3-5개의 영어 단어로 구성
- 소문자만 사용
- 단어는 하이픈(-)으로 연결
- 특수문자 사용 금지
- 파일명으로 적합하게

예시:
주제: "원격 근무와 사무실 근무 중 어느 것이 더 생산적인가?"
답변: remote-vs-office-productivity

다른 텍스트 없이 키워드만 답변해주세요."""

        try:
            # 파일명 생성은 첫 번째 사용 가능한 모델 사용
            first_model = list(AVAILABLE_AI_MODELS.values())[0]
            keyword = self.call_ai(prompt, first_model)
            # 안전하게 파일명으로 사용 가능하도록 정제
            keyword = re.sub(r'[^\w\-]', '', keyword.lower().strip())
            # 연속된 하이픈 제거
            keyword = re.sub(r'\-+', '-', keyword)
            # 최대 50자로 제한
            return keyword[:50].strip('-')
        except Exception as e:
            print(f"⚠️  키워드 생성 실패, 기본값 사용: {e}")
            # 실패 시 타임스탬프만 사용
            return "debate"

    def generate_title_for_position(self, topic: str, position: str) -> str:
        """
        입장에 기반하여 짧은 제목 생성

        Args:
            topic: 토론 주제
            position: 참여자의 핵심 주장

        Returns:
            생성된 제목 (2-5 단어)
        """
        prompt = f"""다음 토론 주제와 입장을 보고, 이 입장을 대표하는 짧은 제목을 생성해주세요.

토론 주제: {topic}
핵심 주장: {position}

요구사항:
- 2-5 단어로 구성된 짧은 제목
- 입장의 핵심을 명확하게 표현
- 예시: "찬성파", "반대파", "중도파", "신중론자", "급진론자", "현실주의자" 등

다른 설명 없이 제목만 답변해주세요."""

        try:
            # 첫 번째 사용 가능한 모델로 제목 생성
            first_model = list(AVAILABLE_AI_MODELS.values())[0]
            title = self.call_ai(prompt, first_model)
            # 특수문자 제거 및 정리
            title = title.strip().strip('"\'')
            return title[:30]  # 최대 30자로 제한
        except Exception as e:
            print(f"⚠️  제목 생성 실패, 기본값 사용: {e}")
            return "참여자"

    def create_stances_from_user_input(self, topic: str, num_participants: int) -> Dict:
        """
        사용자 입력을 통해 N개의 입장을 생성

        Args:
            topic: 토론 주제
            num_participants: 참여자 수

        Returns:
            토론 설정 정보 (주제, 입장들)
        """
        print(f"\n{'='*60}")
        print(f"📋 토론 주제: {topic}")
        print(f"{'='*60}\n")

        # 입장 레이블 정의 (이모지와 함께)
        stance_emojis = ["🔵", "🟡", "🟢", "🔴", "🟣", "🟠", "⚪", "⚫", "🟤", "🔷"]

        debate_setup = {
            'topic': topic,
            'stances': []
        }

        print("👥 각 참여자의 핵심 주장을 입력하고 AI 모델을 선택해주세요.\n")
        print("💡 역할/제목은 자동으로 생성됩니다.\n")

        # 각 참여자의 정보 입력받기
        for i in range(num_participants):
            print(f"{'='*60}")
            print(f"📍 참여자 {i+1}/{num_participants}")
            print(f"{'='*60}\n")

            # 참여자 입장 입력
            while True:
                position = input("핵심주장 또는 역할: ").strip()
                if position:
                    break
                print("❌ 핵심주장 또는 역할을 입력해주세요.")

            # AI로 제목 생성
            print(f"\n🤖 제목 생성 중...")
            title = self.generate_title_for_position(topic, position)
            print(f"✅ 제목: {title}\n")

            # 입장 정보 저장
            emoji = stance_emojis[i % len(stance_emojis)]
            stance = {
                'title': title,
                'position': position,
                'emoji': emoji
            }

            # 바로 AI 모델 선택
            ai_model = self.select_ai_for_stance(f"{emoji} {title}")
            stance['ai_model'] = ai_model

            debate_setup['stances'].append(stance)
            print(f"✅ 참여자 {i+1} 설정 완료: {emoji} {title} ({ai_model.display_name})\n")

        return debate_setup

    def check_consensus_ready(
        self,
        debate_setup: Dict,
        speaker_idx: int,
        history: List
    ) -> bool:
        """
        합의 준비 여부 확인

        Args:
            debate_setup: 토론 설정 정보
            speaker_idx: 참여자 인덱스 (0부터 시작)
            history: 대화 히스토리

        Returns:
            True면 최종 합의 준비 완료, False면 토론 계속 필요
        """
        stance = debate_setup['stances'][speaker_idx]

        prompt = f"""지금까지의 토론을 검토해주세요.

주제: {debate_setup['topic']}
당신의 입장: {stance['position']}

지금까지의 토론 내용:
"""
        for msg in history:
            speaker_label = "나" if msg['speaker_idx'] == speaker_idx else f"참여자 {msg['speaker_idx']+1}"
            prompt += f"{speaker_label}: {msg['content']}\n\n"

        prompt += f"""
질문: 지금까지의 토론으로 최종 합의안을 도출할 준비가 되었나요?

다음 기준으로 판단해주세요:
- 모든 참여자의 핵심 주장이 충분히 교환되었나?
- 주요 쟁점에 대한 논의가 이루어졌나?
- 합의 가능한 지점이 보이는가?

**중요: 다음 중 정확히 하나만 답변하세요:**
- "YES" (최종 합의 준비 완료)
- "NO" (더 토론이 필요함)

다른 설명 없이 YES 또는 NO만 답변하세요."""

        try:
            ai_model = stance['ai_model']
            response = self.call_ai(prompt, ai_model).strip().upper()

            # YES/NO 추출
            if "YES" in response:
                return True
            elif "NO" in response:
                return False
            else:
                # 명확하지 않으면 계속 토론
                return False

        except Exception as e:
            print(f"⚠️  합의 준비 확인 중 오류: {e}")
            return False

    def get_ai_response(
        self,
        debate_setup: Dict,
        speaker_idx: int,
        history: List,
        instruction: str
    ) -> str:
        """
        특정 입장에서 AI 응답 생성 (글자 수 제한 검증 포함)

        Args:
            debate_setup: 토론 설정 정보
            speaker_idx: 참여자 인덱스 (0부터 시작)
            history: 대화 히스토리
            instruction: 현재 라운드 지시사항

        Returns:
            AI 응답 텍스트
        """
        stance = debate_setup['stances'][speaker_idx]
        num_participants = len(debate_setup['stances'])

        # 다른 참여자들의 입장 요약
        other_stances = []
        for i, s in enumerate(debate_setup['stances']):
            if i != speaker_idx:
                other_stances.append(f"{s['title']}: {s['position']}")

        prompt = f"""당신은 다음 주제에 대한 {num_participants}명의 토론에 참여하고 있습니다:

주제: {debate_setup['topic']}

당신의 이름과 입장: {stance['title']} - {stance['position']}

다른 참여자들의 입장:
{chr(10).join(other_stances)}

토론 규칙:
- 자신의 입장을 강력하게 방어하세요
- 다른 참여자의 주장에 반박할 여지가 있다면 적극적으로 반박하세요
- 상대의 논리적 오류, 근거 부족, 모순점, 과장, 일반화의 오류 등을 날카롭게 지적하세요
- 논리적이고 구체적인 반론과 근거를 제시하세요
- 감정적이거나 인신공격적인 표현은 피하되, 논리적으로는 강하게 반박하세요
- 쉽게 동의하지 말고, 비판적 사고로 상대 주장을 면밀히 검토하세요
- 타당한 지적만 수용하고, 반박 가능한 부분은 절대 놓치지 마세요
- 상대 주장의 약점을 찾아내고, 대안이나 반례를 제시하세요

**답변 길이 가이드:**
- 충분히 상세하고 구체적으로 작성하세요
- 하지만 {self.char_limit}자를 넘지 않도록 노력하세요
- 너무 짧거나 추상적인 답변은 피하세요
- 목표: {self.char_limit // 4}-{self.char_limit}자 정도의 충실한 답변

현재 지시사항: {instruction}

한국어로 자연스럽게 답변해주세요."""

        # 대화 히스토리 추가
        if history:
            prompt += "\n\n지금까지의 토론 내용:\n\n"
            for msg in history:
                if msg['speaker_idx'] == speaker_idx:
                    speaker_label = "나"
                else:
                    other_stance = debate_setup['stances'][msg['speaker_idx']]
                    speaker_label = other_stance['title']
                prompt += f"{speaker_label}: {msg['content']}\n\n"

        try:
            # 해당 입장의 AI 모델 사용
            ai_model = stance['ai_model']
            response = self.call_ai(prompt, ai_model)

            # 글자 수 검증
            char_count = len(response)
            min_limit = self.char_limit // 4

            # 너무 짧은 경우 (1회만 재요청)
            if char_count < min_limit:
                print(f"⚠️  답변이 {char_count}자로 너무 짧습니다. 더 상세한 답변을 요청합니다... (최소 권장: {min_limit}자)")

                expand_prompt = f"""다음 답변이 {char_count}자로 너무 짧습니다.

원본 답변:
{response}

**더 상세하게 작성해주세요:**
- 구체적인 근거와 예시를 추가하세요
- 논점을 더 명확하게 설명하세요
- 목표: {min_limit}-{self.char_limit}자 정도
- 하지만 {self.char_limit}자는 넘지 마세요

상세한 답변만 출력하세요 (다른 설명 없이)."""

                response = self.call_ai(expand_prompt, ai_model)
                char_count = len(response)
                print(f"✅ 확장 완료: {char_count}자")

            return response

        except Exception as e:
            print(f"❌ AI 응답 생성 중 오류: {e}")
            return "응답 생성 중 오류가 발생했습니다."

    def conduct_debate(self, debate_setup: Dict):
        """
        전체 토론 진행 (N명 참여)

        Args:
            debate_setup: 토론 설정 정보
        """
        # 토론 파일 초기화
        self.initialize_debate_file(debate_setup)

        num_participants = len(debate_setup['stances'])

        # 라운드 생성
        rounds = []
        for i in range(self.num_rounds):
            # 첫 번째 라운드: 초기 주장 (2라운드 이상일 때만)
            if i == 0 and self.num_rounds >= 2:
                round_info = {
                    'name': '초기 주장',
                    'instruction': f'핵심 주장을 간결하게 제시해주세요. ({self.char_limit}자 이내)',
                }
            # 마지막 라운드: 최종 합의안
            elif i == self.num_rounds - 1:
                round_info = {
                    'name': '최종 합의안',
                    'instruction': f'최종 합의안을 간결하고 구체적으로 제안해주세요. ({self.char_limit}자 이내)',
                }
            # 중간 라운드: 토론 과정
            else:
                round_info = {
                    'name': f'토론 {i}',
                    'instruction': f'다른 참여자의 주장에 대해 반박하거나 질문하고, 타당한 지적은 인정하며, 합의점을 찾아가세요. ({self.char_limit}자 이내)',
                }

            rounds.append(round_info)

        conversation_history = []
        actual_round_num = 0  # 실제 진행된 라운드 번호
        min_rounds = 2  # 최소 진행 라운드 (초기 주장 + 1회 토론)
        last_ready_status = None  # 이전 라운드의 합의 준비 상태

        for i, round_info in enumerate(rounds):
            actual_round_num = i + 1

            print(f"\n{'='*60}")
            print(f"📍 라운드 {actual_round_num}: {round_info['name']}")
            print(f"{'='*60}\n")

            # 발언 순서 결정: 합의 확인 후라면 반론 제기자 우선
            if last_ready_status is not None:
                # 준비 안 된 참여자(반론 제기자) 먼저, 준비된 참여자 나중에
                not_ready_indices = [idx for idx, ready in enumerate(last_ready_status) if not ready]
                ready_indices = [idx for idx, ready in enumerate(last_ready_status) if ready]
                speaker_order = not_ready_indices + ready_indices

                if not_ready_indices:
                    print(f"💬 반론 제기자 우선 발언: {len(not_ready_indices)}명\n")
            else:
                # 기본 순서 (0부터 순차적)
                speaker_order = list(range(num_participants))

            # 모든 참여자가 정해진 순서대로 발언
            for speaker_idx in speaker_order:
                stance = debate_setup['stances'][speaker_idx]
                ai_model = stance['ai_model']
                emoji = stance['emoji']

                print(f"{emoji} {stance['title']} ({ai_model.name}) 발언 중...")
                response = self.get_ai_response(
                    debate_setup,
                    speaker_idx,
                    conversation_history,
                    round_info['instruction']
                )

                print(f"\n{emoji} {stance['title']} ({ai_model.name}):")
                print(f"{'-'*60}")
                print(response)
                print(f"{'-'*60}\n")

                conversation_history.append({
                    'speaker_idx': speaker_idx,
                    'content': response,
                    'round': actual_round_num
                })

                # 실시간으로 파일에 저장
                self.append_to_debate_file(debate_setup, speaker_idx, response, actual_round_num, round_info['name'])

                time.sleep(1)  # API 호출 간격

            # 최종 합의안 라운드면 종료
            if round_info['name'] == '최종 합의안':
                break

            # 최소 라운드 이후이고, 최대 라운드에 도달하지 않았으면 합의 준비 확인
            if actual_round_num >= min_rounds and i < len(rounds) - 1:
                print(f"\n{'~'*60}")
                print("🤝 모든 참여자의 합의 준비 상태를 확인합니다...")
                print(f"{'~'*60}\n")

                # 모든 참여자의 합의 준비 확인
                ready_status = []
                for speaker_idx in range(num_participants):
                    ready = self.check_consensus_ready(debate_setup, speaker_idx, conversation_history)
                    ready_status.append(ready)
                    stance = debate_setup['stances'][speaker_idx]
                    emoji = stance['emoji']
                    status = "✅ 준비 완료" if ready else "⏳ 토론 계속"
                    print(f"{emoji} {stance['title']}: {status}")

                print()

                # 모두 준비 완료된 경우
                if all(ready_status):
                    print("🎉 모든 참여자가 합의 준비를 완료했습니다!")
                    print("📝 최종 합의안 도출을 시작합니다.\n")
                    time.sleep(1)

                    # 최종 합의안 라운드로 이동
                    actual_round_num += 1
                    final_round_info = {
                        'name': '최종 합의안',
                        'instruction': f'최종 합의안을 간결하고 구체적으로 제안해주세요. ({self.char_limit}자 이내)',
                    }

                    print(f"\n{'='*60}")
                    print(f"📍 라운드 {actual_round_num}: {final_round_info['name']}")
                    print(f"{'='*60}\n")

                    # 모든 참여자가 최종 합의안 제시
                    for speaker_idx in range(num_participants):
                        stance = debate_setup['stances'][speaker_idx]
                        ai_model = stance['ai_model']
                        emoji = stance['emoji']

                        print(f"{emoji} {stance['title']} ({ai_model.name}) 발언 중...")
                        final_response = self.get_ai_response(
                            debate_setup,
                            speaker_idx,
                            conversation_history,
                            final_round_info['instruction']
                        )

                        print(f"\n{emoji} {stance['title']} ({ai_model.name}):")
                        print(f"{'-'*60}")
                        print(final_response)
                        print(f"{'-'*60}\n")

                        conversation_history.append({
                            'speaker_idx': speaker_idx,
                            'content': final_response,
                            'round': actual_round_num
                        })

                        self.append_to_debate_file(debate_setup, speaker_idx, final_response, actual_round_num, final_round_info['name'])
                        time.sleep(1)

                    break
                else:
                    # 다음 라운드를 위해 현재 상태 저장
                    last_ready_status = ready_status
                    print("➡️  토론을 계속 진행합니다.\n")
                    print(f"ℹ️  다음 라운드에서는 반론 제기자({sum(1 for r in ready_status if not r)}명)가 먼저 발언합니다.\n")
                    time.sleep(1)

        # 토론 결과 저장
        self.conversation_history = conversation_history

        # 최종 합의안 별도 파일로 저장 (실제 진행된 마지막 라운드 전달)
        self.save_conclusion_file(debate_setup, conversation_history, self.subject_slug, actual_round_num)

        print(f"\n{'='*60}")
        print(f"✅ 토론이 완료되었습니다! (총 {actual_round_num}라운드 진행)")
        print(f"📄 토론 전체 기록: {self.debate_filename}")
        print(f"{'='*60}\n")

    def initialize_debate_file(self, debate_setup: Dict):
        """
        토론 시작 시 마크다운 파일 생성 및 헤더 작성

        Args:
            debate_setup: 토론 설정 정보
        """
        # 타임스탬프 생성 및 저장 (결론 파일과 동일한 값 사용)
        self.timestamp = time.strftime("%Y%m%d-%H%M%S")

        # AI에게 주제를 짧은 영어 키워드로 변환 요청
        print("📝 파일명 키워드 생성 중...")
        self.subject_slug = self.generate_filename_keyword(debate_setup['topic'])
        print(f"✅ 파일명: {self.subject_slug}-{self.timestamp}.md\n")

        self.debate_filename = f"{self.subject_slug}-{self.timestamp}.md"

        with open(self.debate_filename, 'w', encoding='utf-8') as f:
            # 마크다운 헤더
            f.write(f"# AI 토론 기록\n\n")
            f.write(f"**생성 일시**: {time.strftime('%Y년 %m월 %d일 %H:%M:%S')}\n\n")
            f.write(f"**참여자 수**: {len(debate_setup['stances'])}명\n\n")
            f.write(f"---\n\n")

            # 토론 주제 및 입장
            f.write(f"## 📋 토론 주제\n\n")
            f.write(f"{debate_setup['topic']}\n\n")

            # 모든 참여자의 입장 출력
            f.write(f"## 👥 참여자 입장\n\n")
            for i, stance in enumerate(debate_setup['stances']):
                ai_model = stance['ai_model']
                emoji = stance['emoji']
                f.write(f"### {emoji} 참여자 {i+1}: {stance['title']} ({ai_model.display_name})\n\n")
                f.write(f"> {stance['position']}\n\n")

            f.write(f"---\n\n")

            # 토론 내용 섹션 시작
            f.write(f"## 💬 토론 내용\n\n")

        print(f"💾 토론 기록 파일 생성: {self.debate_filename}\n")

    def append_to_debate_file(self, debate_setup: Dict, speaker_idx: int, content: str, round_num: int, round_name: str):
        """
        토론 내용을 실시간으로 파일에 추가

        Args:
            debate_setup: 토론 설정 정보
            speaker_idx: 참여자 인덱스 (0부터 시작)
            content: 발언 내용
            round_num: 라운드 번호
            round_name: 라운드 이름
        """
        with open(self.debate_filename, 'a', encoding='utf-8') as f:
            # 새 라운드 시작 시 라운드 헤더 추가
            if round_num != self.current_round:
                self.current_round = round_num
                f.write(f"### 라운드 {round_num}: {round_name}\n\n")

            stance = debate_setup['stances'][speaker_idx]
            emoji = stance['emoji']
            ai_model = stance['ai_model']

            f.write(f"#### {emoji} {stance['title']} ({ai_model.name})\n\n")
            f.write(f"{content}\n\n")

    def synthesize_final_conclusion(self, debate_setup: Dict, final_proposals: List[Dict]) -> str:
        """
        모든 참여자의 최종 합의안을 종합하여 통합된 결론 생성

        Args:
            debate_setup: 토론 설정 정보
            final_proposals: 최종 합의안 목록

        Returns:
            통합된 최종 결론
        """
        # 각 참여자의 합의안 정리
        proposals_text = ""
        for msg in final_proposals:
            speaker_idx = msg['speaker_idx']
            stance = debate_setup['stances'][speaker_idx]
            proposals_text += f"\n[{stance['title']}의 제안]\n{msg['content']}\n"

        prompt = f"""다음은 "{debate_setup['topic']}" 주제에 대한 {len(debate_setup['stances'])}명의 참여자들이 토론 후 제시한 최종 합의안입니다.

{proposals_text}

**당신의 역할:**
위의 모든 합의안을 종합하여 하나의 통합된 최종 결론을 작성해주세요.

**작성 요구사항:**
1. 모든 참여자의 핵심 제안을 균형있게 반영
2. 공통된 합의점을 명확히 제시
3. 구체적이고 실행 가능한 결론으로 작성
4. 각 참여자의 우려사항이나 조건을 적절히 포함
5. 체계적이고 논리적인 구조로 정리
6. 1000자 이내로 간결하게 작성

**형식:**
- 마크다운 형식 사용
- 섹션 구분 (## 헤더 사용)
- 필요시 불릿 포인트나 번호 목록 활용

통합된 최종 결론만 출력하세요 (다른 설명 없이)."""

        try:
            # 첫 번째 사용 가능한 모델로 통합 결론 생성
            first_model = list(AVAILABLE_AI_MODELS.values())[0]
            print("🤖 최종 합의안 종합 중...")
            unified_conclusion = self.call_ai(prompt, first_model)
            print("✅ 통합 결론 생성 완료\n")
            return unified_conclusion
        except Exception as e:
            print(f"⚠️  통합 결론 생성 실패: {e}")
            return "통합 결론 생성 중 오류가 발생했습니다."

    def save_conclusion_file(self, debate_setup: Dict, history: List, subject_slug: str, final_round_num: int):
        """
        최종 합의안을 별도 파일로 저장

        Args:
            debate_setup: 토론 설정 정보
            history: 대화 히스토리
            subject_slug: 파일명에 사용할 주제 키워드
            final_round_num: 실제 진행된 마지막 라운드 번호
        """
        # 마지막 라운드(최종 합의안) 내용만 추출
        final_round = [msg for msg in history if msg['round'] == final_round_num]

        if not final_round:
            print("⚠️  최종 합의안이 없어 conclusion 파일을 생성하지 않습니다.")
            return

        # 통합된 최종 결론 생성
        unified_conclusion = self.synthesize_final_conclusion(debate_setup, final_round)

        # 토론 파일과 동일한 타임스탬프 사용
        conclusion_filename = f"{subject_slug}-conclusion-{self.timestamp}.md"

        with open(conclusion_filename, 'w', encoding='utf-8') as f:
            # 마크다운 헤더
            f.write(f"# 토론 합의안\n\n")
            f.write(f"**생성 일시**: {time.strftime('%Y년 %m월 %d일 %H:%M:%S')}\n\n")
            f.write(f"**참여자 수**: {len(debate_setup['stances'])}명\n\n")
            f.write(f"---\n\n")

            # 토론 주제
            f.write(f"## 📋 토론 주제\n\n")
            f.write(f"{debate_setup['topic']}\n\n")

            f.write(f"---\n\n")

            # 모든 참여자 입장
            f.write(f"## 👥 참여자 입장\n\n")
            for i, stance in enumerate(debate_setup['stances']):
                ai_model = stance['ai_model']
                emoji = stance['emoji']
                f.write(f"### {emoji} 참여자 {i+1}: {stance['title']} ({ai_model.display_name})\n\n")
                f.write(f"> {stance['position']}\n\n")

            f.write(f"---\n\n")

            # 통합된 최종 결론
            f.write(f"## 📝 통합 최종 결론\n\n")
            f.write(f"{unified_conclusion}\n\n")

            f.write(f"---\n\n")

            # 개별 참여자 합의안 (참고용)
            f.write(f"## 📌 개별 참여자 합의안 (참고)\n\n")

            for msg in final_round:
                speaker_idx = msg['speaker_idx']
                stance = debate_setup['stances'][speaker_idx]
                emoji = stance['emoji']
                ai_model = stance['ai_model']

                f.write(f"### {emoji} {stance['title']} ({ai_model.name})의 제안\n\n")
                f.write(f"{msg['content']}\n\n")

        print(f"📄 합의안 파일 저장: {conclusion_filename}")


def main():
    """메인 함수"""
    print("\n" + "="*60)
    print("🎯 AI 토론 시스템")
    print("="*60)
    print("\n여러 AI 모델을 사용하여 상반된 입장으로 토론하고 합의점을 찾습니다.")
    print("지원 모델: Claude, OpenAI, Gemini, Grok\n")

    try:
        # AI 모델 가용성 확인 및 초기화
        initialize_available_models()

        # 설정값 입력
        print("⚙️  토론 설정")
        print("-" * 60)

        # 참여자 수 입력
        num_participants_input = input("토론 참여자 수 [기본: 2, 최소: 2, 최대: 10]: ").strip()
        num_participants = int(num_participants_input) if num_participants_input else 2

        # 참여자 수 유효성 검사
        if num_participants < 2:
            print("⚠️  참여자 수는 최소 2명 이상이어야 합니다. 기본값(2) 사용")
            num_participants = 2
        elif num_participants > 10:
            print("⚠️  참여자 수는 최대 10명까지 가능합니다. 10명으로 설정")
            num_participants = 10

        # 글자 수 제한 입력
        char_limit_input = input("답변 글자 수 제한 [기본: 500]: ").strip()
        char_limit = int(char_limit_input) if char_limit_input else 500

        # 최대 라운드 수 입력
        num_rounds_input = input("최대 토론 라운드 횟수 [기본: 5]: ").strip()
        num_rounds = int(num_rounds_input) if num_rounds_input else 5

        # 최소 2라운드 이상 확인
        if num_rounds < 2:
            print("⚠️  최대 라운드 수는 최소 2 이상이어야 합니다. 기본값(5) 사용")
            num_rounds = 5

        print(f"\n✅ 설정 완료: 참여자={num_participants}명, 글자 수 제한={char_limit}자, 최대 라운드={num_rounds}회")
        print("💡 모든 참여자가 합의하면 최대 라운드 전에 조기 종료될 수 있습니다.\n")
        print()

        # 시스템 초기화
        system = AIDebateSystem(char_limit=char_limit, num_rounds=num_rounds)

        # 주제 입력
        if len(sys.argv) > 1:
            topic = " ".join(sys.argv[1:])
        else:
            topic = input("토론 주제를 입력하세요: ").strip()

        if not topic:
            print("❌ 주제를 입력해주세요.")
            sys.exit(1)

        # 토론 진행
        debate_setup = system.create_stances_from_user_input(topic, num_participants)
        system.conduct_debate(debate_setup)

    except KeyboardInterrupt:
        print("\n\n⚠️  사용자가 토론을 중단했습니다.")
        sys.exit(0)
    except Exception as e:
        print(f"\n❌ 오류 발생: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()
