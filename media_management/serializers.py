from rest_framework import serializers
from .models import ImageUpload
from .validators import ImageSizeValidator, ImageDimensionValidator, image_extension_validator



class ImageUploadSerializer(serializers.ModelSerializer):
    image_url = serializers.SerializerMethodField()

    class Meta:
        model = ImageUpload
        fields = ['id', 'image_url']

    def get_image_url(self, obj):
        return obj.get_image_url()

