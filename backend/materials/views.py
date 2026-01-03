"""
Views for materials app.
"""
from rest_framework import viewsets, status, permissions
from rest_framework.decorators import action
from rest_framework.response import Response
from django.db.models import Q, Count, Avg
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework.filters import SearchFilter, OrderingFilter
from .models import Material, MaterialFile, MaterialRating, MaterialComment, MaterialTag
from .serializers import (
    MaterialSerializer, MaterialCreateSerializer,
    MaterialFileSerializer, MaterialRatingSerializer, MaterialRatingCreateSerializer,
    MaterialCommentSerializer, MaterialTagSerializer
)


class MaterialViewSet(viewsets.ModelViewSet):
    """ViewSet for Material model."""
    
    queryset = Material.objects.all()
    filter_backends = [DjangoFilterBackend, SearchFilter, OrderingFilter]
    filterset_fields = ['branch', 'status', 'author']
    search_fields = ['description', 'files__original_name', 'tags__name']
    ordering_fields = ['created_at', 'average_rating', 'downloads_count', 'views_count']
    ordering = ['-created_at']
    permission_classes = [permissions.IsAuthenticated]
    
    def get_serializer_class(self):
        if self.action == 'create':
            return MaterialCreateSerializer
        return MaterialSerializer
    
    def get_queryset(self):
        queryset = super().get_queryset()
        
        # Filter by status
        status_filter = self.request.query_params.get('status')
        if status_filter:
            queryset = queryset.filter(status=status_filter)
        else:
            # By default, show only approved materials for non-moderators
            if not self.request.user.can_moderate():
                queryset = queryset.filter(status=Material.Status.APPROVED)
        
        # Filter by branch
        branch_id = self.request.query_params.get('branch')
        if branch_id:
            queryset = queryset.filter(branch_id=branch_id)
        
        # Filter by author
        if self.request.query_params.get('my_materials') == 'true':
            queryset = queryset.filter(author=self.request.user)
        
        # Filter by tags
        tags = self.request.query_params.getlist('tags')
        if tags:
            queryset = queryset.filter(tags__name__in=tags).distinct()
        
        # Filter by file type
        file_type = self.request.query_params.get('file_type')
        if file_type:
            queryset = queryset.filter(files__file_type=file_type).distinct()
        
        queryset = queryset.select_related('author', 'branch', 'moderator').prefetch_related('files', 'tags')
        return queryset
    
    def create(self, request, *args, **kwargs):
        """Create material and return with MaterialSerializer."""
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        self.perform_create(serializer)
        
        # Get the created material and serialize with MaterialSerializer
        material = serializer.instance
        # Refresh to load related objects (tags, files)
        material.refresh_from_db()
        
        # Prefetch related objects for proper serialization
        from django.db.models import Prefetch
        material = Material.objects.prefetch_related(
            Prefetch('files'),
            Prefetch('tags')
        ).get(id=material.id)
        
        # Use MaterialSerializer for response
        response_serializer = MaterialSerializer(material, context={'request': request})
        headers = self.get_success_headers(response_serializer.data)
        return Response(response_serializer.data, status=status.HTTP_201_CREATED, headers=headers)
    
    def perform_create(self, serializer):
        serializer.save(author=self.request.user)
    
    @action(detail=True, methods=['post'])
    def rate(self, request, pk=None):
        """Rate material."""
        material = self.get_object()
        
        if material.status != Material.Status.APPROVED:
            return Response(
                {'error': 'Нельзя оценивать материалы, которые не одобрены'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        serializer = MaterialRatingCreateSerializer(
            data={'material': material.id, 'value': request.data.get('value')},
            context={'request': request}
        )
        serializer.is_valid(raise_exception=True)
        serializer.save()
        
        material.refresh_from_db()
        return Response({
            'message': 'Оценка сохранена',
            'average_rating': material.average_rating,
            'ratings_count': material.ratings_count
        })
    
    @action(detail=True, methods=['post'])
    def download(self, request, pk=None):
        """Increment download count."""
        material = self.get_object()
        material.downloads_count += 1
        material.save(update_fields=['downloads_count'])
        return Response({'message': 'Счетчик скачиваний обновлен'})
    
    @action(detail=True, methods=['get'], url_path='files/(?P<file_id>[^/.]+)/download')
    def download_file(self, request, pk=None, file_id=None):
        """Download a specific file from material."""
        from django.http import FileResponse, Http404
        from django.shortcuts import get_object_or_404
        
        material = self.get_object()
        try:
            material_file = MaterialFile.objects.get(id=file_id, material=material)
        except MaterialFile.DoesNotExist:
            raise Http404('Файл не найден')
        
        if not material_file.file:
            return Response(
                {'error': 'Файл не найден'},
                status=status.HTTP_404_NOT_FOUND
            )
        
        # Increment download count
        material.downloads_count += 1
        material.save(update_fields=['downloads_count'])
        
        # Open file and return response
        file_handle = material_file.file.open('rb')
        response = FileResponse(
            file_handle,
            content_type='application/octet-stream',
            as_attachment=True
        )
        response['Content-Disposition'] = f'attachment; filename="{material_file.original_name}"'
        return response
    
    @action(detail=True, methods=['get'], url_path='files/(?P<file_id>[^/.]+)/view')
    def view_file(self, request, pk=None, file_id=None):
        """View a specific file from material (opens in browser, doesn't download)."""
        import mimetypes
        from django.http import FileResponse, Http404
        from rest_framework_simplejwt.authentication import JWTAuthentication
        from rest_framework_simplejwt.exceptions import InvalidToken, TokenError
        
        # Support token in query parameter for iframe embedding
        token = request.query_params.get('token')
        if token:
            try:
                jwt_auth = JWTAuthentication()
                validated_token = jwt_auth.get_validated_token(token)
                user = jwt_auth.get_user(validated_token)
                request.user = user
            except (InvalidToken, TokenError):
                return Response(
                    {'error': 'Недействительный токен'},
                    status=status.HTTP_401_UNAUTHORIZED
                )
        
        material = self.get_object()
        try:
            material_file = MaterialFile.objects.get(id=file_id, material=material)
        except MaterialFile.DoesNotExist:
            raise Http404('Файл не найден')
        
        if not material_file.file:
            return Response(
                {'error': 'Файл не найден'},
                status=status.HTTP_404_NOT_FOUND
            )
        
        # Determine content type based on file extension
        content_type, _ = mimetypes.guess_type(material_file.original_name)
        if not content_type:
            # Default to application/octet-stream if type cannot be determined
            content_type = 'application/octet-stream'
        
        # Open file and return response for viewing (not downloading)
        file_handle = material_file.file.open('rb')
        response = FileResponse(
            file_handle,
            content_type=content_type,
            as_attachment=False
        )
        # Set inline disposition for viewing in browser
        response['Content-Disposition'] = f'inline; filename="{material_file.original_name}"'
        # Allow embedding in iframe
        response['X-Frame-Options'] = 'SAMEORIGIN'
        return response
    
    @action(detail=True, methods=['post'])
    def view(self, request, pk=None):
        """Increment view count."""
        material = self.get_object()
        material.views_count += 1
        material.save(update_fields=['views_count'])
        return Response({'message': 'Счетчик просмотров обновлен'})
    
    @action(detail=True, methods=['get'])
    def comments(self, request, pk=None):
        """Get comments for material."""
        material = self.get_object()
        comments = material.comments.filter(parent__isnull=True, is_deleted=False)
        serializer = MaterialCommentSerializer(comments, many=True, context={'request': request})
        return Response(serializer.data)
    
    @action(detail=True, methods=['post'])
    def approve(self, request, pk=None):
        """Approve material (moderator only)."""
        if not request.user.can_moderate():
            return Response(
                {'error': 'Недостаточно прав'},
                status=status.HTTP_403_FORBIDDEN
            )
        
        material = self.get_object()
        comment = request.data.get('comment', '')
        
        try:
            material.approve(request.user, comment)
            serializer = self.get_serializer(material)
            return Response({
                'message': 'Материал одобрен',
                'material': serializer.data
            })
        except Exception as e:
            return Response(
                {'error': str(e)},
                status=status.HTTP_400_BAD_REQUEST
            )
    
    @action(detail=True, methods=['post'])
    def reject(self, request, pk=None):
        """Reject material (moderator only)."""
        if not request.user.can_moderate():
            return Response(
                {'error': 'Недостаточно прав'},
                status=status.HTTP_403_FORBIDDEN
            )
        
        material = self.get_object()
        comment = request.data.get('comment', '')
        
        if not comment:
            return Response(
                {'error': 'Комментарий обязателен при отклонении'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        try:
            material.reject(request.user, comment)
            serializer = self.get_serializer(material)
            return Response({
                'message': 'Материал отклонен',
                'material': serializer.data
            })
        except Exception as e:
            return Response(
                {'error': str(e)},
                status=status.HTTP_400_BAD_REQUEST
            )


class MaterialCommentViewSet(viewsets.ModelViewSet):
    """ViewSet for MaterialComment model."""
    
    queryset = MaterialComment.objects.filter(is_deleted=False)
    serializer_class = MaterialCommentSerializer
    permission_classes = [permissions.IsAuthenticated]
    
    def get_queryset(self):
        queryset = super().get_queryset()
        material_id = self.request.query_params.get('material')
        if material_id:
            queryset = queryset.filter(material_id=material_id)
        return queryset.select_related('author', 'material')
    
    def perform_create(self, serializer):
        serializer.save(author=self.request.user)
    
    def perform_destroy(self, instance):
        # Soft delete
        instance.is_deleted = True
        instance.save()


class MaterialTagViewSet(viewsets.ReadOnlyModelViewSet):
    """ViewSet for MaterialTag model."""
    
    queryset = MaterialTag.objects.all()
    serializer_class = MaterialTagSerializer
    permission_classes = [permissions.IsAuthenticated]
    search_fields = ['name']
    
    @action(detail=False, methods=['get'])
    def popular(self, request):
        """Get popular tags."""
        tags = MaterialTag.objects.annotate(
            materials_count=Count('materials')
        ).filter(materials_count__gt=0).order_by('-materials_count')[:20]
        serializer = self.get_serializer(tags, many=True)
        return Response(serializer.data)

