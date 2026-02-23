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
        Uses the most stable /p/ endpoint with ultra-short prompt.
        """
        width, height = 800, 800
        # Use simple English instruction for the URL path
        raw_query = prompt if prompt else f"Thumbnail for {title}"
        
        # Filter: ONLY Alpha characters and Space. No numbers or special chars.
        # This is for MAX compatibility with weird WAFs.
        clean_query = "".join([c for c in raw_query if (c.isalpha() or c == ' ') and ord(c) < 128])
        
        if not clean_query.strip():
            clean_query = "modern blog layout"
            
        # VERY SHORT: 40 chars max to avoid URL limit issues in some proxies
        search_query = clean_query[:40].strip().replace(' ', '+')
        
        seed = random.randint(1, 100000)
        # Using pollination.ai/p/ is often more direct than the subdomain
        return f"https://pollinations.ai/p/{search_query}?width={width}&height={height}&seed={seed}&nologo=true"

    def get_color_thumbnail(self, text):
        """
        Guaranteed 100% visible solid color thumbnail with text.
        Ultimate fallback using placehold.jp.
        """
        import urllib.parse
        encoded_text = urllib.parse.quote(text[:30])
        # Random vibrant background colors
        colors = ["3b82f6", "ef4444", "10b981", "f59e0b", "8b5cf6"]
        bg = random.choice(colors)
        return f"https://placehold.jp/80/{bg}/ffffff/800x800.png?text={encoded_text}"

    def translate_keyword(self, text):
        """
        Maps common Korean terms to English for stock photo relevance.
        """
        if not text: return "nature"
        # Topic detection
        for ko, en in self.COMMON_TOPICS.items():
            if ko in text:
                return en
        # Fallback to ASCII strip
        clean = "".join([c for c in text if c.isalpha() and ord(c) < 128])
        return clean if clean else "modern"

    def get_stock_image_url(self, title, keywords=None):
        """
        Returns a high-quality stock photo URL from LoremFlickr.
        """
        target = keywords if keywords else title
        final_keyword = self.translate_keyword(target)
        return f"https://loremflickr.com/800/800/{final_keyword}?lock={random.randint(1, 1000)}"

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
