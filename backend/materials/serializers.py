"""
Serializers for materials app.
"""
from rest_framework import serializers
from django.contrib.auth import get_user_model
from .models import Material, MaterialFile, MaterialRating, MaterialComment, MaterialTag

User = get_user_model()


class MaterialFileSerializer(serializers.ModelSerializer):
    """Serializer for MaterialFile model."""
    
    file_url = serializers.SerializerMethodField()
    file_size_mb = serializers.SerializerMethodField()
    
    class Meta:
        model = MaterialFile
        fields = [
            'id', 'file', 'file_url', 'original_name', 'file_size',
            'file_size_mb', 'file_type', 'comment', 'upload_order', 'created_at'
        ]
        read_only_fields = ['id', 'file_size', 'file_type', 'created_at']
    
    def get_file_url(self, obj):
        if obj.file:
            request = self.context.get('request')
            if request:
                return request.build_absolute_uri(obj.file.url)
            return obj.file.url
        return None
    
    def get_file_size_mb(self, obj):
        return round(obj.file_size / 1024 / 1024, 2)


class MaterialTagSerializer(serializers.ModelSerializer):
    """Serializer for MaterialTag model."""
    
    class Meta:
        model = MaterialTag
        fields = ['id', 'name']


class MaterialCommentSerializer(serializers.ModelSerializer):
    """Serializer for MaterialComment model."""
    
    author_email = serializers.EmailField(source='author.email', read_only=True)
    author_name = serializers.SerializerMethodField()
    replies_count = serializers.SerializerMethodField()
    replies = serializers.SerializerMethodField()
    
    class Meta:
        model = MaterialComment
        fields = [
            'id', 'material', 'author', 'author_email', 'author_name',
            'text', 'parent', 'replies_count', 'replies',
            'created_at', 'updated_at', 'is_deleted'
        ]
        read_only_fields = ['id', 'author', 'created_at', 'updated_at', 'is_deleted']
    
    def get_author_name(self, obj):
        if obj.author.first_name or obj.author.last_name:
            return f"{obj.author.first_name} {obj.author.last_name}".strip()
        return obj.author.email.split('@')[0]
    
    def get_replies_count(self, obj):
        return obj.replies.filter(is_deleted=False).count()
    
    def get_replies(self, obj):
        replies = obj.replies.filter(is_deleted=False).order_by('created_at')
        return MaterialCommentSerializer(replies, many=True).data


class MaterialRatingSerializer(serializers.ModelSerializer):
    """Serializer for MaterialRating model."""
    
    user_email = serializers.EmailField(source='user.email', read_only=True)
    
    class Meta:
        model = MaterialRating
        fields = ['id', 'material', 'user', 'user_email', 'value', 'created_at', 'updated_at']
        read_only_fields = ['id', 'user', 'created_at', 'updated_at']


class MaterialSerializer(serializers.ModelSerializer):
    """Serializer for Material model."""
    
    status_display = serializers.CharField(source='get_status_display', read_only=True)
    author_email = serializers.EmailField(source='author.email', read_only=True)
    author_name = serializers.SerializerMethodField()
    branch_name = serializers.CharField(source='branch.name', read_only=True)
    branch_path = serializers.CharField(source='branch.get_full_path', read_only=True)
    files = MaterialFileSerializer(many=True, read_only=True)
    tags = MaterialTagSerializer(many=True, read_only=True)
    comments_count = serializers.SerializerMethodField()
    user_rating = serializers.SerializerMethodField()
    
    class Meta:
        model = Material
        fields = [
            'id', 'branch', 'branch_name', 'branch_path', 'author', 'author_email', 'author_name',
            'description', 'status', 'status_display', 'moderation_comment',
            'moderator', 'moderated_at', 'average_rating', 'ratings_count',
            'downloads_count', 'views_count', 'files', 'tags',
            'comments_count', 'user_rating', 'created_at', 'updated_at'
        ]
        read_only_fields = [
            'id', 'author', 'status', 'moderator', 'moderated_at',
            'average_rating', 'ratings_count', 'downloads_count',
            'views_count', 'created_at', 'updated_at'
        ]
    
    def get_author_name(self, obj):
        if obj.author.first_name or obj.author.last_name:
            return f"{obj.author.first_name} {obj.author.last_name}".strip()
        return obj.author.email.split('@')[0]
    
    def get_comments_count(self, obj):
        return obj.comments.filter(is_deleted=False).count()
    
    def get_user_rating(self, obj):
        request = self.context.get('request')
        if request and request.user.is_authenticated:
            try:
                rating = obj.ratings.get(user=request.user)
                return rating.value
            except MaterialRating.DoesNotExist:
                return None
        return None


class MaterialCreateSerializer(serializers.ModelSerializer):
    """Serializer for creating material."""
    
    files = serializers.ListField(
        child=serializers.FileField(),
        write_only=True,
        required=True
    )
    file_comments = serializers.DictField(
        child=serializers.CharField(allow_blank=True),
        required=False,
        allow_empty=True
    )
    tags = serializers.ListField(
        child=serializers.CharField(),
        required=False,
        allow_empty=True
    )
    
    class Meta:
        model = Material
        fields = ['branch', 'description', 'files', 'file_comments', 'tags']
    
    def validate_files(self, value):
        if not value:
            raise serializers.ValidationError("Необходимо загрузить хотя бы один файл")
        if len(value) > 20:
            raise serializers.ValidationError("Максимальное количество файлов: 20")
        return value
    
    def create(self, validated_data):
        files = validated_data.pop('files')
        file_comments = validated_data.pop('file_comments', {})
        tag_names = validated_data.pop('tags', [])
        
        # Author is set in perform_create, so we don't need to set it here
        material = Material.objects.create(
            **validated_data
        )
        
        # Create files
        for index, file in enumerate(files):
            MaterialFile.objects.create(
                material=material,
                file=file,
                original_name=file.name,
                comment=file_comments.get(str(index), ''),
                upload_order=index
            )
        
        # Create/get tags
        for tag_name in tag_names:
            tag, _ = MaterialTag.objects.get_or_create(name=tag_name.lower())
            material.tags.add(tag)
        
        # Refresh from DB to ensure tags are properly loaded
        material.refresh_from_db()
        return material


class MaterialRatingCreateSerializer(serializers.ModelSerializer):
    """Serializer for creating/updating material rating."""
    
    class Meta:
        model = MaterialRating
        fields = ['material', 'value']
    
    def validate(self, attrs):
        material = attrs.get('material')
        if material.status != Material.Status.APPROVED:
            raise serializers.ValidationError({
                'material': 'Нельзя оценивать материалы, которые не одобрены'
            })
        return attrs
    
    def create(self, validated_data):
        validated_data['user'] = self.context['request'].user
        rating, created = MaterialRating.objects.get_or_create(
            material=validated_data['material'],
            user=validated_data['user'],
            defaults={'value': validated_data['value']}
        )
        if not created:
            rating.value = validated_data['value']
            rating.save()
        return rating

