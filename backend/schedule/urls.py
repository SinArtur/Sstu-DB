"""URLs for schedule app."""
from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import (
    InstituteViewSet, GroupViewSet, TeacherViewSet,
    SubjectViewSet, LessonViewSet, ScheduleUpdateViewSet
)

router = DefaultRouter()
router.register(r'institutes', InstituteViewSet, basename='institute')
router.register(r'groups', GroupViewSet, basename='group')
router.register(r'teachers', TeacherViewSet, basename='teacher')
router.register(r'subjects', SubjectViewSet, basename='subject')
router.register(r'lessons', LessonViewSet, basename='lesson')
router.register(r'updates', ScheduleUpdateViewSet, basename='schedule-update')

urlpatterns = [
    path('', include(router.urls)),
]

