from django.shortcuts import render
from rest_framework.views import APIView
from rest_framework.response import Response
from .models import TrainingSession
from .serializers import TrainingSessionSerializer
from rest_framework import generics,status
from rest_framework.permissions import IsAuthenticated, AllowAny
from django.contrib.auth import get_user_model
from django.shortcuts import get_object_or_404

# Create your views here.

User = get_user_model()