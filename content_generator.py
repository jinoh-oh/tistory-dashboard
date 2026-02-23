import google.generativeai as genai
import config
import json
import re
import time

from google.generativeai.types import HarmCategory, HarmBlockThreshold

class ContentGenerator:
    def __init__(self, api_key=None, selected_model=None):
        # Use provided key or fallback to config
        key = api_key if api_key else config.GEMINI_API_KEY
        genai.configure(api_key=key)
        
        # Available models from verified list (Fallbacks)
        self.available_models = [
            'gemini-2.0-flash', 
            'gemini-2.0-flash-lite', 
            'gemini-1.5-flash',
            'gemini-1.5-pro',
            'gemini-1.5-flash-8b'
        ]
        
        # Initialize primary model - allow any string (manual input)
        self.primary_model_name = selected_model if selected_model else self.available_models[0]
        
        # Safety settings (Relaxed)
        self.safety_settings = {
            HarmCategory.HARM_CATEGORY_HARASSMENT: HarmBlockThreshold.BLOCK_NONE,
            HarmCategory.HARM_CATEGORY_HATE_SPEECH: HarmBlockThreshold.BLOCK_NONE,
            HarmCategory.HARM_CATEGORY_SEXUALLY_EXPLICIT: HarmBlockThreshold.BLOCK_NONE,
            HarmCategory.HARM_CATEGORY_DANGEROUS_CONTENT: HarmBlockThreshold.BLOCK_NONE,
        }

        # Handle initialization error for experimental/manual models
        try:
            self.model = genai.GenerativeModel(
                model_name=self.primary_model_name, 
                safety_settings=self.safety_settings
            )
        except Exception:
            # Fallback if manual model name is invalid
            self.model = genai.GenerativeModel(
                model_name=self.available_models[0],
                safety_settings=self.safety_settings
            )

        self.system_instruction = """
        당신은 티스토리 수익형 블로그 전문 필진입니다.
        본문 텍스트 내의 한글 글자 수(공백 제외)가 반드시 1,600자~2,000자 사이가 되도록 매우 길고 상세하게 작성하세요.
        문단마다 깊이 있는 정보를 제공하고, 이모지 사용을 금지하며 전문적인 해요체를 사용하세요.
        """

    def generate_blog_post(self, topic, prompt_template):
        """
        Tries user-selected model first, then fallbacks.
        """
        try:
            prompt = prompt_template.replace("{topic}", topic)
        except Exception:
            prompt = f"Topic: {topic}\n\n" + prompt_template
 
        full_prompt = f"{self.system_instruction}\n\n[USER REQUEST]\n{prompt}\n\n⚠️ 중요: 반드시 한글 1,600자 이상의 충분한 분량으로 작성하세요."

        # Create a priority list: primary model first, then others
        trial_models = [self.primary_model_name] + [m for m in self.available_models if m != self.primary_model_name]
        
        last_error = "모든 가용 모델의 할당량을 초과했거나 연결에 실패했습니다."
        
        for model_name in trial_models:
            print(f"Attempting generation with model: {model_name}...")
            try:
                model = genai.GenerativeModel(model_name=model_name, safety_settings=self.safety_settings)
                response = model.generate_content(full_prompt, generation_config={"response_mime_type": "application/json"})
                
                if not response.text:
                    if response.prompt_feedback:
                        last_error = f"보안 필터 차단 ({model_name}): {response.prompt_feedback}"
                    continue

                data = json.loads(response.text)
                return data, None
                
            except Exception as e:
                last_error = str(e)
                print(f"Model {model_name} failed: {last_error}")
                if "429" in last_error or "ResourceExhausted" in last_error or "404" in last_error:
                    continue
                else:
                    break
        
        return None, last_error

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
        # Retry logic for Quota limits (429 errors)
        for attempt in range(2):
            try:
                response = self.model.generate_content(prompt, generation_config={"response_mime_type": "application/json"})
                data = json.loads(response.text)
                return data.get('content')
            except Exception as e:
                error_msg = str(e)
                if "429" in error_msg or "ResourceExhausted" in error_msg:
                    print(f"API Quota limit reached (429). Waiting 5 seconds before retry {attempt+1}/2...")
                    time.sleep(5)
                    continue
                else:
                    print(f"Error verifying content: {e}")
                    return None
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
        # Retry logic for Quota limits (429 errors)
        for attempt in range(2):
            try:
                response = self.model.generate_content(prompt, generation_config={"response_mime_type": "application/json"})
                data = json.loads(response.text)
                return data.get('content')
            except Exception as e:
                error_msg = str(e)
                if "429" in error_msg or "ResourceExhausted" in error_msg:
                    print(f"API Quota limit reached (429). Waiting 5 seconds before retry {attempt+1}/2...")
                    time.sleep(5)
                    continue
                else:
                    print(f"Error refining content: {e}")
                    return None
        return None
