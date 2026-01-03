"""
URLs for moderation app.
"""
from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import ModerationLogViewSet, SystemSettingsViewSet

router = DefaultRouter()
router.register(r'logs', ModerationLogViewSet, basename='moderation-log')
router.register(r'settings', SystemSettingsViewSet, basename='system-settings')

urlpatterns = [
    path('', include(router.urls)),
]

