from django.db import models
from django.contrib.auth import get_user_model
from django.core.validators import MinValueValidator, MaxValueValidator

# Create your models here.


User = get_user_model()

# UserProfile Model extended from User model
class UserProfile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='profile')
    full_name = models.CharField(max_length=200, blank=True, default="")
    # to ensure the age between 1 to 120
    age = models.PositiveIntegerField(
    validators=[MinValueValidator(1), MaxValueValidator(120)]
    )
    total_training_time = models.PositiveIntegerField(default=0)  # in seconds
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.user.username}'s Profile"
    
# TrainingSession Model
class TrainingSession(models.Model):
    TRAINING_TYPES = [
        ('voice', 'Voice Training'),
        ('conversation', 'Camera Conversation'),
        ('tips', 'Tips & Motivation')
    ]
    
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='training_sessions')
    training_type = models.CharField(max_length=20, choices=TRAINING_TYPES)
    duration = models.PositiveIntegerField(help_text="Duration in seconds")
    audio_file = models.FileField(upload_to='audio/', null=True, blank=True)
    video_file = models.FileField(upload_to='videos/', null=True, blank=True)
    feedback_text = models.TextField(blank=True)
    transcribed_text = models.TextField(blank=True)
    # performance metrics
    repeated_words = models.PositiveIntegerField(default=0)
    mispronunciations = models.PositiveIntegerField(default=0)
    # this ensure scores never go negative or exceed 100
    score = models.FloatField(
        default=0.0,
        validators=[MinValueValidator(0.0), MaxValueValidator(100.0)]
    )
    facial_feedback_score = models.FloatField(
        default=0.0,
        validators=[MinValueValidator(0.0), MaxValueValidator(100.0)]
    )
    # set the confidence level
    confidence_level = models.CharField(
        max_length=20,
        choices=[('low', 'Low'), ('medium', 'Medium'), ('high', 'High')],
        default='medium'
    )
    eye_contact_score = models.FloatField(default=0.0)
    engagement_level = models.CharField(
        max_length=20,
        choices=[('disengaged', 'Disengaged'), ('neutral', 'Neutral'), ('engaged', 'Engaged')],
        default='neutral'
    )
    created_at = models.DateTimeField(auto_now_add=True)
    last_updated = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['-created_at']
    def __str__(self):
         return f"{self.user.username} - {self.training_type} ({self.created_at.date()})"

# ProgressAnalytics Model
class ProgressAnalytics(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='progress_analytics')
    total_sessions = models.PositiveIntegerField(default=0)
    average_score = models.FloatField(default=0.0)
    best_score = models.FloatField(default=0.0)
    worst_score = models.FloatField(default=0.0)
    improvement_rate = models.FloatField(default=0.0) 
    total_training_time = models.PositiveIntegerField(default=0) 
    last_updated = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"Progress Analytics for {self.user.username}"

# Tip Model
class Tip(models.Model):
    TIP_TYPES = [
        ('voice', 'Voice Tip'),
        ('conversation', 'Conversation Tip'),
        ('general', 'General Tip'),
    ]

    title = models.CharField(max_length=150)
    content = models.TextField()
    category = models.CharField(max_length=20, choices=TIP_TYPES, default='general')
    author = models.CharField(max_length=100, blank=True, default="SpeakEase Team")
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.category.capitalize()} - {self.title}"
    
# VocabularyWord Model (for "Describe a Word" training)
class VocabularyWord(models.Model):
    word = models.CharField(max_length=100, unique=True)
    definition = models.TextField()
    difficulty_level = models.CharField(
        max_length=20,
        choices=[('beginner', 'Beginner'), ('intermediate', 'Intermediate'), ('advanced', 'Advanced')],
        default='beginner'
    )
    # to give user example how to use the word in good sentence 
    example_sentence = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.word
    

# DailyQuestion Model (for "Daily Conversation" training)
class DailyQuestion(models.Model):
    question = models.CharField(max_length=300)
    category = models.CharField(
        max_length=50,
        choices=[('personal', 'Personal'), ('professional', 'Professional'), ('social', 'Social')],
        default='personal'
    )
    difficulty_level = models.CharField(
        max_length=20,
        choices=[('beginner', 'Beginner'), ('intermediate', 'Intermediate'), ('advanced', 'Advanced')],
        default='intermediate'
    )
    created_at = models.DateTimeField(auto_now_add=True)
    
    # for random order
    class Meta:
        ordering = ['?']  

    def __str__(self):
        return self.question
    