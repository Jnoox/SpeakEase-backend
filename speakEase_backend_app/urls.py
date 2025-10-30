from django.urls import path
from .views import TrainingSessionListCreateView, UserSignUpView, AllUsersView, CurrentUserView
from rest_framework_simplejwt.views import TokenObtainPairView, TokenRefreshView

urlpatterns = [
   path('users/signup/', UserSignUpView.as_view(), name='user-signup'),
   path('users/current/', CurrentUserView.as_view(), name='current-user'),
   path('users/', AllUsersView.as_view(), name='all-users'),
   path('login/', TokenObtainPairView.as_view(), name='login'),
   path('token/refresh/', TokenRefreshView.as_view(), name='token_refresh'),
   path('training-sessions/', TrainingSessionListCreateView.as_view(), name='training-sessions-list'),    
]