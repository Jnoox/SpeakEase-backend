import speech_recognition as sr
from pydub import AudioSegment
import librosa
import numpy as np
from collections import Counter

class AudioAnalyzer:
    def __init__(self):
        self.recognizer = sr.Recognizer()
        self.recognizer.energy_threshold = 4000