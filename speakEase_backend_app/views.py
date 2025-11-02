from django.shortcuts import render
from rest_framework.views import APIView
from rest_framework.response import Response
from .models import TrainingSession,UserProfile, ProgressAnalytics
from .serializers import TrainingSessionSerializer, UserSerializer,UserProfileSerializer
from rest_framework import generics,status
from rest_framework.permissions import IsAuthenticated, AllowAny
from django.contrib.auth import get_user_model
from django.shortcuts import get_object_or_404
from .ai_modules import audio_analyzer
import os
from rest_framework.parsers import MultiPartParser, FormParser

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


# for analysis the file upload
class VoiceTrainingView(APIView):
    permission_classes = [IsAuthenticated]
    permission_classes = [IsAuthenticated]
    parser_classes = (MultiPartParser, FormParser)

    def post(self, request):
        
            audio_file = request.FILES.get('audio_file')
            training_type = request.data.get('training_type', 'voice')
            duration = int(request.data.get('duration', 0))
            word = request.data.get('word', '')
            if not audio_file:
                return Response({'Audio file is required'}, status=status.HTTP_400_BAD_REQUEST)
            if duration <= 0:
                return Response({'Duration must be greater than 0'}, status=status.HTTP_400_BAD_REQUEST)
            
            # save the file 
            temp_audio_path = f'/tmp/{audio_file.name}'
            with open(temp_audio_path, 'wb+') as destination:
                for chunk in audio_file.chunks():
                    destination.write(chunk)
            
            # audio analysis transcript
            analysis_result = audio_analyzer.calculate_overall_score(
                transcribed_text=audio_analyzer.transcribe_audio(temp_audio_path)['text'],
                audio_duration_seconds=duration,
                audio_path=temp_audio_path
            )
            
            if not analysis_result:
                return Response({'Analysis failed'}, status=status.HTTP_400_BAD_REQUEST)
            
            # it create new TrainingSession save the data to db
            training_session = TrainingSession.objects.create(
                # link session to the user 
                user=request.user,
                training_type=training_type,
                duration=duration,
                audio_file=audio_file,
                score=analysis_result['score'],
                mispronunciations=analysis_result.get('mis_pct', 0),
                repeated_words=analysis_result.get('repeated', 0),
                feedback_text=analysis_result['feedback'],
                transcribed_text=audio_analyzer.transcribe_audio(temp_audio_path).get('text', '')
            )
            
            profile = UserProfile.objects.get(user=request.user)
            # add to the total_training_time the duration
            profile.total_training_time += duration
            # and save it to the db
            profile.save()
            
            serializer = TrainingSessionSerializer(training_session)
            response_data = {
                **serializer.data,
                'analysis': {
                    'wpm': analysis_result.get('wpm'),
                    'rating': analysis_result.get('rating'),
                }
            }
            
            return Response(response_data, status=status.HTTP_201_CREATED)
        
            
class TrainingSessionView(APIView):

    permission_classes = [IsAuthenticated]

    # to get all the training sessions for the user 
    def get(self, request):
        sessions = TrainingSession.objects.filter(user=request.user)
        serializer = TrainingSessionSerializer(sessions, many=True)
        return Response(serializer.data)
    
    # # Create new training session for the user
    # def post(self, request):
        
    #     data = request.data.copy()
    #     data['user'] = request.user.id
        
    #     serializer = TrainingSessionSerializer(data=data)
    #     if serializer.is_valid():
    #         serializer.save(user=request.user)
    #         return Response(serializer.data, status=status.HTTP_201_CREATED)
        
    #     return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

# # def get_object(self, user, session_id):
#         try:
#             return TrainingSession.objects.get(id=session_id, user=user)
#         except TrainingSession.DoesNotExist:
#             return None
class TrainingSessionDetailView(APIView):
    permission_classes = [IsAuthenticated]
    
    def get(self, request, session_id):
        session = self.get_object(request.user, session_id)
        if not session:
            return Response({'error': 'Training session not found'}, status=status.HTTP_404_NOT_FOUND)
        serializer = TrainingSessionSerializer(session)
        return Response(serializer.data)

    # def put(self, request, session_id):
    #     session = self.get_object(request.user, session_id)
    #     if not session:
    #         return Response({'error': 'Training session not found'}, status=status.HTTP_404_NOT_FOUND)
    #     serializer = TrainingSessionSerializer(session, data=request.data, partial=True)
    #     if serializer.is_valid():
    #         serializer.save()
    #         return Response(serializer.data)
    #     return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def delete(self, request, session_id):
        session = self.get_object(request.user, session_id)
        if not session:
            return Response({'error': 'Training session not found'}, status=status.HTTP_404_NOT_FOUND)
        session.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)

