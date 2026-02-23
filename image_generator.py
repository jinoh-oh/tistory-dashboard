import urllib.parse
import random

class ImageGenerator:
    def __init__(self, output_dir="generated_images"):
        self.output_dir = output_dir

    def get_ai_image_url(self, title, prompt=None):
        """
        Constructs and returns a Pollinations.ai URL for the image.
        Uses a sanitized, truncated prompt for stability.
        """
        width, height = 800, 800
        # Use simpler prompt and sanitize for URL stability
        raw_query = prompt if prompt else title
        # Sanitize: Remove commas, dots, special chars and truncate
        clean_query = "".join([c for c in raw_query if c.isalnum() or c == ' '])
        search_query = clean_query[:60].strip()
        
        encoded_prompt = urllib.parse.quote(search_query)
        seed = random.randint(1, 1000000)
        
        return f"https://image.pollinations.ai/prompt/{encoded_prompt}?width={width}&height={height}&nologo=true&seed={seed}&enhance=true"

    def get_stock_image_url(self, title):
        """
        Returns a high-quality stock photo URL from LoremFlickr.
        Very stable and fast.
        """
        # LoremFlickr uses simple keywords
        clean_query = "".join([c for c in title if c.isalnum() or c == ' '])
        keywords = urllib.parse.quote(clean_query[:30].strip())
        return f"https://loremflickr.com/800/800/{keywords}?random={random.randint(1, 1000)}"

    def get_image_url(self, title, prompt=None, use_stock=False):
        """
        Unified method to get image URL.
        """
        if use_stock:
            return self.get_stock_image_url(title)
        return self.get_ai_image_url(title, prompt)

    def generate_image(self, title, prompt=None, include_text=False):
        """
        Compatibility method. Now just returns the URL.
        """
        return self.get_image_url(title, prompt)
