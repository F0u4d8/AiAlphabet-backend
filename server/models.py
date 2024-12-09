import uuid
from django.db import models
from django.contrib.auth.models import User

class QRCode(models.Model):
    """
    Model to represent one-time QR codes.
    """
    code = models.UUIDField(default=uuid.uuid4, editable=False, unique=True)
    is_used = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return str(self.code)
    
    
    
class UserProfile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='profile')
    avatar_url = models.URLField(max_length=500, default='/media/avatars/avatar1.jpg')  # Store the avatar URL here

    def __str__(self):
        return f"{self.user.username}'s Profile"
    


class Category(models.Model):
    name = models.CharField(max_length=255, unique=True)
    description = models.TextField(blank=True, null=True)

    def __str__(self):
        return self.name


class Content(models.Model):
    category = models.ForeignKey(Category, on_delete=models.CASCADE, related_name='contents')
    title = models.CharField(max_length=255)
    url = models.URLField()
    pitch = models.TextField()
    image = models.URLField()

    def __str__(self):
        return f"{self.title} ({self.category.name})"
    



class Todo(models.Model):
    PRIORITY_CHOICES = [
        (0, 'عاجل'),      
        (1, 'مهم'),      
        (2, 'عادي'),     
        (3, 'غير مهم'),    
    ]

    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='todos')
    title = models.CharField(max_length=255)
    description = models.TextField(blank=True, null=True)
    priority = models.IntegerField(choices=PRIORITY_CHOICES, default=2)  
    is_completed = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.title} (Priority: {dict(self.PRIORITY_CHOICES).get(self.priority)})"
