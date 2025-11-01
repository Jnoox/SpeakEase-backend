import speech_recognition as sr
from pydub import AudioSegment
import librosa
import numpy as np
from collections import Counter

# source helper https://github.com/Uberi/speech_recognition
class AudioAnalyzer:
    def __init__(self):
        self.recognizer = sr.Recognizer()
        self.recognizer.energy_threshold = 4000
        
    def full_analysis(self, audio_file_path, expected_word, duration_seconds):
        print(f"[AUDIO] Starting analysis for: {expected_word}")
        
        transcription_result = self.transcribe_audio(audio_file_path)
        if not transcription_result['success']:
            return {'success': False, 'error': transcription_result['error'], 'score': 0}
        
        transcribed_text = transcription_result['text']
        mispronunciations = self.detect_mispronunciations(transcribed_text, expected_word)
        repeated_words = self.detect_repeated_words(transcribed_text)
        speech_rate = self.analyze_speech_rate(audio_file_path, duration_seconds)
        pause_frequency = self.analyze_pause_frequency(audio_file_path)
        
        score = self.calculate_score(mispronunciations, repeated_words, speech_rate, pause_frequency, duration_seconds)
        feedback = self.generate_detailed_feedback(mispronunciations, repeated_words, speech_rate, pause_frequency, transcribed_text)
        
        return {
            'success': True,
            'transcribed_text': transcribed_text,
            'mispronunciations': mispronunciations,
            'repeated_words': repeated_words,
            'speech_rate': speech_rate,
            'pause_frequency': pause_frequency,
            'score': score,
            'feedback': feedback
        }
        
    def transcribe_audio(self, audio_file_path):
        try:
            if audio_file_path.lower().endswith('.mp3'):
                sound = AudioSegment.from_mp3(audio_file_path)
                wav_path = audio_file_path.replace('.mp3', '.wav')
                sound.export(wav_path, format="wav")
                audio_file_path = wav_path
            
            with sr.AudioFile(audio_file_path) as source:
                audio = self.recognizer.record(source)
            text = self.recognizer.recognize_google(audio)
            return {'success': True, 'text': text}
        except sr.UnknownValueError:
            return {'success': False, 'error': 'Could not understand audio. Please speak clearly.'}
        except sr.RequestError as e:
            return {'success': False, 'error': f'API error: {str(e)}'}
