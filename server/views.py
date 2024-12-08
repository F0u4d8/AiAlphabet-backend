from rest_framework.decorators import api_view, authentication_classes, permission_classes
from rest_framework.authentication import SessionAuthentication, TokenAuthentication
from rest_framework.permissions import IsAuthenticated , IsAdminUser
from rest_framework.response import Response
from rest_framework import status
from django.shortcuts import get_object_or_404
from django.contrib.auth.models import User
from rest_framework.authtoken.models import Token
from .serializers import UserSerializer ,CategorySerializer ,ContentSerializer
from .models import QRCode , UserProfile ,Category ,Content
from django.db.models.signals import post_save
from django.dispatch import receiver
import jwt
import os
from django.conf import settings
from django.http import JsonResponse
from datetime import datetime, timedelta,timezone



@receiver(post_save, sender=User)
def create_user_profile(sender, instance, created, **kwargs):
    if created:
        UserProfile.objects.create(user=instance)

@receiver(post_save, sender=User)
def save_user_profile(sender, instance, **kwargs):
    instance.profile.save()

@api_view(['GET'])
def predefined_avatars(request):
    avatars_path = os.path.join(settings.MEDIA_ROOT, 'avatars')
    avatar_files = [
        f"{settings.MEDIA_URL}avatars/{filename}" 
        for filename in os.listdir(avatars_path) 
        if filename.lower().endswith(('.png', '.jpg', '.jpeg'))
    ]
    return JsonResponse({'avatars': avatar_files}, safe=False)



@api_view(['POST'])
def signup(request):
    qr_code_value = request.data.get('qr_code')
    username = request.data.get('username')
    email = request.data.get('email')
    avatar_url = request.data.get('avatar_url')
    
    try:
        qr_code = QRCode.objects.get(code=qr_code_value)
    except QRCode.DoesNotExist:
        return Response({'error': 'Invalid QR code'}, status=status.HTTP_400_BAD_REQUEST) 
    if qr_code.is_used:
        return Response({'error': 'QR code already used'}, status=status.HTTP_400_BAD_REQUEST)


    if User.objects.filter(username=username).exists():
        return Response({'error': 'Username already taken'}, status=status.HTTP_400_BAD_REQUEST)

    if User.objects.filter(email=email).exists():
        return Response({'error': 'Email already registered'}, status=status.HTTP_400_BAD_REQUEST)


    serializer = UserSerializer(data=request.data)
    if serializer.is_valid():
        serializer.save()
        user = User.objects.get(username=request.data['username'])
        user.profile.avatar_url = avatar_url
        user.profile.save()
        user.save()
        token = Token.objects.create(user=user)
        qr_code.is_used = True
        qr_code.save()
        return Response({'token': token.key, 'user': serializer.data} , status=status.HTTP_201_CREATED)
    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)



@api_view(['POST'])
def login(request):
    user = get_object_or_404(User, username=request.data['username'])
    if not user.check_password(request.data['password']):
        return Response("missing user", status=status.HTTP_404_NOT_FOUND)
    token, created = Token.objects.get_or_create(user=user)
    serializer = UserSerializer(user)
    return Response({'token': token.key, 'user': serializer.data})



@api_view(['GET'])
@authentication_classes([SessionAuthentication, TokenAuthentication])
@permission_classes([IsAuthenticated])
def categoryListAll(request):
    categories = Category.objects.all()
    serializer = CategorySerializer(categories, many=True)
    return Response(serializer.data, status=status.HTTP_200_OK)


@api_view(['GET'])
@authentication_classes([SessionAuthentication, TokenAuthentication])
@permission_classes([IsAuthenticated])
def contentListByCat(request, category_id):
    try:
        category = Category.objects.get(id=category_id)
    except Category.DoesNotExist:
        return Response({'error': 'Category not found'}, status=status.HTTP_404_NOT_FOUND)

    contents = category.contents.all()
    serializer = ContentSerializer(contents, many=True)
    return Response(serializer.data, status=status.HTTP_200_OK)



@api_view(['GET'])
@authentication_classes([SessionAuthentication, TokenAuthentication])
@permission_classes([IsAuthenticated])
def contentListById(request, content_id):
    try:
        content = Content.objects.get(id=content_id)
    except Content.DoesNotExist:
        return Response({'error': 'content not found'}, status=status.HTTP_404_NOT_FOUND)
    serializer = ContentSerializer(content)
    return Response(serializer.data, status=status.HTTP_200_OK)



















#ADMIN ROUTES

JWT_SECRET = settings.SECRET_KEY
JWT_ALGORITHM = 'HS256'

def generate_jwt_tokens(user):
    """
    Generates access and refresh tokens for a user.
    """
    # Access token expires in 15 minutes
    access_token_exp = datetime.now(timezone.utc) + timedelta(minutes=1)
    access_token_payload = {
        'user_id': user.id,
        'email': user.email,
     'username': user.username,
        'is_staff': user.is_staff,
        'avatar': user.profile.avatar_url,
        'exp': access_token_exp,
        'iat': datetime.now(timezone.utc),
    }
    access_token = jwt.encode(access_token_payload, JWT_SECRET, algorithm=JWT_ALGORITHM)

    # Refresh token expires in 7 days
    refresh_token_exp = datetime.now(timezone.utc) + timedelta(days=1)
    refresh_token_payload = {
        'user_id': user.id,
        'email': user.email,
        'username': user.username,
        'token_type': 'refresh',
        'avatar': user.profile.avatar_url,
        'exp': refresh_token_exp,
        'iat': datetime.now(timezone.utc),
    }
    refresh_token = jwt.encode(refresh_token_payload, JWT_SECRET, algorithm=JWT_ALGORITHM)

    return access_token, refresh_token



@api_view(['POST'])
def admin_login(request):
    """
    Admin login endpoint using JWT for authentication.
    """
    # Get the user by username
    user = get_object_or_404(User, email=request.data['email'])
    
    # Check the password
    if not user.check_password(request.data['password']):
        return Response({"error": "Invalid credentials"}, status=status.HTTP_401_UNAUTHORIZED)
    
    # Check if the user is an admin (is_staff or is_superuser)
    if not user.is_staff:
        return Response({"error": "User is not an admin"}, status=status.HTTP_403_FORBIDDEN)
    
    # Get or create a token
    access_token, refresh_token = generate_jwt_tokens(user)
   
    return Response({
        'access_token': access_token,
        'refresh_token': refresh_token,
    })


@api_view(['POST'])
def refresh_token(request):
    """
    Refresh the access token using a valid refresh token.
    """
    # Extract the refresh token from the Authorization header
    auth_header = request.headers.get('Authorization')
    if not auth_header or not auth_header.startswith('Bearer '):
        return Response({"error": "Authorization header is required"}, status=status.HTTP_400_BAD_REQUEST)

    refresh_token = auth_header.split(' ')[1]  # Extract the token part

    try:
        # Decode the refresh token
        payload = jwt.decode(refresh_token, JWT_SECRET, algorithms=[JWT_ALGORITHM])
        if payload.get('token_type') != 'refresh':
            return Response({"error": "Invalid token type"}, status=status.HTTP_400_BAD_REQUEST)

        # Get the user associated with the refresh token
        user = get_object_or_404(User, id=payload.get('user_id'))

        # Generate a new access token
        access_token, _ = generate_jwt_tokens(user)

        return Response({'access_token': access_token})

    except jwt.ExpiredSignatureError:
        return Response({"error": "Refresh token has expired"}, status=status.HTTP_401_UNAUTHORIZED)
    except jwt.InvalidTokenError:
        return Response({"error": "Invalid refresh token"}, status=status.HTTP_401_UNAUTHORIZED)


@api_view(['POST'])
@authentication_classes([SessionAuthentication, TokenAuthentication])
@permission_classes([IsAuthenticated ,IsAdminUser])
def generate_qr_code(request):
    """
    Generate a one-time QR code (admin only).
    """
    qr_code = QRCode.objects.create()
    return Response({'code': str(qr_code.code)})




@api_view(['POST'])
@authentication_classes([SessionAuthentication, TokenAuthentication])
@permission_classes([IsAuthenticated ,IsAdminUser])
def adminCreateCategory(request):
    """
admin create category    """
    serializer = CategorySerializer(data=request.data)
    if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_201_CREATED)
    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)



@api_view(['PUT', 'DELETE'])
@authentication_classes([SessionAuthentication, TokenAuthentication])
@permission_classes([IsAuthenticated ,IsAdminUser])
def category_update_delete(request, category_id):
    try:
        category = Category.objects.get(pk=category_id)
    except Category.DoesNotExist:
        return Response({'error': 'Category not found'}, status=status.HTTP_404_NOT_FOUND)

    if request.method == 'PUT':
        serializer = CategorySerializer(category, data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data , status=status.HTTP_200_OK)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    if request.method == 'DELETE':
        category.delete()
        return Response({'success': 'Category deleted successfully'} ,status=status.HTTP_204_NO_CONTENT)
    
    
 
@api_view(['POST'])
@authentication_classes([SessionAuthentication, TokenAuthentication])
@permission_classes([IsAuthenticated ,IsAdminUser])
def adminCreateContent(request):
    """
admin create Content    """
    serializer = ContentSerializer(data=request.data)
    if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_201_CREATED)
    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


@api_view(['PUT', 'DELETE'])
@authentication_classes([SessionAuthentication, TokenAuthentication])
@permission_classes([IsAuthenticated ,IsAdminUser])
def content_update_delete(request, content_id):
    try:
         content = Content.objects.get(id=content_id)
    except Content.DoesNotExist:
        return Response({'error': 'Content not found'}, status=status.HTTP_404_NOT_FOUND)

    if request.method == 'PUT':
        serializer = ContentSerializer(content, data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data , status=status.HTTP_200_OK)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    if request.method == 'DELETE':
        content.delete()
        return Response({'success': 'content deleted successfully'} ,status=status.HTTP_204_NO_CONTENT)