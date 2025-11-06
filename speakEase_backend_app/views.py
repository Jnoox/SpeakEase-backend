from django.shortcuts import render
from rest_framework.views import APIView
from rest_framework.response import Response
from .models import TrainingSession,UserProfile, ProgressAnalytics, VocabularyWord, Tip
from .serializers import TrainingSessionSerializer, UserSerializer,UserProfileSerializer, VocabularyWordSerializer, TipSerializer, ProgressAnalyticsSerializer
from rest_framework import status
from rest_framework.permissions import IsAuthenticated, AllowAny
from django.contrib.auth import get_user_model
from .ai_modules import audio_analyzer
from rest_framework.parsers import MultiPartParser, FormParser
from django.core.files.storage import default_storage
import uuid
from pathlib import Path
from pydub import AudioSegment
# Create your views here.

User = get_user_model()
# source helper: https://www.bezkoder.com/django-rest-api/
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

# to do (post)
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
    parser_classes = (MultiPartParser, FormParser)

    # Source helper: https://stackoverflow.com/questions/20473572/django-rest-framework-file-upload
    def post(self, request):
            audio_file = request.FILES.get('audio_file')
            training_type = request.data.get('training_type', 'voice')
            duration = int(request.data.get('duration', 0))
            word = request.data.get('word', '')
            
            if not audio_file:
                return Response({'Audio file is required'}, status=status.HTTP_400_BAD_REQUEST)
            if duration <= 0:
                return Response({'Duration must be greater than 0'}, status=status.HTTP_400_BAD_REQUEST)
            
            # Source helper : https://www.geeksforgeeks.org/python/how-to-get-file-extension-in-python/
            # to get file extension
            file_ext = Path(audio_file.name).suffix if audio_file.name else '.webm'
            if not file_ext:
                file_ext = '.webm'
            
            file_ext = Path(audio_file.name).suffix if audio_file.name else '.webm'
            # Source helper : https://www.geeksforgeeks.org/python/generating-random-ids-using-uuid-python/
            # generate random id number for the saving audio files
            temp_filename = f"temp_audio/{uuid.uuid4()}{file_ext}"
            temp_path = default_storage.save(temp_filename, audio_file)
            full_temp_path = default_storage.path(temp_path)
            
            wav_filename = f"temp_audio/{uuid.uuid4()}.wav"
            wav_path = default_storage.path(wav_filename)
            audio = AudioSegment.from_file(full_temp_path)
            audio = audio.set_channels(1).set_frame_rate(16000)  # mono 16kHz
            audio.export(wav_path, format="wav")
            
            default_storage.delete(temp_path)

            # Transcribe audio using audio_analyzer from audio_analysis ai model
            transcription_result = audio_analyzer.transcribe_audio(wav_path)
            if not transcription_result or 'text' not in transcription_result:
                default_storage.delete(wav_path)
                return Response({'error': 'Transcription failed'}, status=status.HTTP_400_BAD_REQUEST)

            transcribed_text = transcription_result['text']

            
            # audio analysis calculate_overall_score
            analysis_result = audio_analyzer.calculate_overall_score(
                transcribed_text=transcribed_text,
                audio_duration_seconds=duration,
                audio_path=  wav_path  
            )
            
            if not analysis_result:
                default_storage.delete(wav_path)
                return Response({'Analysis failed'}, status=status.HTTP_400_BAD_REQUEST)
            
            # it create new TrainingSession save the data to db
            training_session = TrainingSession.objects.create(
                # link session to the user 
                user=request.user,
                training_type=training_type,
                duration=duration,
                # audio_file=audio_file,
                score=analysis_result.get('score', 0),
                mispronunciations=analysis_result.get('mis_pct', 0),
                repeated_words=analysis_result.get('repeated', 0),
                feedback_text=analysis_result.get('feedback', ''),
                transcribed_text= transcribed_text 
            )
            
            profile = UserProfile.objects.get(user=request.user)
            # add to the total_training_time the duration
            profile.total_training_time += duration
            # and save it to the db
            profile.save()
            
            
            
            Progress_Analytics = ProgressAnalytics.objects.get(user=request.user)
            # update total_sessions
            Progress_Analytics.total_sessions = Progress_Analytics.total_sessions + 1 
            Progress_Analytics.total_training_time = Progress_Analytics.total_training_time + duration
            
            # to get all user sessions
            all_sessions = TrainingSession.objects.filter(user=request.user)
            # loop and save all scores for the user in TrainingSession
            scores = []
            for session in all_sessions:
                score = session.score
                scores.append(score)
                
            #source helper: https://stackoverflow.com/questions/64692048/how-to-get-average-highest-and-lowest-values-of-input-values
            if scores:
                Progress_Analytics.average_score = sum(scores) / len(scores)
                Progress_Analytics.best_score = max(scores)
                Progress_Analytics.worst_score = min(scores)
                
            # save all data and analysis in ProgressAnalytics db
            Progress_Analytics.save()
            
            serializer = TrainingSessionSerializer(training_session)
            response_data = {
                **serializer.data,
                'analysis': {
                    'wpm': analysis_result.get('wpm', 0),
                    'rating': analysis_result.get('rating'),
                    'word': word,
                    'mispronounced_words': analysis_result.get('mispronounced_words', []),
                    'repeated_words': analysis_result.get('repeated_words', []),
                    'pauses_percentage': analysis_result.get('pauses_percentage'),
                }
            }
            default_storage.delete(wav_path)
            return Response(response_data, status=status.HTTP_201_CREATED)
        
              
class TrainingSessionView(APIView):

    permission_classes = [IsAuthenticated]

    # to get all the training sessions for the user 
    def get(self, request):
        sessions = TrainingSession.objects.filter(user=request.user)
        serializer = TrainingSessionSerializer(sessions, many=True)
        return Response(serializer.data)
    
class TrainingSessionDetailView(APIView):
    permission_classes = [IsAuthenticated]
    
    def get_object(self, user, session_id):
        try:
            return TrainingSession.objects.get(id=session_id, user=user)
        except TrainingSession.DoesNotExist:
            return None
    
    def get(self, request, session_id):
        session = self.get_object(request.user, session_id)
        if not session:
            return Response({'error': 'Training session not found'}, status=status.HTTP_404_NOT_FOUND)
        serializer = TrainingSessionSerializer(session)
        return Response(serializer.data)
    
    def delete(self, request, session_id):
        session = self.get_object(request.user, session_id)
        if not session:
            return Response({'error': 'Training session not found'}, status=status.HTTP_404_NOT_FOUND)
        session.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)

# to get one random word for the voice training 
class VocabularyView(APIView):
    permission_classes = [AllowAny]

    def get(self, request):
        word = VocabularyWord.objects.order_by('?').first()
        
        if not word:
            return Response({'error': 'No words'}, status=status.HTTP_404_NOT_FOUND)
        
        serializer = VocabularyWordSerializer(word)
        return Response(serializer.data)
    

# to get one random word for the voice training 
class TipView(APIView):
    permission_classes = [AllowAny]

    def get(self, request):
        tip = Tip.objects.order_by('?').first()
        
        if not tip:
            return Response({'error': 'No tips'}, status=status.HTTP_404_NOT_FOUND)
        
        serializer = TipSerializer(tip)
        return Response(serializer.data)
    
class TipView(APIView):
    permission_classes = [AllowAny]  # GET is public

    def get(self, request):
        tip = Tip.objects.order_by('?').first()
        
        if not tip:
            return Response({'error': 'No tips'}, status=status.HTTP_404_NOT_FOUND)
        
        serializer = TipSerializer(tip)
        return Response(serializer.data)


class TipListView(APIView):
    permission_classes = [IsAuthenticated]
    
    def get(self, request):
        if not request.user.is_staff:
            return Response({'error': 'Admin only'}, status=status.HTTP_403_FORBIDDEN)
        
        tips = Tip.objects.all()
        serializer = TipSerializer(tips, many=True)
        return Response(serializer.data)
    
    def post(self, request):
        if not request.user.is_staff:
            return Response({'error': 'Admin only'}, status=status.HTTP_403_FORBIDDEN)
        
        serializer = TipSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class TipDetailView(APIView):
    permission_classes = [IsAuthenticated]
    
    def get_object(self, tip_id):
        try:
            return Tip.objects.get(id=tip_id)
        except Tip.DoesNotExist:
            return None
    
    def get(self, request, tip_id):
        if not request.user.is_staff:
            return Response({'error': 'Admin only'}, status=status.HTTP_403_FORBIDDEN)
        
        tip = self.get_object(tip_id)
        if not tip:
            return Response({'error': 'Tip not found'}, status=status.HTTP_404_NOT_FOUND)
        
        serializer = TipSerializer(tip)
        return Response(serializer.data)
    
    def put(self, request, tip_id):
        if not request.user.is_staff:
            return Response({'error': 'Admin only'}, status=status.HTTP_403_FORBIDDEN)
        
        tip = self.get_object(tip_id)
        if not tip:
            return Response({'error': 'Tip not found'}, status=status.HTTP_404_NOT_FOUND)
        
        serializer = TipSerializer(tip, data=request.data, partial=True)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    
    def delete(self, request, tip_id):
        if not request.user.is_staff:
            return Response({'error': 'Admin only'}, status=status.HTTP_403_FORBIDDEN)
        
        tip = self.get_object(tip_id)
        if not tip:
            return Response({'error': 'Tip not found'}, status=status.HTTP_404_NOT_FOUND)
        
        tip.delete()
        return Response({'message': 'Tip deleted'}, status=status.HTTP_204_NO_CONTENT)
    
    
class ProgressAnalyticsView(APIView):
     permission_classes = [IsAuthenticated]
     
     def get(self, request):
        try:
            Progress_Analytics = ProgressAnalytics.objects.get(user=request.user)
            serializer = ProgressAnalyticsSerializer(Progress_Analytics)
            return Response(serializer.data)
        except ProgressAnalytics.DoesNotExist:
            return Response(
                {'error': 'Progress Analytics not found'},
                status=status.HTTP_404_NOT_FOUND
            )