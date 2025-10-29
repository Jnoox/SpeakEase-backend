from rest_framework import serializers
from django.contrib.auth import get_user_model
from .models import TrainingSession, ProgressAnalytics, Tip, UserProfile, VocabularyWord,DailyQuestion



class TrainingSessionSerializer(serializers.ModelSerializer):
    class Meta:
        model = TrainingSession
        fields = '__all__'

class ProgressAnalyticsSerializer(serializers.ModelSerializer):
    class Meta:
        model = ProgressAnalytics
        fields = '__all__'

class TipSerializer(serializers.ModelSerializer):
    class Meta:
        model = Tip
        fields = '__all__'


