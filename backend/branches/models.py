"""
Branch models for tree structure.
"""
from django.db import models
from django.contrib.auth import get_user_model
from django.core.validators import MinLengthValidator

User = get_user_model()


class Branch(models.Model):
    """Branch in the tree structure (Institute -> Department -> Direction -> Course -> Teacher)."""
    
    class BranchType(models.TextChoices):
        INSTITUTE = 'institute', 'Институт'
        DEPARTMENT = 'department', 'Кафедра'
        DIRECTION = 'direction', 'Направление'
        COURSE = 'course', 'Курс'
        TEACHER = 'teacher', 'Преподаватель'
    
    class Status(models.TextChoices):
        PENDING = 'pending', 'На модерации'
        APPROVED = 'approved', 'Одобрено'
        REJECTED = 'rejected', 'Отклонено'
    
    type = models.CharField(
        max_length=20,
        choices=BranchType.choices,
        verbose_name='Тип ветки'
    )
    name = models.CharField(
        max_length=200,
        validators=[MinLengthValidator(2)],
        verbose_name='Название'
    )
    parent = models.ForeignKey(
        'self',
        on_delete=models.CASCADE,
        related_name='children',
        null=True,
        blank=True,
        verbose_name='Родительская ветка'
    )
    creator = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        related_name='created_branches',
        null=True,
        verbose_name='Создатель'
    )
    status = models.CharField(
        max_length=20,
        choices=Status.choices,
        default=Status.PENDING,
        db_index=True,
        verbose_name='Статус'
    )
    moderation_comment = models.TextField(
        blank=True,
        null=True,
        verbose_name='Комментарий модератора'
    )
    moderator = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        related_name='moderated_branches',
        null=True,
        blank=True,
        verbose_name='Модератор'
    )
    moderated_at = models.DateTimeField(
        null=True,
        blank=True,
        verbose_name='Дата модерации'
    )
    created_at = models.DateTimeField(
        auto_now_add=True,
        verbose_name='Дата создания'
    )
    updated_at = models.DateTimeField(
        auto_now=True,
        verbose_name='Дата обновления'
    )
    
    class Meta:
        verbose_name = 'Ветка'
        verbose_name_plural = 'Ветки'
        ordering = ['type', 'name']
        indexes = [
            models.Index(fields=['parent', 'status']),
            models.Index(fields=['type', 'status']),
            models.Index(fields=['creator', 'status']),
        ]
    
    def __str__(self):
        return f"{self.get_type_display()}: {self.name}"
    
    def get_full_path(self):
        """Get full path from root to this branch."""
        path = [self.name]
        current = self.parent
        while current:
            path.insert(0, current.name)
            current = current.parent
        return ' → '.join(path)
    
    def get_ancestors(self):
        """Get all ancestors of this branch."""
        ancestors = []
        current = self.parent
        while current:
            ancestors.insert(0, current)
            current = current.parent
        return ancestors
    
    def get_descendants(self):
        """Get all descendants of this branch."""
        descendants = []
        for child in self.children.all():
            descendants.append(child)
            descendants.extend(child.get_descendants())
        return descendants
    
    def is_leaf(self):
        """Check if branch is a leaf (teacher level)."""
        return self.type == self.BranchType.TEACHER or self.type == self.BranchType.COURSE
    
    def can_have_children(self):
        """Check if branch can have children based on type."""
        # Only teacher level cannot have children
        return self.type != self.BranchType.TEACHER
    
    def get_next_type(self):
        """Get next type in hierarchy."""
        type_hierarchy = {
            self.BranchType.INSTITUTE: self.BranchType.DEPARTMENT,
            self.BranchType.DEPARTMENT: self.BranchType.DIRECTION,
            self.BranchType.DIRECTION: self.BranchType.COURSE,
            self.BranchType.COURSE: self.BranchType.TEACHER,
        }
        return type_hierarchy.get(self.type)
    
    def approve(self, moderator, comment=''):
        """Approve branch."""
        self.status = self.Status.APPROVED
        self.moderator = moderator
        self.moderation_comment = comment
        from django.utils import timezone
        self.moderated_at = timezone.now()
        self.save()
    
    def reject(self, moderator, comment):
        """Reject branch."""
        if not comment:
            raise ValueError("Comment is required for rejection")
        self.status = self.Status.REJECTED
        self.moderator = moderator
        self.moderation_comment = comment
        from django.utils import timezone
        self.moderated_at = timezone.now()
        self.save()


class BranchRequest(models.Model):
    """Request to create a new branch."""
    
    parent = models.ForeignKey(
        Branch,
        on_delete=models.CASCADE,
        related_name='branch_requests',
        verbose_name='Родительская ветка'
    )
    name = models.CharField(
        max_length=200,
        validators=[MinLengthValidator(2)],
        verbose_name='Название новой ветки'
    )
    requester = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='branch_requests',
        verbose_name='Запросивший'
    )
    status = models.CharField(
        max_length=20,
        choices=Branch.Status.choices,
        default=Branch.Status.PENDING,
        db_index=True,
        verbose_name='Статус'
    )
    moderation_comment = models.TextField(
        blank=True,
        null=True,
        verbose_name='Комментарий модератора'
    )
    moderator = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        related_name='moderated_branch_requests',
        null=True,
        blank=True,
        verbose_name='Модератор'
    )
    moderated_at = models.DateTimeField(
        null=True,
        blank=True,
        verbose_name='Дата модерации'
    )
    created_branch = models.OneToOneField(
        Branch,
        on_delete=models.SET_NULL,
        related_name='branch_request',
        null=True,
        blank=True,
        verbose_name='Созданная ветка'
    )
    created_at = models.DateTimeField(
        auto_now_add=True,
        verbose_name='Дата создания'
    )
    
    class Meta:
        verbose_name = 'Запрос на ветку'
        verbose_name_plural = 'Запросы на ветки'
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['status', 'created_at']),
            models.Index(fields=['requester', 'status']),
        ]
    
    def __str__(self):
        return f"Запрос: {self.name} (от {self.requester.email})"
    
    def approve(self, moderator, comment=''):
        """Approve request and create branch."""
        from django.utils import timezone
        
        # Validate parent can have children
        if not self.parent.can_have_children():
            raise ValueError("Родительская ветка не может иметь дочерние элементы")
        
        # Get next type in hierarchy
        next_type = self.parent.get_next_type()
        if not next_type:
            raise ValueError("Невозможно определить тип новой ветки для данного родителя")
        
        # Check if branch with same name already exists
        if Branch.objects.filter(
            parent=self.parent,
            name=self.name,
            status=Branch.Status.APPROVED
        ).exists():
            raise ValueError("Ветка с таким названием уже существует")
        
        # Create branch
        branch = Branch.objects.create(
            type=next_type,
            name=self.name,
            parent=self.parent,
            creator=self.requester,
            status=Branch.Status.APPROVED,
            moderation_comment=comment,
            moderator=moderator,
            moderated_at=timezone.now()
        )
        
        # Update request
        self.status = Branch.Status.APPROVED
        self.moderator = moderator
        self.moderation_comment = comment
        self.moderated_at = timezone.now()
        self.created_branch = branch
        self.save()
        
        return branch
    
    def reject(self, moderator, comment):
        """Reject request."""
        if not comment:
            raise ValueError("Comment is required for rejection")
        from django.utils import timezone
        
        self.status = Branch.Status.REJECTED
        self.moderator = moderator
        self.moderation_comment = comment
        self.moderated_at = timezone.now()
        self.save()

