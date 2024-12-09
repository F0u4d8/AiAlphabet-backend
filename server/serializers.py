from rest_framework import serializers
from django.contrib.auth.models import User
from .models import UserProfile ,Category ,Content,Todo


class UserProfileSerializer(serializers.ModelSerializer):
    class Meta:
        model = UserProfile
        fields = ['avatar_url']


class UserSerializer(serializers.ModelSerializer):
    profile = UserProfileSerializer(read_only=True)
    predefined_avatar_id = serializers.IntegerField(write_only=True)
    password = serializers.CharField(write_only=True)

    class Meta:
        model = User
        fields = ['id', 'username', 'email', 'password', 'profile', 'predefined_avatar_id']

    def create(self, validated_data):

        # Create the user
        user = User.objects.create(
            username=validated_data['username'],
            email=validated_data['email']
        )
        user.set_password(validated_data['password'])
        user.save()

        return user


class LimitedContentSerializer(serializers.ModelSerializer):
    class Meta:
        model = Content
        fields = ['id', 'image']


class ContentSerializer(serializers.ModelSerializer):
    class Meta:
        model = Content
        fields = ['id', 'title', 'url', 'pitch', 'image', 'category']


class CategorySerializer(serializers.ModelSerializer):
    contents = serializers.SerializerMethodField()

    class Meta:
        model = Category
        fields = ['id', 'name', 'description', 'contents']

    def get_contents(self, obj):
        contents = obj.contents.all()[:8]  # Limit to 8 images
        return LimitedContentSerializer(contents, many=True).data
    
    


class TodoSerializer(serializers.ModelSerializer):
    priority_display = serializers.SerializerMethodField()

    class Meta:
        model = Todo
        fields = ['id', 'user', 'title', 'description', 'priority', 'priority_display', 'is_completed', 'created_at', 'updated_at']
        read_only_fields = ['id', 'user', 'created_at', 'updated_at']

    def get_priority_display(self, obj):
        return dict(Todo.PRIORITY_CHOICES).get(obj.priority)    