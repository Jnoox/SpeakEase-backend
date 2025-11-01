from django.shortcuts import render
from rest_framework.views import APIView
from rest_framework.response import Response
from .models import TrainingSession,UserProfile, ProgressAnalytics
from .serializers import TrainingSessionSerializer, UserSerializer,UserProfileSerializer
from rest_framework import generics,status
from rest_framework.permissions import IsAuthenticated, AllowAny
from django.contrib.auth import get_user_model
from django.shortcuts import get_object_or_404

# Create your views here.

User = get_user_model()

# this for User SignUp
class UserSignUpView(APIView):
    
    permission_classes = [AllowAny]
    
    # to create new user 
    def post(self, request):
        username = request.data.get('username')
        email = request.data.get('email')
        password = request.data.get('password')
        first_name = request.data.get('first_name', '')
        last_name = request.data.get('last_name', '')
        age = request.data.get('age')

        # Validation
        
        if age:
            age = int(age)
            if age < 1 or age > 150:
                return Response({'error': 'Age must be between 1 and 150'}, status=400)

        if not username or not email or not password:
            return Response(
                {'error': 'Username, email, and password are required'},
                status=status.HTTP_400_BAD_REQUEST
            )
            
        if User.objects.filter(username=username).exists():
            return Response(
                {'error': 'Username already exists'},
                status=status.HTTP_400_BAD_REQUEST
            )

        if User.objects.filter(email=email).exists():
            return Response(
                {'error': 'Email already exists'},
                status=status.HTTP_400_BAD_REQUEST
            )

        # Create user
        try:
            user = User.objects.create_user(
                username=username,
                email=email,
                password=password,
                first_name=first_name,
                last_name=last_name
            )
            
            # Create related profiles
            UserProfile.objects.create(user=user, age=age)
            # to connect the ProgressAnalytics with this user
            ProgressAnalytics.objects.create(user=user)

            serializer = UserSerializer(user)
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        
        except Exception as e:
            return Response(
                {'error': str(e)},
                status=status.HTTP_400_BAD_REQUEST
            )

# get user info
class CurrentUserView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        serializer = UserSerializer(request.user)
        return Response(serializer.data)

class UserProfileView(APIView):
    permission_classes = [IsAuthenticated]
    
    # Get user's profile info
    def get(self, request):
        try:
            profile = UserProfile.objects.get(user=request.user)
            serializer = UserProfileSerializer(profile)
            return Response(serializer.data)
        except UserProfile.DoesNotExist:
            return Response(
                {'error': 'Profile not found'},
                status=status.HTTP_404_NOT_FOUND
            )
            
    # Update user's profile info 
    def put(self, request):
       
        try:
            profile = UserProfile.objects.get(user=request.user)
            serializer = UserProfileSerializer(profile, data=request.data, partial=True)
            
            if serializer.is_valid():
                serializer.save()
                return Response(serializer.data)
            
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        
        except UserProfile.DoesNotExist:
            return Response(
                {'error': 'Profile not found'},
                status=status.HTTP_404_NOT_FOUND
            )
    
    # Delete user account
    def delete(self, request):
        try:
            user = request.user
            username = user.username
            user.delete()
            
            return Response(
                {'message': f'Account {username} deleted successfully'},
                status=status.HTTP_204_NO_CONTENT
            )
        except Exception as e:
            return Response(
                {'error': str(e)},
                status=status.HTTP_400_BAD_REQUEST
            )
            
            
# get all the user (just the admin)
class AllUsersView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        # Get all users just by admin
        if not request.user.is_staff:
            return Response(
                {'error': 'Admin access required'},
                status=status.HTTP_403_FORBIDDEN
            )
        
        users = User.objects.all()
        serializer = UserSerializer(users, many=True)
        return Response(serializer.data)



class TrainingSessionListCreateView(APIView):

    permission_classes = [IsAuthenticated]

    # to get all the training sessions for the user 
    def get(self, request):
        sessions = TrainingSession.objects.filter(user=request.user)
        serializer = TrainingSessionSerializer(sessions, many=True)
        return Response(serializer.data)
    
    # Create new training session for the user
    def post(self, request):
        
        data = request.data.copy()
        data['user'] = request.user.id
        
        serializer = TrainingSessionSerializer(data=data)
        if serializer.is_valid():
            serializer.save(user=request.user)
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
