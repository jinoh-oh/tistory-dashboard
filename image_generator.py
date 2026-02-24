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
        Dynamically finds available Korean-supporting fonts on Windows and Linux (Streamlit Cloud).
        """
        import os
        import glob
        
        # Paths to search based on OS
        search_dirs = []
        if os.name == 'nt': # Windows
            search_dirs = [r"C:\Windows\Fonts"]
        else: # Linux / Streamlit Cloud
            search_dirs = [
                "/usr/share/fonts",
                "/usr/local/share/fonts",
                "~/.fonts"
            ]
        
        patterns = [
            "*malgun*", "*nanum*", "*gulim*", "*dotum*", "*batang*",
            "*noto*korean*", "*noto*cjk*", "*unfonts*", "*baekmuk*"
        ]
        
        found_fonts = []
        for d in search_dirs:
            d = os.path.expanduser(d)
            if not os.path.exists(d): continue
            
            for p in patterns:
                # Recursive search for .ttf and .ttc
                full_pattern = os.path.join(d, "**", p + ".t*")
                matches = glob.glob(full_pattern, recursive=True)
                if matches:
                    # Prioritize bold or medium weights
                    priority = [m for m in matches if any(x in m.lower() for x in ['bold', 'bd', 'medium', 'eb'])]
                    found_fonts.extend(priority if priority else matches)
        
        return list(dict.fromkeys(found_fonts)) # Deduplicate

    def get_jpg_thumbnail(self, text):
        """
        Generates a 800x800 JPG thumbnail using Pillow for Tistory compatibility.
        Works across Windows and Linux (Streamlit Cloud).
        """
        from PIL import Image, ImageDraw, ImageFont
        import io
        import base64
        import os
        
        # 1. Setup Canvas
        size = 800
        # Vibrant colors that work well with white text
        colors = ["#3b82f6", "#ef4444", "#10b981", "#f59e0b", "#8b5cf6", "#ec4899", "#06b6d4", "#f43f5e", "#6366f1"]
        bg_hex = random.choice(colors)
        img = Image.new('RGB', (size, size), color=bg_hex)
        draw = ImageDraw.Draw(img)
        
        # 2. Text Preparation
        display_text = text.strip()
        if not display_text.endswith(">"):
            display_text += " >"
            
        # 3. Smart Font Discovery
        font_paths = self._find_system_fonts()
        
        font = None
        font_size = 110 # Premium large size
        
        for f_path in font_paths:
            try:
                font = ImageFont.truetype(f_path, font_size)
                break
            except Exception:
                continue
        
        if not font:
            # Last ditch effort for Linux (Streamlit Cloud)
            linux_fallbacks = [
                "/usr/share/fonts/truetype/nanum/NanumGothicBold.ttf",
                "/usr/share/fonts/truetype/noto/NotoSansCJK-Bold.ttc"
            ]
            for lf in linux_fallbacks:
                try:
                    if os.path.exists(lf):
                        font = ImageFont.truetype(lf, font_size)
                        break
                except: continue
        
        if not font:
            font = ImageFont.load_default()
            
        # 4. Word Wrap (Max 3 lines, tight wrap)
        words = display_text.split()
        lines = []
        current_line = ""
        for word in words:
            if len(current_line + word) <= 7: 
                current_line += (word + " ")
            else:
                if current_line: lines.append(current_line.strip())
                current_line = word + " "
        if current_line: lines.append(current_line.strip())
        lines = lines[:3]
        
        # 5. Draw Text with "Glow" Outline (Premium YouTube Style)
        line_height = 145
        total_text_height = len(lines) * line_height
        start_y = (size - total_text_height) // 2
        
        for i, line in enumerate(lines):
            try:
                left, top, right, bottom = draw.textbbox((0, 0), line, font=font)
                w = right - left
            except AttributeError:
                w = draw.textlength(line, font=font)
                
            x = (size - w) // 2
            y = start_y + (i * line_height)
            
            # Ultra Thick Shadow for maximum legibility
            for dx in range(-6, 7, 2):
                for dy in range(-6, 7, 2):
                    draw.text((x+dx, y+dy), line, fill="#111111", font=font)
            
            # Main Bold Text
            draw.text((x, y), line, fill="white", font=font)

        # 6. Export to Base64 JPG
        buffered = io.BytesIO()
        img.save(buffered, format="JPEG", quality=90)
        encoded = base64.b64encode(buffered.getvalue()).decode('utf-8')
        return f"data:image/jpeg;base64,{encoded}"

    def translate_keyword(self, text):
        """
        Maps Korean terms to English for stock photo relevance.
        Prioritizes semantic meaning over literal translation.
        """
        if not text: return "lifestyle"
        
        text_lower = text.lower()
        # High relevance triggers
        if "수면" in text_lower or "숙면" in text_lower: return "bed"
        if "부종" in text_lower or "부은" in text_lower: return "spa"
        if "다이어트" in text_lower: return "healthy"
        if "운동" in text_lower or "헬스" in text_lower: return "workout"
        
        for ko, en in self.COMMON_TOPICS.items():
            if ko in text_lower:
                return en
        # Fallback to first ASCII word or generic tag
        clean = "".join([c if (c.isalpha() or c == ' ') else ' ' for c in text if ord(c) < 128])
        parts = clean.split()
        return parts[0] if parts else "nature"

    def get_stock_image_url(self, title, keywords=None):
        """
        Returns a high-quality stock photo URL using LoremFlickr.
        Reduces multi-keyword pollution for better visual relevance.
        """
        target = keywords if keywords else title
        kw = self.translate_keyword(target)
        
        # LoremFlickr works best with single, strong keywords
        primary_kw = kw.split(',')[0].strip()
        seed = random.randint(1, 1000)
        return f"https://loremflickr.com/800/800/{urllib.parse.quote(primary_kw)}?lock={seed}"

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
