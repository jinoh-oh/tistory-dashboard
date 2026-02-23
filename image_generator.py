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

    def get_svg_thumbnail(self, text):
        """
        Generates a 100% reliable SVG thumbnail as a Data URL.
        Features: Large bold text, auto-wrapping, vibrant colors.
        """
        import base64
        
        # Limit text to 30 chars for readability, but try to wrap at 10-12
        full_text = text[:40].strip()
        words = full_text.split()
        lines = []
        current_line = ""
        
        for word in words:
            if len(current_line + word) <= 12:
                current_line += (word + " ")
            else:
                if current_line: lines.append(current_line.strip())
                current_line = word + " "
        if current_line: lines.append(current_line.strip())
        
        # Max 3 lines for clean look
        lines = lines[:3]
        
        # Vibrant colors (Tailwind palette)
        colors = ["#3b82f6", "#ef4444", "#10b981", "#f59e0b", "#8b5cf6", "#ec4899", "#06b6d4"]
        bg = random.choice(colors)
        
        # SVG Construction
        # Use white text with a slight shadow for premium feel
        line_height = 80
        start_y = 400 - ((len(lines)-1) * line_height / 2)
        
        text_elements = ""
        # Dynamic font size based on line count
        font_size = "90px" if len(lines) <= 2 else "70px"
        for i, line in enumerate(lines):
            y = start_y + (i * line_height)
            text_elements += f'<text x="50%" y="{y}" text-anchor="middle" fill="white" font-family="sans-serif" font-weight="900" font-size="{font_size}">{line}</text>'
            
        svg = f"""
        <svg width="800" height="800" viewBox="0 0 800 800" xmlns="http://www.w3.org/2000/svg">
            <rect width="800" height="800" fill="{bg}"/>
            {text_elements}
        </svg>
        """
        
        encoded = base64.b64encode(svg.encode('utf-8')).decode('utf-8')
        return f"data:image/svg+xml;base64,{encoded}"

    def translate_keyword(self, text):
        """
        Maps common Korean terms to English for stock photo relevance.
        """
        if not text: return "nature"
        for ko, en in self.COMMON_TOPICS.items():
            if ko in text:
                return en
        # Fallback: Extract first ASCII word
        clean = "".join([c if (c.isalpha() or c == ' ') else ' ' for c in text if ord(c) < 128])
        parts = clean.split()
        return parts[0] if parts else "modern"

    def get_stock_image_url(self, title, keywords=None):
        """
        Returns a high-quality stock photo URL from Unsplash.
        Unsplash is much more relevant than LoremFlickr.
        """
        target = keywords if keywords else title
        kw = self.translate_keyword(target)
        # Use Unsplash Source for better quality and relevance
        return f"https://images.unsplash.com/photo-1542314831-068cd1dbfeeb?auto=format&fit=crop&w=800&q=80&keywords={kw}" if kw == "hotel" else \
               f"https://source.unsplash.com/800x800/?{kw}&sig={random.randint(1, 1000)}"

    def get_image_url(self, title, prompt=None, keywords=None, use_stock=False):
        """
        Unified method. Defaults to SVG for text thumbnails.
        """
        if use_stock:
            return self.get_stock_image_url(title, keywords)
        # We now use SVG by default for "Thumbnail" because it's 100% reliable
        return self.get_svg_thumbnail(title)

    def generate_image(self, title, prompt=None, include_text=False):
        """
        Compatibility method.
        """
        return self.get_image_url(title)
