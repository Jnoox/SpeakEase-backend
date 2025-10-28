from django.shortcuts import render
from rest_framework.views import APIView
from rest_framework.response import Response
from .models import TrainingSession
from .serializers import TrainingSessionSerializer
from rest_framework import generics,status

# Create your views here.
