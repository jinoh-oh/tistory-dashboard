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
        # Sanitize: ASCII ONLY, No special chars except spaces for now
        clean_query = "".join([c for c in raw_query if (c.isalnum() or c == ' ') and ord(c) < 128])
        
        if not clean_query.strip():
            clean_query = "blog feature image"
            
        # VERY IMPORTANT: Replace spaces with '+' for URL stability
        # This prevents %20 in the path which some WAFs/Origins block
        search_query = clean_query[:60].strip().replace(' ', '+')
        
        seed = random.randint(1, 1000000)
        return f"https://image.pollinations.ai/prompt/{search_query}?width={width}&height={height}&nologo=true&seed={seed}&enhance=true"

    def get_stock_image_url(self, title, keywords=None):
        """
        Returns a high-quality stock photo URL from LoremFlickr.
        Very stable and fast.
        """
        raw_query = keywords if keywords else title
        # ENSURE ASCII ONLY for the URL path
        clean_query = "".join([c for c in raw_query if (c.isalnum() or c == ' ') and ord(c) < 128])
        
        if not clean_query.strip():
            clean_query = "nature professional"
            
        # LoremFlickr: Multiple tags MUST be separated by commas, NOT spaces.
        final_keywords = clean_query[:40].strip().replace(' ', ',')
        
        # Use 'lock' param for consistency, it's more stable than 'random' query param
        return f"https://loremflickr.com/800/800/{final_keywords}?lock={random.randint(1, 1000)}"

    def get_image_url(self, title, prompt=None, keywords=None, use_stock=False):
        """
        Unified method to get image URL.
        """
        if use_stock:
            return self.get_stock_image_url(title, keywords)
        return self.get_ai_image_url(title, prompt)

    def generate_image(self, title, prompt=None, include_text=False):
        """
        Compatibility method. Now just returns the URL.
        """
        return self.get_image_url(title, prompt)
