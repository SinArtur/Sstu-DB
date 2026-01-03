"""
URLs for branches app.
"""
from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import BranchViewSet, BranchRequestViewSet

router = DefaultRouter()
router.register(r'requests', BranchRequestViewSet, basename='branch-request')
router.register(r'', BranchViewSet, basename='branch')

urlpatterns = [
    path('', include(router.urls)),
]

