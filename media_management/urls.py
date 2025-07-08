from django.urls import path
from .views import ImageUploadView, ImageDetailView

app_name = 'media_management'

urlpatterns = [
    path('upload/', ImageUploadView.as_view(), name='image-upload'),
    path('images/', ImageUploadView.as_view(), name='image-list'),
    path('images/<uuid:image_id>/', ImageDetailView.as_view(), name='image-detail'),
]