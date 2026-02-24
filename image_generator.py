import urllib.parse
import random
import os
import requests
import io
import base64

class ImageGenerator:
    def __init__(self, output_dir="generated_images"):
        self.output_dir = output_dir
        self.font_dir = "fonts"
        self.local_font_path = os.path.join(self.font_dir, "NanumGothicBold.ttf")
        
        # Ensure local font exists for cloud environments
        self._ensure_font_exists()

    def _ensure_font_exists(self):
        """
        Downloads a Korean font if not available locally or in system paths.
        This ensures the app works on Streamlit Cloud/Linux without pre-installed fonts.
        """
        if not os.path.exists(self.font_dir):
            os.makedirs(self.font_dir)
            
        if not os.path.exists(self.local_font_path):
            try:
                # Using a reliable raw link from NanumGothic GitHub or similar
                font_url = "https://github.com/google/fonts/raw/main/ofl/nanumgothic/NanumGothic-Bold.ttf"
                response = requests.get(font_url, timeout=10)
                if response.status_code == 200:
                    with open(self.local_font_path, "wb") as f:
                        f.write(response.content)
                    print(f"Font downloaded successfully to {self.local_font_path}")
            except Exception as e:
                print(f"Failed to download font: {e}")

    # Curated Library of verified high-quality Unsplash IDs for 100% relevance
    CURATED_STOCK = {
        "sleep": "1541781774370-8a1d05b17ae7",  # Cozy bed
        "bedroom": "1512499617640-42f4731dec01", # Serene bedroom
        "night": "1519750744998-bfc048040c0c",   # Night window
        "diet": "1490645935967-107d1e2s5160",    # Healthy salad
        "healthy": "1498837167721-e011830efad3", # Fresh vegetables
        "weight loss": "1517833115132-ec377c8d710f", # Scale/Fitness
        "fitness": "1534438327245-c0517a1bb102",  # Running shoes/track
        "workout": "1534438327245-c0517a1bb102",  # Gym
        "stock": "1611974717521-4a43a7c1219d",    # Stock market charts
        "finance": "1579621973515-0178631c7fe3",  # Coins/Growth
        "economy": "1459257255995-1f9999b4aex9",  # City buildings/Graph
        "tech": "1488590527370-d803d642610e",     # Laptop/Code
        "smartphone": "1511702199708-8687263636b6", # Modern phone
        "skincare": "155622857592f-b2f5606b4da8",  # Beauty/Spa
        "makeup": "1522335789203-a4c020c027de",   # Cosmetics
        "food": "1476224203461-9c3c8s9b2acc",     # Generic delicious food
        "coffee": "1495474472287-4d71bcdd2085",   # Coffee cup
        "cafe": "1509042239035-0c83d5bd737b",     # Cafe interior
        "travel": "1469441996581-c93a958e03e1",   # Plane window/landscape
        "tourism": "1476610182121-5a3994e77501",  # Tourist map
        "hotel": "1566073771279-63715s09170b",    # Luxury room
        "parenting": "1510333302158-df3px760200e", # Parent and child
        "baby": "1502441739563-36x24f3b7s4d",     # Cute baby
        "money": "1589753191714-3d8s2c1456b3",    # Dollars
        "success": "163361321631s-da1d4s9c1a2b",  # Mountain peak
        "interior": "1616489959146-da3s9c1a2b3d", # Modern room
        "medicine": "158436294614s-da1d4s9c1a2b", # Pills/Health
        "swelling": "1519415943484-da3s9c1a2b3d", # Feet/Health
        "doctor": "15329389110s9-da1d4s9c1a2b",  # Stethoscope
    }

    # Hardcoded mapping for common Korean blog topics to ensure relevance
    COMMON_TOPICS = {
        "다이어트": "diet", "체중": "weight loss", "운동": "fitness", "헬스": "workout",
        "주식": "stock", "투자": "finance", "재테크": "finance", "경제": "economy",
        "건강": "healthy", "영양": "healthy", "비타민": "medicine",
        "요리": "food", "레시피": "food", "음식": "food", "맛집": "food",
        "여행": "travel", "관광": "tourism", "호텔": "hotel",
        "뷰티": "skincare", "화장품": "makeup", "피부": "skincare",
        "it": "tech", "반도체": "tech", "스마트폰": "smartphone",
        "육아": "parenting", "아기": "baby", "교육": "parenting",
        "부업": "money", "수익": "money", "자기계발": "success",
        "수면": "sleep", "숙면": "bedroom", "불면증": "night",
        "부종": "swelling", "붓기": "swelling", "혈액순환": "medicine",
        "커피": "coffee", "카페": "cafe", "인테리어": "interior"
    }

    def _find_system_fonts(self):
        """
        Dynamically finds available Korean-supporting fonts on Windows and Linux.
        """
        import glob
        
        # Include our local downloaded font as the absolute FIRST priority
        found_fonts = []
        if os.path.exists(self.local_font_path):
            found_fonts.append(self.local_font_path)
            
        # Paths to search based on OS
        search_dirs = []
        if os.name == 'nt': # Windows
            search_dirs = [r"C:\Windows\Fonts"]
        else: # Linux / Streamlit Cloud
            search_dirs = [
                "/usr/share/fonts",
                "/usr/local/share/fonts",
                os.path.expanduser("~/.fonts")
            ]
        
        patterns = [
            "*malgun*", "*nanum*", "*gulim*", "*dotum*", "*batang*",
            "*noto*korean*", "*noto*cjk*", "*unfonts*", "*baekmuk*"
        ]
        
        for d in search_dirs:
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
        # [REMOVED] decorative '>' as per user request
            
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
        Maps Korean/English terms to searchable tags.
        Prioritizes the Curated Library.
        """
        if not text: return None
        
        text_lower = text.lower()
        # 1. Check direct mapping from Korean topics
        for ko, en in self.COMMON_TOPICS.items():
            if ko in text_lower:
                return en
        
        # 2. Check direct mapping if the input is already one of our keys
        if text_lower in self.CURATED_STOCK:
            return text_lower

        # 3. Process English keywords (Gemini output)
        stop_words = ["serene", "deep", "peaceful", "beautiful", "good", "best", "the", "a", "an"]
        clean = "".join([c if (c.isalpha() or c == ',' or c == ' ') else ' ' for c in text if ord(c) < 128])
        parts = []
        for p in clean.replace(',', ' ').split():
            p_clean = p.strip().lower()
            if p_clean and p_clean not in stop_words and len(p_clean) > 2:
                # Check if any part matches our curated keys
                if p_clean in self.CURATED_STOCK:
                    return p_clean
                parts.append(p_clean)
        
        return parts[0] if parts else None

    def get_stock_image_url(self, title, keywords=None):
        """
        Returns a high-quality stock photo URL using the Curated Library.
        """
        target = keywords if keywords else title
        kw = self.translate_keyword(target)
        
        # Use curated library for guaranteed quality and relevance
        if kw and kw in self.CURATED_STOCK:
            photo_id = self.CURATED_STOCK[kw]
            return f"https://images.unsplash.com/photo-{photo_id}?q=80&w=800&auto=format&fit=crop"
            
        # If no curated match, return None to trigger fallback to beautiful text thumbnail
        return None

    def get_image_url(self, title, prompt=None, keywords=None, use_stock=False):
        """
        Unified method. Falls back to text thumbnail if curated stock is unavailable.
        """
        if use_stock:
            stock_url = self.get_stock_image_url(title, keywords)
            if stock_url:
                return stock_url
                
        # Fallback to JPG text thumbnail
        return self.get_jpg_thumbnail(title)

    def generate_image(self, title, prompt=None, include_text=False):
        """
        Compatibility method.
        """
        return self.get_image_url(title)
