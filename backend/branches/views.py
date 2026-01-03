"""
Views for branches app.
"""
from rest_framework import generics, viewsets, status, permissions
from rest_framework.decorators import action
from rest_framework.response import Response
from django.db.models import Q
from .models import Branch, BranchRequest
from .serializers import (
    BranchSerializer, BranchTreeSerializer,
    BranchRequestSerializer, BranchRequestCreateSerializer
)


class BranchViewSet(viewsets.ModelViewSet):
    """ViewSet for Branch model."""
    
    queryset = Branch.objects.all()
    serializer_class = BranchSerializer
    permission_classes = [permissions.IsAuthenticated]
    
    def get_queryset(self):
        queryset = super().get_queryset()
        
        # Admins can see all branches, others see only approved
        if not self.request.user.is_admin:
            # Filter by status
            status_filter = self.request.query_params.get('status')
            if status_filter:
                queryset = queryset.filter(status=status_filter)
            else:
                # By default, show only approved branches for non-moderators
                if not self.request.user.can_moderate():
                    queryset = queryset.filter(status=Branch.Status.APPROVED)
        else:
            # Admins can filter by status if needed
            status_filter = self.request.query_params.get('status')
            if status_filter:
                queryset = queryset.filter(status=status_filter)
        
        # Filter by type
        type_filter = self.request.query_params.get('type')
        if type_filter:
            queryset = queryset.filter(type=type_filter)
        
        # Filter by parent
        parent_id = self.request.query_params.get('parent')
        if parent_id:
            queryset = queryset.filter(parent_id=parent_id)
        elif parent_id == '':
            queryset = queryset.filter(parent__isnull=True)
        
        return queryset
    
    def get_queryset(self):
        queryset = super().get_queryset()
        
        # Filter by status
        status_filter = self.request.query_params.get('status')
        if status_filter:
            queryset = queryset.filter(status=status_filter)
        else:
            # By default, show only approved branches for non-moderators
            if not self.request.user.can_moderate():
                queryset = queryset.filter(status=Branch.Status.APPROVED)
        
        # Filter by type
        type_filter = self.request.query_params.get('type')
        if type_filter:
            queryset = queryset.filter(type=type_filter)
        
        # Filter by parent
        parent_id = self.request.query_params.get('parent')
        if parent_id:
            queryset = queryset.filter(parent_id=parent_id)
        elif parent_id == '':
            queryset = queryset.filter(parent__isnull=True)
        
        return queryset
    
    @action(detail=True, methods=['get'])
    def children(self, request, pk=None):
        """Get children of a branch."""
        branch = self.get_object()
        children = branch.children.filter(status=Branch.Status.APPROVED)
        serializer = self.get_serializer(children, many=True)
        return Response(serializer.data)
    
    @action(detail=False, methods=['get'])
    def tree(self, request):
        """Get full tree structure."""
        root_branches = Branch.objects.filter(
            parent__isnull=True,
            status=Branch.Status.APPROVED
        )
        serializer = BranchTreeSerializer(root_branches, many=True)
        return Response(serializer.data)
    
    def destroy(self, request, *args, **kwargs):
        """Delete branch (admin only)."""
        if not request.user.is_admin:
            return Response(
                {'error': 'Только администраторы могут удалять ветки'},
                status=status.HTTP_403_FORBIDDEN
            )
        return super().destroy(request, *args, **kwargs)
    
    @action(detail=False, methods=['get'])
    def search(self, request):
        """Search branches, materials and files."""
        query = request.query_params.get('q', '')
        if not query:
            return Response({'branches': [], 'materials': [], 'files': []})
        
        # Search branches by name
        branches = Branch.objects.filter(
            Q(name__icontains=query),
            status=Branch.Status.APPROVED
        ).select_related('parent')[:10]
        branch_serializer = self.get_serializer(branches, many=True)
        
        # Search materials
        from materials.models import Material, MaterialFile
        
        materials = Material.objects.filter(
            Q(description__icontains=query) | Q(tags__name__icontains=query),
            status=Material.Status.APPROVED
        ).select_related('author', 'branch').prefetch_related('files', 'tags').distinct()[:10]
        
        from materials.serializers import MaterialSerializer
        material_serializer = MaterialSerializer(materials, many=True, context={'request': request})
        
        # Search files
        files = MaterialFile.objects.filter(
            Q(original_name__icontains=query) | Q(comment__icontains=query),
            material__status=Material.Status.APPROVED
        ).select_related('material', 'material__branch')[:10]
        
        # Prepare file results with material and branch info
        file_results = []
        for file_obj in files:
            branch = file_obj.material.branch
            file_results.append({
                'id': file_obj.id,
                'original_name': file_obj.original_name,
                'file_size': file_obj.file_size,
                'file_type': file_obj.file_type,
                'comment': file_obj.comment,
                'material_id': file_obj.material.id,
                'material_description': (file_obj.material.description or '')[:100],
                'branch_id': branch.id,
                'branch_name': branch.name,
                'branch_path': branch.get_full_path() if hasattr(branch, 'get_full_path') else branch.name,
            })
        
        return Response({
            'branches': branch_serializer.data,
            'materials': material_serializer.data,
            'files': file_results
        })


class BranchRequestViewSet(viewsets.ModelViewSet):
    """ViewSet for BranchRequest model."""
    
    queryset = BranchRequest.objects.all()
    permission_classes = [permissions.IsAuthenticated]
    
    def get_serializer_class(self):
        if self.action == 'create':
            return BranchRequestCreateSerializer
        return BranchRequestSerializer
    
    def get_queryset(self):
        queryset = super().get_queryset()
        
        # Non-moderators see only their own requests
        if not self.request.user.can_moderate():
            queryset = queryset.filter(requester=self.request.user)
        
        # Filter by status
        status_filter = self.request.query_params.get('status')
        if status_filter:
            queryset = queryset.filter(status=status_filter)
        else:
            # Moderators see pending requests by default
            if self.request.user.can_moderate():
                queryset = queryset.filter(status=Branch.Status.PENDING)
        
        return queryset
    
    def perform_create(self, serializer):
        serializer.save(requester=self.request.user)
    
    @action(detail=True, methods=['post'])
    def approve(self, request, pk=None):
        """Approve branch request (moderator only)."""
        if not request.user.can_moderate():
            return Response(
                {'error': 'Недостаточно прав'},
                status=status.HTTP_403_FORBIDDEN
            )
        
        branch_request = self.get_object()
        comment = request.data.get('comment', '')
        
        try:
            branch = branch_request.approve(request.user, comment)
            serializer = BranchSerializer(branch)
            return Response({
                'message': 'Запрос одобрен',
                'branch': serializer.data
            })
        except Exception as e:
            return Response(
                {'error': str(e)},
                status=status.HTTP_400_BAD_REQUEST
            )
    
    @action(detail=True, methods=['post'])
    def reject(self, request, pk=None):
        """Reject branch request (moderator only)."""
        if not request.user.can_moderate():
            return Response(
                {'error': 'Недостаточно прав'},
                status=status.HTTP_403_FORBIDDEN
            )
        
        branch_request = self.get_object()
        comment = request.data.get('comment', '')
        
        if not comment:
            return Response(
                {'error': 'Комментарий обязателен при отклонении'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        try:
            branch_request.reject(request.user, comment)
            serializer = self.get_serializer(branch_request)
            return Response({
                'message': 'Запрос отклонен',
                'request': serializer.data
            })
        except Exception as e:
            return Response(
                {'error': str(e)},
                status=status.HTTP_400_BAD_REQUEST
            )

