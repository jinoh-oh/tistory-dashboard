import urllib.parse
import random

class ImageGenerator:
    def __init__(self, output_dir="generated_images"):
        self.output_dir = output_dir

    def get_ai_image_url(self, title, prompt=None):
        """
        Constructs and returns a Pollinations.ai URL for the image.
        """
        width, height = 800, 800
        # AI Prompt Strategy: Use ASCII-ONLY in the URL itself to prevent blocks.
        # AI can still understand "Thumbnail with Korean text X" if encoded, 
        # but pure ASCII is the safest way to avoid 403 Forbidden on the request itself.
        raw_query = prompt if prompt else f"Thumbnail for {title}"
        
        # STRICT ASCII FILTER for the URL Path segment
        # This is the single most important fix for 403 Forbidden / 1033 errors
        clean_query = "".join([c for c in raw_query if (c.isalnum() or c == ' ') and ord(c) < 128])
        
        if not clean_query.strip():
            clean_query = "professional blog thumbnail"
            
        # Replace spaces with '+' for stability
        search_query = clean_query[:100].strip().replace(' ', '+')
        
        seed = random.randint(1, 1000000)
        return f"https://image.pollinations.ai/prompt/{search_query}?width={width}&height={height}&nologo=true&seed={seed}&enhance=true"

    def get_stock_image_url(self, title, keywords=None):
        """
        Returns a high-quality stock photo URL from LoremFlickr.
        """
        raw_query = keywords if keywords else title
        # ENSURE ASCII ONLY
        clean_query = "".join([c for c in raw_query if (c.isalnum() or c == ' ' or c == ',') and ord(c) < 128])
        
        # Take ONLY THE FIRST WORD. LoremFlickr returns cats if it matches multiple words poorly.
        # Single broad word (e.g., 'diet') is much more reliable than 'diet,food,health'.
        parts = [p.strip() for p in clean_query.replace(',', ' ').split() if p.strip()]
        
        if not parts:
            final_keyword = "nature"
        else:
            final_keyword = parts[0] # Take only the top-level keyword
            
        # Use 'lock' param for consistency
        return f"https://loremflickr.com/800/800/{final_keyword}?lock={random.randint(1, 1000)}"

    def get_image_url(self, title, prompt=None, keywords=None, use_stock=False):
        """
        Unified method to get image URL.
        """
        if use_stock:
            return self.get_stock_image_url(title, keywords)
        return self.get_ai_image_url(title, prompt)

    def generate_image(self, title, prompt=None, include_text=False):
        """
        Compatibility method.
        """
        return self.get_image_url(title, prompt)
