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
from typing import Dict, List
import time
import subprocess
import re
from dataclasses import dataclass


@dataclass
class AIModel:
    """AI 모델 정보"""
    name: str           # 표시 이름 (예: "Claude")
    command: List[str]  # CLI 명령어 (예: ["claude", "code", "-p"])
    display_name: str   # 화면 표시용 전체 이름 (예: "Claude (Anthropic)")


# 지원하는 AI 모델 정의
AVAILABLE_AI_MODELS = {
    "claude": AIModel(
        name="Claude",
        command="claude -p".split(),
        display_name="Claude (Anthropic)"
    ),
    "openai": AIModel(
        name="OpenAI",
        command="codex exec --skip-git-repo-check".split(),
        display_name="OpenAI GPT (Codex)"
    ),
    "gemini": AIModel(
        name="Gemini",
        command="gemini -p".split(),
        display_name="Gemini (Google)"
    ),
    "grok": AIModel(
        name="Grok",
        command="grok -p".split(),
        display_name="Grok (xAI)"
    )
}


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
                print("\n\n⚠️  기본값(Claude) 사용")
                return AVAILABLE_AI_MODELS["claude"]

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
            # 파일명 생성은 Claude 사용 (기본)
            keyword = self.call_ai(prompt, AVAILABLE_AI_MODELS["claude"])
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
        
    def analyze_topic_and_create_stances(self, topic: str) -> Dict:
        """
        주제를 분석하고 상반된 두 입장을 생성
        
        Args:
            topic: 토론 주제
            
        Returns:
            토론 설정 정보 (주제, 입장 A, 입장 B)
        """
        print(f"\n{'='*60}")
        print(f"📋 주제 분석 중: {topic}")
        print(f"{'='*60}\n")
        
        prompt = f"""다음 주제에 대해 분석하고 두 가지 상반된 입장을 생성해주세요:

주제: "{topic}"

다음 JSON 형식으로 응답해주세요 (다른 텍스트 없이 JSON만):
{{
  "topic": "명확하게 정리된 토론 주제",
  "stanceA": {{
    "position": "입장 A의 핵심 주장 (한 문장)",
    "title": "입장 A의 간단한 라벨 (예: 찬성파, 진보적 관점)"
  }},
  "stanceB": {{
    "position": "입장 B의 핵심 주장 (한 문장)",
    "title": "입장 B의 간단한 라벨 (예: 반대파, 보수적 관점)"
  }}
}}

두 입장은 명확히 대립되어야 하며, 균형잡힌 토론이 가능해야 합니다."""

        try:
            # 주제 분석은 Claude 사용 (기본)
            response_text = self.call_ai(prompt, AVAILABLE_AI_MODELS["claude"])
            
            # JSON 추출 (마크다운 코드블록 제거)
            if response_text.startswith("```"):
                response_text = response_text.split("```")[1]
                if response_text.startswith("json"):
                    response_text = response_text[4:]
                response_text = response_text.strip()
            
            debate_setup = json.loads(response_text)
            
            print(f"✅ 토론 주제: {debate_setup['topic']}\n")
            print(f"🔵 입장 A ({debate_setup['stanceA']['title']})")
            print(f"   {debate_setup['stanceA']['position']}\n")
            print(f"🟡 입장 B ({debate_setup['stanceB']['title']})")
            print(f"   {debate_setup['stanceB']['position']}\n")

            # 각 입장에 대해 AI 선택
            ai_model_a = self.select_ai_for_stance(debate_setup['stanceA']['title'])
            ai_model_b = self.select_ai_for_stance(debate_setup['stanceB']['title'])

            # AI 정보 추가
            debate_setup['stanceA']['ai_model'] = ai_model_a
            debate_setup['stanceB']['ai_model'] = ai_model_b

            return debate_setup
            
        except Exception as e:
            print(f"❌ 오류 발생: {e}")
            raise
    
    def check_consensus_ready(
        self,
        debate_setup: Dict,
        speaker: str,
        history: List
    ) -> bool:
        """
        합의 준비 여부 확인

        Args:
            debate_setup: 토론 설정 정보
            speaker: 'A' 또는 'B'
            history: 대화 히스토리

        Returns:
            True면 최종 합의 준비 완료, False면 토론 계속 필요
        """
        stance = debate_setup['stanceA'] if speaker == 'A' else debate_setup['stanceB']

        prompt = f"""지금까지의 토론을 검토해주세요.

주제: {debate_setup['topic']}
당신의 입장: {stance['position']}

지금까지의 토론 내용:
"""
        for msg in history:
            speaker_label = "나" if msg['speaker'] == speaker else "상대방"
            prompt += f"{speaker_label}: {msg['content']}\n\n"

        prompt += f"""
질문: 지금까지의 토론으로 최종 합의안을 도출할 준비가 되었나요?

다음 기준으로 판단해주세요:
- 양측의 핵심 주장이 충분히 교환되었나?
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
        speaker: str,
        history: List,
        instruction: str
    ) -> str:
        """
        특정 입장에서 AI 응답 생성 (글자 수 제한 검증 포함)

        Args:
            debate_setup: 토론 설정 정보
            speaker: 'A' 또는 'B'
            history: 대화 히스토리
            instruction: 현재 라운드 지시사항

        Returns:
            AI 응답 텍스트
        """
        stance = debate_setup['stanceA'] if speaker == 'A' else debate_setup['stanceB']
        other_stance = debate_setup['stanceB'] if speaker == 'A' else debate_setup['stanceA']

        prompt = f"""당신은 다음 주제에 대한 토론에 참여하고 있습니다:

주제: {debate_setup['topic']}

당신의 입장: {stance['position']}
상대방의 입장: {other_stance['position']}

토론 규칙:
- 자신의 입장을 명확히 방어하되, 상대방의 타당한 지적은 수용하세요
- 논리적이고 구체적인 근거를 제시하세요
- 감정적이거나 인신공격적인 표현은 피하세요
- 궁극적으로는 합의점을 찾는 것이 목표입니다

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
                speaker_label = "나" if msg['speaker'] == speaker else "상대방"
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

            # 적정 범위
            if char_count <= self.char_limit:
                return response

            # 너무 긴 경우 (1회만 요약 요청)
            print(f"⚠️  답변이 {char_count}자로 제한({self.char_limit}자)을 초과했습니다. 요약을 요청합니다...")

            summary_prompt = f"""다음 답변이 {char_count}자로 너무 깁니다.

원본 답변:
{response}

**🚨 필수: 위 내용을 {self.char_limit}자 이내로 요약하세요.**
- 핵심 논점만 유지하세요
- 불필요한 수식어나 예시는 제거하세요
- 반드시 {self.char_limit}자 이내로 작성하세요

요약된 답변만 출력하세요 (다른 설명 없이)."""

            response = self.call_ai(summary_prompt, ai_model)

            # 요약 후 글자 수 표시 (정보 제공용)
            final_char_count = len(response)
            if final_char_count > self.char_limit:
                print(f"ℹ️  요약 후 {final_char_count}자 (제한: {self.char_limit}자)")
            else:
                print(f"✅ 요약 완료: {final_char_count}자")

            return response

        except Exception as e:
            print(f"❌ AI 응답 생성 중 오류: {e}")
            return "응답 생성 중 오류가 발생했습니다."
    
    def conduct_debate(self, debate_setup: Dict):
        """
        전체 토론 진행

        Args:
            debate_setup: 토론 설정 정보
        """
        # 토론 파일 초기화
        self.initialize_debate_file(debate_setup)

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
                    'instruction': f'상대방의 주장에 대해 반박하거나 질문하고, 타당한 지적은 인정하며, 합의점을 찾아가세요. ({self.char_limit}자 이내)',
                }

            rounds.append(round_info)
        
        conversation_history = []
        actual_round_num = 0  # 실제 진행된 라운드 번호
        min_rounds = 2  # 최소 진행 라운드 (초기 주장 + 1회 토론)

        for i, round_info in enumerate(rounds):
            actual_round_num = i + 1

            print(f"\n{'='*60}")
            print(f"📍 라운드 {actual_round_num}: {round_info['name']}")
            print(f"{'='*60}\n")

            # 입장 A 응답
            ai_a = debate_setup['stanceA']['ai_model']
            print(f"🔵 {debate_setup['stanceA']['title']} ({ai_a.name}) 발언 중...")
            response_a = self.get_ai_response(
                debate_setup,
                'A',
                conversation_history,
                round_info['instruction']
            )

            print(f"\n🔵 {debate_setup['stanceA']['title']} ({ai_a.name}):")
            print(f"{'-'*60}")
            print(response_a)
            print(f"{'-'*60}\n")

            conversation_history.append({
                'speaker': 'A',
                'content': response_a,
                'round': actual_round_num
            })

            # 실시간으로 파일에 저장
            self.append_to_debate_file(debate_setup, 'A', response_a, actual_round_num, round_info['name'])

            time.sleep(1)  # API 호출 간격

            # 입장 B 응답
            ai_b = debate_setup['stanceB']['ai_model']
            print(f"🟡 {debate_setup['stanceB']['title']} ({ai_b.name}) 발언 중...")
            response_b = self.get_ai_response(
                debate_setup,
                'B',
                conversation_history,
                round_info['instruction']
            )

            print(f"\n🟡 {debate_setup['stanceB']['title']} ({ai_b.name}):")
            print(f"{'-'*60}")
            print(response_b)
            print(f"{'-'*60}\n")

            conversation_history.append({
                'speaker': 'B',
                'content': response_b,
                'round': actual_round_num
            })

            # 실시간으로 파일에 저장
            self.append_to_debate_file(debate_setup, 'B', response_b, actual_round_num, round_info['name'])

            time.sleep(1)  # API 호출 간격

            # 최종 합의안 라운드면 종료
            if round_info['name'] == '최종 합의안':
                break

            # 최소 라운드 이후이고, 최대 라운드에 도달하지 않았으면 합의 준비 확인
            if actual_round_num >= min_rounds and i < len(rounds) - 1:
                print(f"\n{'~'*60}")
                print("🤝 양측의 합의 준비 상태를 확인합니다...")
                print(f"{'~'*60}\n")

                # 양측 합의 준비 확인
                ready_a = self.check_consensus_ready(debate_setup, 'A', conversation_history)
                ready_b = self.check_consensus_ready(debate_setup, 'B', conversation_history)

                status_a = "✅ 준비 완료" if ready_a else "⏳ 토론 계속"
                status_b = "✅ 준비 완료" if ready_b else "⏳ 토론 계속"

                print(f"🔵 {debate_setup['stanceA']['title']}: {status_a}")
                print(f"🟡 {debate_setup['stanceB']['title']}: {status_b}\n")

                if ready_a and ready_b:
                    print("🎉 양측 모두 합의 준비가 완료되었습니다!")
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

                    # 최종 합의안 - 입장 A
                    print(f"🔵 {debate_setup['stanceA']['title']} ({ai_a.name}) 발언 중...")
                    final_response_a = self.get_ai_response(
                        debate_setup,
                        'A',
                        conversation_history,
                        final_round_info['instruction']
                    )
                    print(f"\n🔵 {debate_setup['stanceA']['title']} ({ai_a.name}):")
                    print(f"{'-'*60}")
                    print(final_response_a)
                    print(f"{'-'*60}\n")

                    conversation_history.append({
                        'speaker': 'A',
                        'content': final_response_a,
                        'round': actual_round_num
                    })
                    self.append_to_debate_file(debate_setup, 'A', final_response_a, actual_round_num, final_round_info['name'])
                    time.sleep(1)

                    # 최종 합의안 - 입장 B
                    print(f"🟡 {debate_setup['stanceB']['title']} ({ai_b.name}) 발언 중...")
                    final_response_b = self.get_ai_response(
                        debate_setup,
                        'B',
                        conversation_history,
                        final_round_info['instruction']
                    )
                    print(f"\n🟡 {debate_setup['stanceB']['title']} ({ai_b.name}):")
                    print(f"{'-'*60}")
                    print(final_response_b)
                    print(f"{'-'*60}\n")

                    conversation_history.append({
                        'speaker': 'B',
                        'content': final_response_b,
                        'round': actual_round_num
                    })
                    self.append_to_debate_file(debate_setup, 'B', final_response_b, actual_round_num, final_round_info['name'])

                    break
                else:
                    print("➡️  토론을 계속 진행합니다.\n")
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
        timestamp = time.strftime("%Y%m%d-%H%M%S")

        # AI에게 주제를 짧은 영어 키워드로 변환 요청
        print("📝 파일명 키워드 생성 중...")
        self.subject_slug = self.generate_filename_keyword(debate_setup['topic'])
        print(f"✅ 파일명: {self.subject_slug}-{timestamp}.md\n")

        self.debate_filename = f"{self.subject_slug}-{timestamp}.md"

        with open(self.debate_filename, 'w', encoding='utf-8') as f:
            # 마크다운 헤더
            f.write(f"# AI 토론 기록\n\n")
            f.write(f"**생성 일시**: {time.strftime('%Y년 %m월 %d일 %H:%M:%S')}\n\n")
            f.write(f"---\n\n")

            # 토론 주제 및 입장
            f.write(f"## 📋 토론 주제\n\n")
            f.write(f"{debate_setup['topic']}\n\n")

            ai_a = debate_setup['stanceA']['ai_model']
            ai_b = debate_setup['stanceB']['ai_model']

            f.write(f"### 🔵 입장 A: {debate_setup['stanceA']['title']} ({ai_a.display_name})\n\n")
            f.write(f"> {debate_setup['stanceA']['position']}\n\n")

            f.write(f"### 🟡 입장 B: {debate_setup['stanceB']['title']} ({ai_b.display_name})\n\n")
            f.write(f"> {debate_setup['stanceB']['position']}\n\n")

            f.write(f"---\n\n")

            # 토론 내용 섹션 시작
            f.write(f"## 💬 토론 내용\n\n")

        print(f"💾 토론 기록 파일 생성: {self.debate_filename}\n")

    def append_to_debate_file(self, debate_setup: Dict, speaker: str, content: str, round_num: int, round_name: str):
        """
        토론 내용을 실시간으로 파일에 추가

        Args:
            debate_setup: 토론 설정 정보
            speaker: 'A' 또는 'B'
            content: 발언 내용
            round_num: 라운드 번호
            round_name: 라운드 이름
        """
        with open(self.debate_filename, 'a', encoding='utf-8') as f:
            # 새 라운드 시작 시 라운드 헤더 추가
            if round_num != self.current_round:
                self.current_round = round_num
                f.write(f"### 라운드 {round_num}: {round_name}\n\n")

            stance = debate_setup['stanceA'] if speaker == 'A' else debate_setup['stanceB']
            icon = "🔵" if speaker == 'A' else "🟡"
            ai_model = stance['ai_model']

            f.write(f"#### {icon} {stance['title']} ({ai_model.name})\n\n")
            f.write(f"{content}\n\n")

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

        timestamp = time.strftime("%Y%m%d-%H%M%S")
        conclusion_filename = f"{subject_slug}-conclusion-{timestamp}.md"

        with open(conclusion_filename, 'w', encoding='utf-8') as f:
            # 마크다운 헤더
            f.write(f"# 토론 합의안\n\n")
            f.write(f"**생성 일시**: {time.strftime('%Y년 %m월 %d일 %H:%M:%S')}\n\n")
            f.write(f"---\n\n")

            # 토론 주제
            f.write(f"## 📋 토론 주제\n\n")
            f.write(f"{debate_setup['topic']}\n\n")

            f.write(f"---\n\n")

            # 양측 입장
            ai_a = debate_setup['stanceA']['ai_model']
            ai_b = debate_setup['stanceB']['ai_model']

            f.write(f"## 🤝 양측 입장\n\n")
            f.write(f"### 🔵 {debate_setup['stanceA']['title']} ({ai_a.display_name})\n\n")
            f.write(f"> {debate_setup['stanceA']['position']}\n\n")
            f.write(f"### 🟡 {debate_setup['stanceB']['title']} ({ai_b.display_name})\n\n")
            f.write(f"> {debate_setup['stanceB']['position']}\n\n")

            f.write(f"---\n\n")

            # 최종 합의안
            f.write(f"## ✅ 최종 합의안\n\n")

            for msg in final_round:
                stance = debate_setup['stanceA'] if msg['speaker'] == 'A' else debate_setup['stanceB']
                icon = "🔵" if msg['speaker'] == 'A' else "🟡"
                ai_model = stance['ai_model']

                f.write(f"### {icon} {stance['title']} ({ai_model.name})의 제안\n\n")
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
        # 설정값 입력
        print("⚙️  토론 설정")
        print("-" * 60)

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

        print(f"\n✅ 설정 완료: 글자 수 제한={char_limit}자, 최대 라운드={num_rounds}회")
        print("💡 양측이 합의하면 최대 라운드 전에 조기 종료될 수 있습니다.\n")
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
        debate_setup = system.analyze_topic_and_create_stances(topic)
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
