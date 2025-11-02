from django.contrib import admin
from .models import TrainingSession, ProgressAnalytics, Tip, VocabularyWord

# Register your models here.
admin.site.register(TrainingSession)
admin.site.register(ProgressAnalytics)
admin.site.register(Tip)
# to add vocably
admin.site.register(VocabularyWord)