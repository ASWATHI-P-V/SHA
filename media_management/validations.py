from django.core.exceptions import ValidationError
from django.core.validators import FileExtensionValidator
from django.utils.deconstruct import deconstructible
from PIL import Image

@deconstructible
class ImageSizeValidator:
    """Validate image file size"""
    def __init__(self, max_size_mb=5):
        self.max_size = max_size_mb * 1024 * 1024  # Convert to bytes
    
    def __call__(self, image):
        if image.size > self.max_size:
            raise ValidationError(f'Image size cannot exceed {self.max_size // (1024*1024)}MB')

@deconstructible
class ImageDimensionValidator:
    """Validate image dimensions"""
    def __init__(self, max_width=4000, max_height=4000):
        self.max_width = max_width
        self.max_height = max_height
    
    def __call__(self, image):
        try:
            with Image.open(image) as img:
                width, height = img.size
                if width > self.max_width or height > self.max_height:
                    raise ValidationError(
                        f'Image dimensions cannot exceed {self.max_width}x{self.max_height} pixels'
                    )
        except Exception as e:
            raise ValidationError('Invalid image file')

# Common validators
image_extension_validator = FileExtensionValidator(
    allowed_extensions=['jpg', 'jpeg', 'png', 'gif', 'webp']
)