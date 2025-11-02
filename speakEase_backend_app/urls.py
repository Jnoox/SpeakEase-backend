from django.urls import path
from .views import TrainingSessionView, UserSignUpView, AllUsersView, CurrentUserView, UserProfileView, VoiceTrainingView, TrainingSessionDetailView
from rest_framework_simplejwt.views import TokenObtainPairView, TokenRefreshView

urlpatterns = [
   path('users/signup/', UserSignUpView.as_view(), name='user-signup'),
   path('users/current/', CurrentUserView.as_view(), name='current-user'),
   path('users/', AllUsersView.as_view(), name='all-users'),
   path('profile/', UserProfileView.as_view(), name='user-profile'),
   path('login/', TokenObtainPairView.as_view(), name='login'),
   path('token/refresh/', TokenRefreshView.as_view(), name='token_refresh'),
   path('training/voice/', VoiceTrainingView.as_view(), name='voice-training'), 
   path('training-sessions/', TrainingSessionView.as_view(), name='training-sessions-list'),
   path('training-sessions/<int:session_id>/', TrainingSessionDetailView.as_view(), name='training-session-detail'),

]