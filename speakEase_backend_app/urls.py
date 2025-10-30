from django.urls import path
from .views import TrainingSessionListCreateView, UserSignUpView

urlpatterns = [
   path('signup/', UserSignUpView.as_view(), name='user-register'),
   path('training-sessions/', TrainingSessionListCreateView.as_view(), name='training-sessions-list'),    
]