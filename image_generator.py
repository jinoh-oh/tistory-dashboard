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
        Features: Large bold text, big vertical spacing, and " >" symbol.
        """
        import base64
        
        # User request: Add ' >' at the end for premium look
        display_text = text.strip()
        if not display_text.endswith(">"):
            display_text += " >"
            
        words = display_text.split()
        lines = []
        current_line = ""
        
        for word in words:
            if len(current_line + word) <= 8: # Even shorter for bigger font
                current_line += (word + " ")
            else:
                if current_line: lines.append(current_line.strip())
                current_line = word + " "
        if current_line: lines.append(current_line.strip())
        
        lines = lines[:3]
        
        # Vibrant colors (Tailwind palette)
        colors = ["#3b82f6", "#ef4444", "#10b981", "#f59e0b", "#8b5cf6", "#ec4899", "#06b6d4"]
        bg = random.choice(colors)
        
        # Polished Spacing: Maximize vertical air
        line_height = 135 
        total_height = len(lines) * line_height
        start_y = 400 - (total_height / 2) + (line_height / 1.3)
        
        text_elements = ""
        font_size = "100px" if len(lines) <= 2 else "80px"
        for i, line in enumerate(lines):
            y = start_y + (i * line_height)
            # Use paint-order for broad contrast
            text_elements += f'<text x="50%" y="{y}" text-anchor="middle" fill="white" font-family="sans-serif" font-weight="900" font-size="{font_size}" style="paint-order: stroke; stroke: rgba(0,0,0,0.1); stroke-width: 6px;">{line}</text>'
            
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
        text_lower = text.lower()
        for ko, en in self.COMMON_TOPICS.items():
            if ko in text_lower:
                return en
        # Fallback: Extract first ASCII word
        clean = "".join([c if (c.isalpha() or c == ' ') else ' ' for c in text if ord(c) < 128])
        parts = clean.split()
        return parts[0] if parts else "modern"

    def get_stock_image_url(self, title, keywords=None):
        """
        Returns a high-quality stock photo URL.
        Uses Unsplash Source with better keyword handling to avoid irrelevant images.
        """
        target = keywords if keywords else title
        kw = self.translate_keyword(target)
        
        seed = random.randint(1, 1000)
        # Unsplash Source is usually more relevant than LoremFlickr for professional blog topics
        # Adding a topic keyword like 'professional' or 'lifestyle' helps avoid random objects
        return f"https://source.unsplash.com/featured/800x800?{kw},blog&sig={seed}"

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
