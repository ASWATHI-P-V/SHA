from django.db import models
from django.contrib.auth import get_user_model
import uuid
import os
from PIL import Image

User = get_user_model()

def get_image_upload_path(instance, filename):
    """Generate dynamic upload path for images"""
    ext = filename.split('.')[-1].lower()
    filename = f"{uuid.uuid4().hex}.{ext}"
    return f'images/{filename}'

class ImageUpload(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='uploaded_images')
    image = models.ImageField(upload_to=get_image_upload_path)
    original_filename = models.CharField(max_length=255)
    title = models.CharField(max_length=255, blank=True, null=True)
    description = models.TextField(blank=True, null=True)
    
    # Image metadata
    width = models.PositiveIntegerField(blank=True, null=True)
    height = models.PositiveIntegerField(blank=True, null=True)
    file_size = models.PositiveIntegerField(help_text="File size in bytes")
    
    # Timestamps
    uploaded_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['-uploaded_at']
        verbose_name = 'Image Upload'
        verbose_name_plural = 'Image Uploads'
    
    def __str__(self):
        return f"{self.original_filename} - {self.user.name or self.user.mobile_number}"
    
    def save(self, *args, **kwargs):
        if self.image:
            self.file_size = self.image.size
            self.original_filename = os.path.basename(self.image.name)
            
            # Get image dimensions
            try:
                with Image.open(self.image) as img:
                    self.width, self.height = img.size
            except Exception:
                pass
        
        super().save(*args, **kwargs)
    
    def get_image_url(self):
        """Get the image URL"""
        if self.image:
            return self.image.url
        return None