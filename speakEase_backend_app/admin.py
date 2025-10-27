from django.contrib import admin
from .models import TrainingSession, ProgressAnalytics, Tip

# Register your models here.
admin.site.register(TrainingSession)
admin.site.register(ProgressAnalytics)
admin.site.register(Tip)