from PIL import Image, ImageDraw, ImageFont
import os
import random

class ImageGenerator:
    def __init__(self, output_dir="generated_images"):
        self.output_dir = output_dir
        if not os.path.exists(self.output_dir):
            os.makedirs(self.output_dir)

    def generate_image(self, title, prompt=None, include_text=False):
        """
        Generates a blog cover image. 
        Size: 800x800 (Recommended for Tistory SEO)
        """
        # Image settings (Square)
        width, height = 800, 800  
        background_color = self._get_random_color()
        text_color = (255, 255, 255)

        image = Image.new('RGB', (width, height), background_color)

        if include_text:
            draw = ImageDraw.Draw(image)
            
            # Font handling for Cloud/Local compatibility
            font_path = "NanumGothic.ttf"
            
            if not os.path.exists(font_path):
                # Try Windows default first if local
                if os.path.exists("C:/Windows/Fonts/malgun.ttf"):
                    font_path = "C:/Windows/Fonts/malgun.ttf"
                else:
                    # Download NanumGothic if not present (for Streamlit Cloud)
                    try:
                        import requests
                        url = "https://github.com/google/fonts/raw/main/ofl/nanumgothic/NanumGothic-Regular.ttf"
                        response = requests.get(url)
                        with open("NanumGothic.ttf", "wb") as f:
                            f.write(response.content)
                        font_path = "NanumGothic.ttf"
                    except Exception:
                        font_path = None # Fallback to default

            try:
                if font_path:
                    font = ImageFont.truetype(font_path, 60)
                else:
                    font = ImageFont.load_default()
            except IOError:
                font = ImageFont.load_default()

            # Wrap text
            lines = self._wrap_text(title, font, width - 100) # Padding
            
            # Draw text centered
            total_text_height = len(lines) * 80 # Line height
            y_text = (height - total_text_height) / 2
            
            for line in lines:
                bbox = draw.textbbox((0, 0), line, font=font)
                text_width = bbox[2] - bbox[0]
                
                x_text = (width - text_width) / 2
                
                # Subtle text shadow for better readability
                shadow_offset = 2
                draw.text((x_text + shadow_offset, y_text + shadow_offset), line, font=font, fill=(50, 50, 50))
                draw.text((x_text, y_text), line, font=font, fill=text_color)
                
                y_text += 80

        filename = f"{self._clean_filename(title)}.jpg"
        filepath = os.path.join(self.output_dir, filename)
        image.save(filepath)
        return filepath

    def _get_random_color(self):
        # Generate a pleasing dark color
        return (random.randint(20, 100), random.randint(20, 100), random.randint(20, 100))

    def _wrap_text(self, text, font, max_width):
        # A simple text wrapper
        lines = []
        words = text.split()
        current_line = []
        
        # Create a dummy draw object to measure text
        dummy_img = Image.new('RGB', (1, 1))
        draw = ImageDraw.Draw(dummy_img)

        for word in words:
            current_line.append(word)
            line_str = ' '.join(current_line)
            bbox = draw.textbbox((0, 0), line_str, font=font)
            width = bbox[2] - bbox[0]
            if width > max_width:
                current_line.pop()
                lines.append(' '.join(current_line))
                current_line = [word]
        
        if current_line:
            lines.append(' '.join(current_line))
        return lines

    def _clean_filename(self, text):
        return "".join([c for c in text if c.isalnum() or c in (' ', '-', '_')]).strip().replace(' ', '_')[:50]
