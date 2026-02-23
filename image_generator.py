import urllib.parse
import random

class ImageGenerator:
    def __init__(self, output_dir="generated_images"):
        self.output_dir = output_dir

    # Hardcoded mapping for common Korean blog topics to ensure relevance
    COMMON_TOPICS = {
        "다이어트": "diet", "체중": "weight loss", "운동": "fitness", "헬스": "gym",
        "주식": "stock market", "투자": "investing", "재능": "finance", "경제": "economy",
        "건강": "health", "영양": "nutrition", "비타민": "vitamins",
        "요리": "cooking", "레시피": "recipe", "음식": "food", "맛집": "restaurant",
        "여행": "travel", "관광": "tourism", "호텔": "hotel",
        "뷰티": "beauty", "화장품": "cosmetics", "피부": "skincare",
        "it": "technology", "반도체": "tech", "스마트폰": "smartphone",
        "육아": "parenting", "아기": "baby", "교육": "education",
        "부업": "side hustle", "수익": "money", "자기계발": "success"
    }

    def get_ai_image_url(self, title, prompt=None):
        """
        Constructs and returns a Pollinations.ai URL for the image.
        """
        width, height = 800, 800
        # AI Prompt: Use ASCII-ONLY in the URL.
        # Minimalist instruction for better stability.
        raw_query = prompt if prompt else f"Thumbnail for {title}"
        
        # Filter: Only Alphanumeric and Space
        clean_query = "".join([c for c in raw_query if (c.isalnum() or c == ' ') and ord(c) < 128])
        
        if not clean_query.strip():
            clean_query = "professional blog thumbnail"
            
        # Use simple URL path - remove 'enhance=true' as it can be flakey/slow
        search_query = clean_query[:70].strip().replace(' ', '+')
        
        seed = random.randint(1, 1000000)
        return f"https://image.pollinations.ai/prompt/{search_query}?width={width}&height={height}&nologo=true&seed={seed}"

    def translate_keyword(self, text):
        """
        Maps common Korean terms to English for stock photo relevance.
        """
        if not text: return "nature"
        for ko, en in self.COMMON_TOPICS.items():
            if ko in text:
                return en
        # If no match, try to strip non-ascii and take first word
        clean = "".join([c for c in text if (c.isalnum() or c == ' ') and ord(c) < 128])
        parts = clean.split()
        return parts[0] if parts else "nature"

    def get_stock_image_url(self, title, keywords=None):
        """
        Returns a high-quality stock photo URL from LoremFlickr.
        """
        # Try to get a clean English keyword from mapping or input
        target = keywords if keywords else title
        final_keyword = self.translate_keyword(target)
            
        # Use 'lock' param for consistency
        return f"https://loremflickr.com/800/800/{final_keyword.replace(' ', ',')}?lock={random.randint(1, 1000)}"

    def get_image_url(self, title, prompt=None, keywords=None, use_stock=False):
        """
        Unified method to get image URL.
        """
        if use_stock:
            return self.get_stock_image_url(title, keywords)
        return self.get_ai_image_url(title, prompt)

    def generate_image(self, title, prompt=None, include_text=False):
        """
        Compatibility method.
        """
        return self.get_image_url(title, prompt)
