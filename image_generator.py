import urllib.parse
import random

class ImageGenerator:
    def __init__(self, output_dir="generated_images"):
        self.output_dir = output_dir

    def get_image_url(self, title, prompt=None):
        """
        Constructs and returns a Pollinations.ai URL for the image.
        """
        width, height = 800, 800
        # AI generated prompts can be too long for URLs. Truncate to be safe.
        raw_query = prompt if prompt else f"Refined, professional blog header for: {title}"
        search_query = raw_query[:250] 
        
        encoded_prompt = urllib.parse.quote(search_query)
        seed = random.randint(1, 1000000)
        
        return f"https://image.pollinations.ai/prompt/{encoded_prompt}?width={width}&height={height}&nologo=true&seed={seed}&enhance=true"

    def generate_image(self, title, prompt=None, include_text=False):
        """
        Compatibility method. Now just returns the URL.
        """
        return self.get_image_url(title, prompt)
