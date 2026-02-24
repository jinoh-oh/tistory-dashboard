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
        # Added futuristic models seen in user screenshot
        self.available_models = [
            'gemini-2.0-flash', 
            'gemini-2.0-flash-lite', 
            'gemini-1.5-flash',
            'gemini-1.5-pro',
            'gemini-3-flash',
            'gemini-2.5-flash',
            'gemini-2.5-pro'
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

        self.system_instruction = """
        당신은 티스토리 수익형 블로그 전문 필진입니다.
        본문 텍스트 내의 한글 글자 수(공백 제외)가 반드시 1,600자~2,000자 사이가 되도록 매우 길고 상세하게 작성하세요.
        문단마다 깊이 있는 정보를 제공하고, 이모지 사용을 금지하며 전문적인 해요체를 사용하세요.
        """

    def _generate_with_fallback(self, prompt, is_json=True):
        """
        Internal helper: Tries primary model first, then fallbacks.
        Handles JSON parsing and common errors.
        """
        # Create a priority list: primary model first, then others
        trial_models = [self.primary_model_name] + [m for m in self.available_models if m != self.primary_model_name]
        
        last_error = "모든 가용 모델의 할당량을 초과했거나 연결에 실패했습니다."
        
        for model_name in trial_models:
            print(f"Attempting task with model: {model_name}...")
            try:
                model = genai.GenerativeModel(model_name=model_name, safety_settings=self.safety_settings)
                
                gen_config = {"response_mime_type": "application/json"} if is_json else {}
                response = model.generate_content(prompt, generation_config=gen_config)
                
                if not response.text:
                    if response.prompt_feedback:
                        last_error = f"보안 필터 차단 ({model_name}): {response.prompt_feedback}"
                    continue

                if is_json:
                    # Strip markdown code blocks if present
                    text = response.text.strip()
                    if text.startswith("```json"):
                        text = text.replace("```json", "", 1).replace("```", "", 1).strip()
                    elif text.startswith("```"):
                        text = text.replace("```", "", 1).replace("```", "", 1).strip()
                    
                    data = json.loads(text)
                    return data, None
                else:
                    return response.text, None
                
            except Exception as e:
                last_error = str(e)
                print(f"Model {model_name} failed: {last_error}")
                # Skip 404 or 429
                if "429" in last_error or "ResourceExhausted" in last_error or "404" in last_error or "not found" in last_error.lower():
                    continue
                else:
                    # Might be a transient error, wait briefly and try next model
                    time.sleep(2)
                    continue
        
        return None, last_error

    def generate_blog_post(self, topic, prompt_template):
        """
        Orchestrates main blog generation.
        """
        try:
            prompt = prompt_template.replace("{topic}", topic)
        except Exception:
            prompt = f"Topic: {topic}\n\n" + prompt_template
 
        full_prompt = f"""
        {self.system_instruction}
        
        [USER REQUEST]
        {prompt}
        
        ⚠️ [CRITICAL: OUTPUT FORMAT]
        반드시 아래의 JSON 형식을 엄격히 준수하여 응답하세요. 다른 텍스트 설명은 포함하지 마세요.
        {{
            "title": "SEO 최적화된 제목",
            "thumbnail_title": "이미지에 들어갈 핵심 키워드 + ' >'",
            "content": "HTML 형식의 본문 내용 (한글 1,600자 이상)",
            "tags": ["태그1", "태그2", "태그3", "태그4", "태그5"],
            "image_prompt": "이미지 생성을 위한 상세 영어 프롬프트",
            "image_keywords": "이미지 테마 영문 키워드 2-3개"
        }}
        """
        data, error = self._generate_with_fallback(full_prompt, is_json=True)
        if data:
            if 'title' in data:
                data['title'] = self._strip_html(data['title'])
            if 'content' in data:
                data['content'] = self._clean_residue(data['content'])
        return data, error

    def _strip_html(self, text):
        """
        Removes HTML tags from a string.
        """
        if not text: return text
        clean = re.compile('<.*?>')
        return re.sub(clean, '', text).strip()

    def _clean_residue(self, text):
        """
        Removes accidentally leaked JSON characters (like }} ] }) and backticks from HTML content.
        """
        if not text: return text
        # Remove trailing JSON-like characters that AI sometimes leaks
        cleaned = re.sub(r'\s*[}\]]+\s*$', '', text.strip())
        # Remove triple backticks if still present
        cleaned = cleaned.replace("```html", "").replace("```", "").strip()
        return cleaned

    def verify_and_rewrite(self, content, topic):
        """
        Verifies if the content is up-to-date and rewrites it.
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
        반드시 JSON 형식으로 반환하세요. "content" 필드에 HTML을 담으세요.
        """
        result, error = self._generate_with_fallback(prompt, is_json=True)
        if result:
            return self._clean_residue(result.get('content')), None
        return None, error

    def spell_check_and_refine(self, content):
        """
        Corrects spelling and grammar.
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
        반드시 JSON 형식으로 반환하세요. "content" 필드에 HTML을 담으세요.
        """
        result, error = self._generate_with_fallback(prompt, is_json=True)
        if result:
            return self._clean_residue(result.get('content')), None
        return None, error
