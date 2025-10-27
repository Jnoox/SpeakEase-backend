from django.db import models

# Create your models here.


# TrainingSession model
class TrainingSession(models.Model):
    TRAINING_TYPES = [
        ('voice', 'Voice Training'),
        ('conversation', 'Camera Conversation'),
    ]

    training_type = models.CharField(max_length=20, choices=TRAINING_TYPES)
    duration = models.PositiveIntegerField(help_text="Duration in seconds")
    audio_file = models.FileField(upload_to='audio/', null=True, blank=True)
    video_file = models.FileField(upload_to='videos/', null=True, blank=True)
    feedback_text = models.TextField(blank=True)

    # performance metrics
    repeated_words = models.PositiveIntegerField(default=0)
    mispronunciations = models.PositiveIntegerField(default=0)
    facial_feedback_score = models.FloatField(default=0.0)
    score = models.FloatField(null=True, blank=True)

    created_at = models.DateTimeField(auto_now_add=True)
    last_updated = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.training_type.capitalize()} Training - {self.created_at.strftime('%Y-%m-%d')}"

