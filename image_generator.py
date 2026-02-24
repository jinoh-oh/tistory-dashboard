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

    def get_jpg_thumbnail(self, text):
        """
        Generates a 800x800 JPG thumbnail using Pillow for Tistory compatibility.
        Features high-quality Korean typography and visual polish.
        """
        from PIL import Image, ImageDraw, ImageFont
        import io
        import base64
        
        # 1. Setup Canvas
        size = 800
        colors = ["#3b82f6", "#ef4444", "#10b981", "#f59e0b", "#8b5cf6", "#ec4899", "#06b6d4"]
        bg_hex = random.choice(colors)
        img = Image.new('RGB', (size, size), color=bg_hex)
        draw = ImageDraw.Draw(img)
        
        # 2. Text Preparation
        display_text = text.strip()
        if not display_text.endswith(">"):
            display_text += " >"
            
        # 3. Dynamic Font Loading
        font_path = r"C:\Windows\Fonts\malgun.ttf" # Windows default
        try:
            # Fallback if malgun is missing (though verified earlier)
            font_size = 110 # Slightly bigger than SVG
            font = ImageFont.truetype(font_path, font_size)
        except Exception:
            font = ImageFont.load_default()
            
        # 4. Word Wrap (Max 3 lines, max 8 chars per line)
        words = display_text.split()
        lines = []
        current_line = ""
        for word in words:
            if len(current_line + word) <= 8:
                current_line += (word + " ")
            else:
                if current_line: lines.append(current_line.strip())
                current_line = word + " "
        if current_line: lines.append(current_line.strip())
        lines = lines[:3]
        
        # 5. Draw Text with Strong Outline (Premium YouTube Style)
        line_height = 130
        total_text_height = len(lines) * line_height
        start_y = (size - total_text_height) // 2
        
        outline_color = (0, 0, 0, 40) # Subtle dark outline/shadow
        
        for i, line in enumerate(lines):
            # Calculate centering
            w = draw.textlength(line, font=font)
            x = (size - w) // 2
            y = start_y + (i * line_height)
            
            # Thick Outline (draw 8 times for full coverage)
            outline_thickness = 4
            for dx in range(-outline_thickness, outline_thickness + 1):
                for dy in range(-outline_thickness, outline_thickness + 1):
                    if dx != 0 or dy != 0:
                        draw.text((x+dx, y+dy), line, fill="black", font=font)
            
            # Main Bold Text
            draw.text((x, y), line, fill="white", font=font)

        # 6. Export to Base64 JPG
        buffered = io.BytesIO()
        img.save(buffered, format="JPEG", quality=95)
        encoded = base64.b64encode(buffered.getvalue()).decode('utf-8')
        return f"data:image/jpeg;base64,{encoded}"

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
        Switching to LoremFlickr for better reliability than Unsplash Source.
        """
        target = keywords if keywords else title
        kw = self.translate_keyword(target)
        
        # Multiple keywords handling for LoremFlickr (comma separated)
        clean_kw = kw.replace(" ", "")
        seed = random.randint(1, 1000)
        
        # LoremFlickr is very reliable for keyword-based placeholders
        return f"https://loremflickr.com/800/800/{clean_kw}/all?lock={seed}"

    def get_image_url(self, title, prompt=None, keywords=None, use_stock=False):
        """
        Unified method.
        """
        if use_stock:
            return self.get_stock_image_url(title, keywords)
        # Switch to JPG by default for Tistory
        return self.get_jpg_thumbnail(title)

    def generate_image(self, title, prompt=None, include_text=False):
        """
        Compatibility method.
        """
        return self.get_image_url(title)
