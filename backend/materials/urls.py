"""
URLs for materials app.
"""
from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import MaterialViewSet, MaterialCommentViewSet, MaterialTagViewSet

router = DefaultRouter()
router.register(r'comments', MaterialCommentViewSet, basename='material-comment')
router.register(r'tags', MaterialTagViewSet, basename='material-tag')
router.register(r'', MaterialViewSet, basename='material')

urlpatterns = [
    path('', include(router.urls)),
]

