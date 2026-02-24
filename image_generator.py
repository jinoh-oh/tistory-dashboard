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

    def _find_system_fonts(self):
        """
        Intelligently finds available Korean fonts on Windows.
        """
        import os
        import glob
        
        search_patterns = [
            r"C:\Windows\Fonts\malgun*.t*", 
            r"C:\Windows\Fonts\gulim.t*", 
            r"C:\Windows\Fonts\batang.t*",
            r"C:\Windows\Fonts\dotum.t*",
            r"C:\Windows\Fonts\Nanum*.t*"
        ]
        
        found_fonts = []
        for pattern in search_patterns:
            matches = glob.glob(pattern)
            if matches:
                # Prioritize bold versions if available
                bold_matches = [m for m in matches if 'bd' in m.lower() or 'bold' in m.lower()]
                found_fonts.extend(bold_matches if bold_matches else matches)
        
        return list(dict.fromkeys(found_fonts)) # Deduplicate

    def get_jpg_thumbnail(self, text):
        """
        Generates a 800x800 JPG thumbnail using Pillow for Tistory compatibility.
        Features high-quality Korean typography and visual polish.
        """
        from PIL import Image, ImageDraw, ImageFont
        import io
        import base64
        import os
        
        # 1. Setup Canvas
        size = 800
        colors = ["#3b82f6", "#ef4444", "#10b981", "#f59e0b", "#8b5cf6", "#ec4899", "#06b6d4", "#f43f5e", "#10b981"]
        bg_hex = random.choice(colors)
        img = Image.new('RGB', (size, size), color=bg_hex)
        draw = ImageDraw.Draw(img)
        
        # 2. Text Preparation
        display_text = text.strip()
        if not display_text.endswith(">"):
            display_text += " >"
            
        # 3. Force Priority Font Path
        priority_paths = [
            r"C:\Windows\Fonts\malgunbd.ttf",
            r"C:\Windows\Fonts\malgun.ttf",
            r"C:\Windows\Fonts\gulim.ttc",
            r"C:\Windows\Fonts\batang.ttc"
        ]
        
        # Add dynamically found fonts
        font_paths = priority_paths + self._find_system_fonts()
        font_paths.append("arial.ttf") 
        
        font = None
        font_size = 100
        for f_path in font_paths:
            try:
                if os.path.exists(f_path):
                    # Handle .ttc by taking the first font in the collection
                    font = ImageFont.truetype(f_path, font_size)
                    break
            except Exception:
                continue
        
        if not font:
            font = ImageFont.load_default()
            
        # 4. Word Wrap (Max 3 lines, max 8 chars per line)
        words = display_text.split()
        lines = []
        current_line = ""
        for word in words:
            if len(current_line + word) <= 8: # Tighter wrap for large fonts
                current_line += (word + " ")
            else:
                if current_line: lines.append(current_line.strip())
                current_line = word + " "
        if current_line: lines.append(current_line.strip())
        lines = lines[:3]
        
        # 5. Draw Text with Strong Outline (Premium YouTube Style)
        line_height = 135
        total_text_height = len(lines) * line_height
        start_y = (size - total_text_height) // 2
        
        for i, line in enumerate(lines):
            # Calculate centering
            try:
                left, top, right, bottom = draw.textbbox((0, 0), line, font=font)
                w = right - left
            except AttributeError:
                w = draw.textlength(line, font=font)
                
            x = (size - w) // 2
            y = start_y + (i * line_height)
            
            # Ultra Thick Outline for maximum readability on complex backgrounds
            for dx in range(-8, 9, 2):
                for dy in range(-8, 9, 2):
                    draw.text((x+dx, y+dy), line, fill="black", font=font)
            
            # Main Bold Text
            draw.text((x, y), line, fill="white", font=font)

        # 6. Export to Base64 JPG
        buffered = io.BytesIO()
        img.save(buffered, format="JPEG", quality=90)
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
        # Extract first ASCII word
        clean = "".join([c if (c.isalpha() or c == ' ') else ' ' for c in text if ord(c) < 128])
        parts = clean.split()
        return parts[0] if parts else "lifestyle"

    def get_stock_image_url(self, title, keywords=None):
        """
        Returns a high-quality stock photo URL using LoremFlickr (highly reliable).
        """
        target = keywords if keywords else title
        kw = self.translate_keyword(target)
        
        # LoremFlickr format: https://loremflickr.com/800/800/keyword
        # It's very stable and doesn't 503 like Unsplash Source often does
        seed = random.randint(1, 1000)
        return f"https://loremflickr.com/800/800/{urllib.parse.quote(kw)}?lock={seed}"

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
