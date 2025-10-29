from django.urls import path
from .views import TrainingSessionListCreateView

urlpatterns = [
   path('training-sessions/', TrainingSessionListCreateView.as_view(), name='training-sessions-list'),    
]