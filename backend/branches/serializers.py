"""
Serializers for branches app.
"""
from rest_framework import serializers
from django.contrib.auth import get_user_model
from .models import Branch, BranchRequest

User = get_user_model()


class BranchSerializer(serializers.ModelSerializer):
    """Serializer for Branch model."""
    
    type_display = serializers.CharField(source='get_type_display', read_only=True)
    status_display = serializers.CharField(source='get_status_display', read_only=True)
    full_path = serializers.CharField(source='get_full_path', read_only=True)
    creator_email = serializers.EmailField(source='creator.email', read_only=True)
    moderator_email = serializers.EmailField(source='moderator.email', read_only=True)
    children_count = serializers.SerializerMethodField()
    materials_count = serializers.SerializerMethodField()
    
    class Meta:
        model = Branch
        fields = [
            'id', 'type', 'type_display', 'name', 'parent', 'full_path',
            'creator', 'creator_email', 'status', 'status_display',
            'moderator', 'moderator_email', 'moderation_comment',
            'moderated_at', 'created_at', 'updated_at',
            'children_count', 'materials_count'
        ]
        read_only_fields = [
            'id', 'created_at', 'updated_at', 'moderated_at',
            'moderator'
        ]
    
    def get_children_count(self, obj):
        return obj.children.filter(status=Branch.Status.APPROVED).count()
    
    def get_materials_count(self, obj):
        if hasattr(obj, 'materials'):
            return obj.materials.filter(status='approved').count()
        return 0
    
    def validate(self, attrs):
        """Validate branch data."""
        parent = attrs.get('parent')
        branch_type = attrs.get('type')
        
        if parent:
            # Get parent object from DB (parent can be ID or object)
            parent_id = parent.id if hasattr(parent, 'id') else parent
            try:
                parent_obj = Branch.objects.get(id=parent_id)
            except Branch.DoesNotExist:
                raise serializers.ValidationError({
                    'parent': 'Родительская ветка не найдена'
                })
            
            if not parent_obj.can_have_children():
                raise serializers.ValidationError({
                    'parent': 'Эта ветка не может иметь дочерние элементы'
                })
            
            # Check type hierarchy
            expected_type = parent_obj.get_next_type()
            if branch_type and expected_type and branch_type != expected_type:
                raise serializers.ValidationError({
                    'type': f'Для родителя "{parent_obj.name}" ожидается тип "{expected_type}"'
                })
        
        return attrs
    
    def create(self, validated_data):
        """Create branch with creator set."""
        request = self.context.get('request')
        if request and request.user:
            validated_data['creator'] = request.user
            # If admin creates, set status to approved
            if request.user.is_admin and 'status' not in validated_data:
                validated_data['status'] = Branch.Status.APPROVED
        return super().create(validated_data)


class BranchTreeSerializer(serializers.ModelSerializer):
    """Serializer for tree structure."""
    
    children = serializers.SerializerMethodField()
    materials_count = serializers.SerializerMethodField()
    
    class Meta:
        model = Branch
        fields = [
            'id', 'type', 'name', 'status', 'children', 'materials_count'
        ]
    
    def get_children(self, obj):
        approved_children = obj.children.filter(status=Branch.Status.APPROVED)
        return BranchTreeSerializer(approved_children, many=True).data
    
    def get_materials_count(self, obj):
        if hasattr(obj, 'materials'):
            return obj.materials.filter(status='approved').count()
        return 0


class BranchRequestSerializer(serializers.ModelSerializer):
    """Serializer for BranchRequest model."""
    
    parent_name = serializers.CharField(source='parent.name', read_only=True)
    parent_path = serializers.CharField(source='parent.get_full_path', read_only=True)
    requester_email = serializers.EmailField(source='requester.email', read_only=True)
    moderator_email = serializers.EmailField(source='moderator.email', read_only=True)
    status_display = serializers.CharField(source='get_status_display', read_only=True)
    
    class Meta:
        model = BranchRequest
        fields = [
            'id', 'parent', 'parent_name', 'parent_path', 'name',
            'requester', 'requester_email', 'status', 'status_display',
            'moderator', 'moderator_email', 'moderation_comment',
            'moderated_at', 'created_branch', 'created_at'
        ]
        read_only_fields = [
            'id', 'created_at', 'moderated_at', 'moderator', 'status',
            'created_branch'
        ]
    
    def validate(self, attrs):
        parent = attrs.get('parent')
        if parent:
            if not parent.can_have_children():
                raise serializers.ValidationError({
                    'parent': 'Эта ветка не может иметь дочерние элементы'
                })
            if parent.status != Branch.Status.APPROVED:
                raise serializers.ValidationError({
                    'parent': 'Родительская ветка должна быть одобрена'
                })
        return attrs


class BranchRequestCreateSerializer(serializers.ModelSerializer):
    """Serializer for creating branch request."""
    
    class Meta:
        model = BranchRequest
        fields = ['parent', 'name']
    
    def validate(self, attrs):
        parent = attrs.get('parent')
        name = attrs.get('name')
        
        if parent:
            # Get parent object from DB (parent can be ID or object)
            parent_id = parent.id if hasattr(parent, 'id') else parent
            try:
                parent_obj = Branch.objects.get(id=parent_id)
            except Branch.DoesNotExist:
                raise serializers.ValidationError({
                    'parent': 'Родительская ветка не найдена'
                })
            
            if not parent_obj.can_have_children():
                raise serializers.ValidationError({
                    'parent': 'Эта ветка не может иметь дочерние элементы'
                })
            if parent_obj.status != Branch.Status.APPROVED:
                raise serializers.ValidationError({
                    'parent': 'Родительская ветка должна быть одобрена'
                })
            
            # Check if branch with same name already exists
            if Branch.objects.filter(parent=parent_obj, name=name, status=Branch.Status.APPROVED).exists():
                raise serializers.ValidationError({
                    'name': 'Ветка с таким названием уже существует'
                })
            
            # Replace parent with actual object
            attrs['parent'] = parent_obj
        
        return attrs
    
    def create(self, validated_data):
        validated_data['requester'] = self.context['request'].user
        return super().create(validated_data)

