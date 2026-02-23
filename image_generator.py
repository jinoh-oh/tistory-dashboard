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
        # Sanitize: ASCII ONLY
        clean_query = "".join([c for c in raw_query if (c.isalnum() or c == ' ') and ord(c) < 128])
        
        if not clean_query.strip():
            clean_query = "blog feature image"
            
        # Use simple quote for the whole string. 
        # Pollinations handles spaces well if quoted.
        search_query = clean_query[:70].strip()
        encoded_prompt = urllib.parse.quote(search_query)
        
        seed = random.randint(1, 1000000)
        return f"https://image.pollinations.ai/prompt/{encoded_prompt}?width={width}&height={height}&nologo=true&seed={seed}&enhance=true"

    def get_stock_image_url(self, title, keywords=None):
        """
        Returns a high-quality stock photo URL from LoremFlickr.
        """
        raw_query = keywords if keywords else title
        # ENSURE ASCII ONLY for the URL path
        clean_query = "".join([c for c in raw_query if (c.isalnum() or c == ' ' or c == ',') and ord(c) < 128])
        
        # Take the FIRST 1-2 keywords only. Too many keywords = cats.
        # Split by comma or space
        parts = [p.strip() for p in clean_query.replace(',', ' ').split() if p.strip()]
        if not parts:
            final_keywords = "nature"
        else:
            # Take only the first two words for maximum relevance in LoremFlickr
            final_keywords = ",".join(parts[:2])
            
        # Use 'lock' param for consistency
        return f"https://loremflickr.com/800/800/{final_keywords}?lock={random.randint(1, 1000)}"

    def get_image_url(self, title, prompt=None, keywords=None, use_stock=False):
        """
        Unified method to get image URL.
        """
        if use_stock:
            return self.get_stock_image_url(title, keywords)
        
        # Default strategy: Try AI first, but if it's the first load, 
        # we might want to ensure keywords are passed.
        return self.get_ai_image_url(title, prompt)

    def generate_image(self, title, prompt=None, include_text=False):
        """
        Compatibility method. Now just returns the URL.
        """
        return self.get_image_url(title, prompt)
