"""
Views for moderation app.
"""
from rest_framework import viewsets, status, permissions
from rest_framework.decorators import action
from rest_framework.response import Response
from django.db.models import Q
from accounts.permissions import IsAdmin
from .models import ModerationLog, SystemSettings
from .serializers import ModerationLogSerializer, SystemSettingsSerializer


class ModerationLogViewSet(viewsets.ReadOnlyModelViewSet):
    """ViewSet for ModerationLog model."""
    
    queryset = ModerationLog.objects.all()
    serializer_class = ModerationLogSerializer
    permission_classes = [permissions.IsAuthenticated]
    
    def get_queryset(self):
        queryset = super().get_queryset()
        
        # Non-moderators see only logs related to their content
        if not self.request.user.can_moderate():
            # Filter by user's materials/branches
            queryset = queryset.filter(
                Q(content_type__model='material', object_id__in=self.request.user.uploaded_materials.values_list('id', flat=True)) |
                Q(content_type__model='branch', object_id__in=self.request.user.created_branches.values_list('id', flat=True))
            )
        
        # Filter by action
        action_filter = self.request.query_params.get('action')
        if action_filter:
            queryset = queryset.filter(action=action_filter)
        
        # Filter by content type
        content_type = self.request.query_params.get('content_type')
        if content_type:
            queryset = queryset.filter(content_type__model=content_type)
        
        return queryset.select_related('moderator', 'content_type')


class SystemSettingsViewSet(viewsets.ModelViewSet):
    """ViewSet for SystemSettings model."""
    
    queryset = SystemSettings.objects.all()
    serializer_class = SystemSettingsSerializer
    permission_classes = [permissions.IsAuthenticated]
    
    def get_permissions(self):
        if self.action in ['list', 'retrieve']:
            return [permissions.IsAuthenticated()]
        return [IsAdmin()]
    
    def perform_update(self, serializer):
        serializer.save(updated_by=self.request.user)
    
    def perform_create(self, serializer):
        serializer.save(updated_by=self.request.user)
    
    @action(detail=False, methods=['get'])
    def pending_count(self, request):
        """Get count of pending items for moderation."""
        if not request.user.can_moderate():
            return Response(
                {'error': 'Недостаточно прав'},
                status=status.HTTP_403_FORBIDDEN
            )
        
        from branches.models import BranchRequest
        from materials.models import Material
        
        branch_requests_count = BranchRequest.objects.filter(status='pending').count()
        materials_count = Material.objects.filter(status='pending').count()
        
        return Response({
            'branch_requests': branch_requests_count,
            'materials': materials_count,
            'total': branch_requests_count + materials_count
        })

