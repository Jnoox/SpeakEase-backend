from rest_framework import serializers
from django.contrib.auth import get_user_model
from .models import TrainingSession, ProgressAnalytics, Tip, UserProfile, VocabularyWord,DailyQuestion

User = get_user_model()

class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = '__all__'

class UserProfileSerializer(serializers.ModelSerializer):
    user = UserSerializer(read_only=True)

    class Meta:
        model = UserProfile
        fields = '__all__'
        
class TrainingSessionSerializer(serializers.ModelSerializer):
    # get the username from User model
    user_username = serializers.CharField(source='user.username', read_only=True)
    class Meta:
        model = TrainingSession
        fields = '__all__'

class ProgressAnalyticsSerializer(serializers.ModelSerializer):
    # get the username from User model
    user_username = serializers.CharField(source='user.username', read_only=True)
    class Meta:
        model = ProgressAnalytics
        fields = '__all__'

class TipSerializer(serializers.ModelSerializer):
    class Meta:
        model = Tip
        fields = '__all__'

class VocabularyWordSerializer(serializers.ModelSerializer):
    class Meta:
        model = VocabularyWord
        fields = '__all__'
        
class DailyQuestionSerializer(serializers.ModelSerializer):
    class Meta:
        model = DailyQuestion
        fields = '__all__'