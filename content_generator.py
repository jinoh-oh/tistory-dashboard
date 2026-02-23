import google.generativeai as genai
import config
import json
import re

class ContentGenerator:
    def __init__(self):
        genai.configure(api_key=config.GEMINI_API_KEY)
        # Use a model confirmed to be available and robust
        self.model = genai.GenerativeModel(
            model_name='gemini-2.0-flash'
        )
        self.system_instruction = """
        당신은 티스토리 수익형 블로그 전문 필진입니다.
        당신의 최우선 목표는 '풍부한 양'과 '독창적 정보'를 제공하는 것입니다.
        다음 지침을 철저히 준수하세요:
        1. 분량: 본문 텍스트 내의 한글 글자 수(공백 제외)가 반드시 1,600자~2,000자 사이가 되도록 매우 길고 상세하게 작성하세요.
        2. 품질: 각 소제목 아래에는 최소 3개 이상의 상세 문단을 작성하여 깊이 있는 정보를 제공하세요.
        3. 형식: HTML 태그를 적절히 활용하여 독자가 읽기 편한 구조를 만드세요.
        4. 말투: 친절하고 전문적인 해요체를 사용하며, 이모지는 절대 사용하지 마세요.
        """

    def generate_blog_post(self, topic, prompt_template):
        """
        Generates a blog post title, content, and image prompt based on the topic.
        """
        try:
            prompt = prompt_template.replace("{topic}", topic)
        except Exception:
            prompt = f"Topic: {topic}\n\n" + prompt_template

        # Combine system instruction and final reminders into the prompt for maximum compatibility
        full_prompt = f"{self.system_instruction}\n\n[USER REQUEST]\n{prompt}\n\n⚠️ 중요: 반드시 한글 1,600자 이상의 충분한 분량으로 작성하세요."

        try:
            response = self.model.generate_content(full_prompt, generation_config={"response_mime_type": "application/json"})
            data = json.loads(response.text)
            return data
        except Exception as e:
            print(f"Error generating content: {e}")
            return None

    def verify_and_rewrite(self, content, topic):
        """
        Verifies if the content is up-to-date and rewrites it if necessary.
        """
        prompt = f"""
        당신은 전문 사실 확인 및 콘텐츠 편집가입니다.
        다음 주제({topic})에 대해 작성된 블로그 본문(HTML 형식)을 검토해주세요.

        [검토 지침]
        1. 정보의 최신성: 2026년 2월 현재 기준으로 정보가 정확하고 최신인지 확인하세요.
        2. 내용 보완: 부족하거나 틀린 정보가 있다면 실제 팩트에 기반하여 자연스럽게 수정하거나 보완하세요.
        3. 기존 스타일 유지: 제공된 HTML 구조와 스타일을 그대로 유지하면서 내용만 개선하세요.
        4. 말투: 친절한 해요체 유지. 이모지 사용 금지.

        [본문 내용]
        {content}

        [건의]
        반드시 JSON 형식으로 반환하세요:
        {{
            "content": "수정 및 보완된 HTML 본문"
        }}
        """
        try:
            response = self.model.generate_content(prompt, generation_config={"response_mime_type": "application/json"})
            data = json.loads(response.text)
            return data.get('content')
        except Exception as e:
            print(f"Error verifying content: {e}")
            return None

    def spell_check_and_refine(self, content):
        """
        Corrects spelling and grammar while maintaining HTML structure.
        """
        prompt = f"""
        당신은 한국어 교열 전문가입니다.
        다음 HTML 본문의 맞춤법, 띄어쓰기, 문법을 교정하고 문장을 더 매끄럽게 다듬어주세요.

        [주의 사항]
        1. HTML 태그는 절대 건드리지 마세요. 태그 내부의 텍스트만 교정하세요.
        2. 가급적 원래의 의미를 훼손하지 않으면서 자연스러운 문장으로 만드세요.
        3. 이모지는 절대 사용하지 마세요.

        [본문 내용]
        {content}

        [건의]
        반드시 JSON 형식으로 반환하세요:
        {{
            "content": "교정된 HTML 본문"
        }}
        """
        try:
            response = self.model.generate_content(prompt, generation_config={"response_mime_type": "application/json"})
            data = json.loads(response.text)
            return data.get('content')
        except Exception as e:
            print(f"Error refining content: {e}")
            return None
