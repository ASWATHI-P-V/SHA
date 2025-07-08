from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from rest_framework.parsers import MultiPartParser, FormParser
from django.shortcuts import get_object_or_404
from .models import ImageUpload
from .serializers import ImageUploadSerializer

def api_response(success, message, data=None, status_code=status.HTTP_200_OK):
    return Response({
        "success": success,
        "message": message,
        "data": data
    }, status=status_code)

class ImageUploadView(APIView):
    permission_classes = [IsAuthenticated]
    parser_classes = [MultiPartParser, FormParser]
    
    def post(self, request):
        """Upload a new image"""
        serializer = ImageUploadSerializer(data=request.data)
        if serializer.is_valid():
            image_upload = serializer.save(user=request.user)
            return api_response(
                True,
                "Image uploaded successfully",
                data=ImageUploadSerializer(image_upload).data,
                status_code=status.HTTP_201_CREATED
            )
        
        return api_response(
            False,
            "Image upload failed",
            data=serializer.errors,
            status_code=status.HTTP_400_BAD_REQUEST
        )
    
    def get(self, request):
        """Get user's uploaded images"""
        images = ImageUpload.objects.filter(user=request.user)
        serializer = ImageUploadSerializer(images, many=True)
        return api_response(
            True,
            "Images retrieved successfully",
            data=serializer.data
        )

class ImageDetailView(APIView):
    permission_classes = [IsAuthenticated]
    
    def get(self, request, image_id):
        """Get image details"""
        image = get_object_or_404(ImageUpload, id=image_id, user=request.user)
        serializer = ImageUploadSerializer(image)
        return api_response(
            True,
            "Image details retrieved successfully",
            data=serializer.data
        )
    
    def put(self, request, image_id):
        """Update image metadata (title, description)"""
        image = get_object_or_404(ImageUpload, id=image_id, user=request.user)
        serializer = ImageUploadSerializer(image, data=request.data, partial=True)
        
        if serializer.is_valid():
            serializer.save()
            return api_response(
                True,
                "Image updated successfully",
                data=serializer.data
            )
        
        return api_response(
            False,
            "Image update failed",
            data=serializer.errors,
            status_code=status.HTTP_400_BAD_REQUEST
        )
    
    def delete(self, request, image_id):
        """Delete an image"""
        image = get_object_or_404(ImageUpload, id=image_id, user=request.user)
        image.delete()
        return api_response(
            True,
            "Image deleted successfully",
            status_code=status.HTTP_204_NO_CONTENT
        )