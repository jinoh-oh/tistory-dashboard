import os
import requests
import random
import urllib.parse

class ImageGenerator:
    def __init__(self, output_dir="generated_images"):
        self.output_dir = output_dir
        if not os.path.exists(self.output_dir):
            os.makedirs(self.output_dir)

    def generate_image(self, title, prompt=None, include_text=False):
        """
        Generates a blog cover image. 
        Uses Pollinations.ai for real AI imagery.
        Size: 800x800 (Recommended for Tistory SEO)
        """
        width, height = 800, 800
        
        # Use provided prompt or fall back to title
        search_query = prompt if prompt else f"Refined, professional blog header for: {title}"
        
        # URL encode the prompt
        encoded_prompt = urllib.parse.quote(search_query)
        seed = random.randint(1, 1000000)
        
        # Pollinations.ai URL
        image_url = f"https://image.pollinations.ai/prompt/{encoded_prompt}?width={width}&height={height}&nologo=true&seed={seed}&enhance=true"
        
        filename = f"{self._clean_filename(title)}.jpg"
        filepath = os.path.join(self.output_dir, filename)

        try:
            # Download the image
            response = requests.get(image_url, timeout=20)
            if response.status_code == 200:
                with open(filepath, 'wb') as f:
                    f.write(response.content)
                return filepath
            else:
                raise Exception(f"Failed to download image: {response.status_code}")
        except Exception as e:
            print(f"AI Image Generation Error: {e}")
            # Fallback: Create a simple placeholder if external service fails
            from PIL import Image
            fallback_color = (random.randint(50, 150), random.randint(50, 150), random.randint(50, 150))
            img = Image.new('RGB', (width, height), fallback_color)
            img.save(filepath)
            return filepath

    def _clean_filename(self, text):
        # A simple filename cleaner
        return "".join([c for c in text if c.isalnum() or c in (' ', '-', '_')]).strip().replace(' ', '_')[:50]
