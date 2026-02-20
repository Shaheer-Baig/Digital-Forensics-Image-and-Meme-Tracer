import imagehash
from PIL import Image
import requests
from io import BytesIO

class Hasher:
    @staticmethod
    def compute_phash(image_path_or_obj):
        """Computes the perceptual hash of an image."""
        try:
            if isinstance(image_path_or_obj, str):
                img = Image.open(image_path_or_obj)
            else:
                img = image_path_or_obj
            
            return imagehash.phash(img)
        except Exception as e:
            print(f"Hashing Error: {e}")
            return None

    @staticmethod
    def download_image(url):
        """Downloads an image from a URL and returns a PIL Image object."""
        try:
            response = requests.get(url, timeout=10)
            response.raise_for_status()
            return Image.open(BytesIO(response.content))
        except Exception as e:
            print(f"Download Error {url}: {e}")
            return None
