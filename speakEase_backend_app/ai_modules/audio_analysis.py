# source helper https://thepythoncode.com/article/speech-recognition-in-python
# https://www.geeksforgeeks.org/python/how-to-get-the-duration-of-audio-in-python/
# https://shahabks.github.io/my-voice-analysis/

import speech_recognition as sr
import os 
from pydub import AudioSegment
from pydub.silence import split_on_silence
import numpy as np
import pronouncing


from transformers import WhisperProcessor, WhisperForConditionalGeneration
import torch
import librosa
import torch

import mutagen
from mutagen.wave import WAVE
from collections import Counter


# Carnegie Mellon University Pronouncing Dictionary
import nltk
nltk.download('cmudict')
nltk.download('averaged_perceptron_tagger_eng')
from nltk.corpus import cmudict
pronouncing_dict = cmudict.dict()
from difflib import SequenceMatcher

# phoneme generator fallback for unknown words
from g2p_en import G2p
g2p = G2p()

# Creating a Recognizer instance
r = sr.Recognizer()

# a function to recognize speech in the audio file
def transcribe_audio(path):
    # use the audio file as the audio source
    with sr.AudioFile(path) as source:
        audio_listened = r.record(source)
        # try converting it to text
        text = r.recognize_google(audio_listened)
    return text

device = "cuda:0" if torch.cuda.is_available() else "cpu"
# whisper_model_name = "openai/whisper-tiny.en" # English-only, ~ 151 MB
# whisper_model_name = "openai/whisper-base.en" # English-only, ~ 290 MB
# whisper_model_name = "openai/whisper-small.en" # English-only, ~ 967 MB
# whisper_model_name = "openai/whisper-medium.en" # English-only, ~ 3.06 GB
whisper_model_name = "openai/whisper-small" 
# whisper_model_name = "openai/whisper-base" # multilingual, ~ 290 MB
# whisper_model_name = "openai/whisper-small" # multilingual, ~ 967 MB
# whisper_model_name = "openai/whisper-medium" # multilingual, ~ 3.06 GB
# whisper_model_name = "openai/whisper-large-v2" # multilingual, ~ 6.17 GB

# load the model and the processor
whisper_processor = WhisperProcessor.from_pretrained(whisper_model_name)
whisper_model = WhisperForConditionalGeneration.from_pretrained(whisper_model_name).to(device)

def load_audio(audio_path):
  # load our wav file
  speech, sr = librosa.load(audio_path, sr=16000)
  speech = librosa.util.normalize(speech) 
  return torch.tensor(speech)

def get_transcription_whisper(audio_path, model, processor, language="english", skip_special_tokens=True):
  # resample from whatever the audio sampling rate to 16000
  speech = load_audio(audio_path)
  # get the input features from the audio file
  input_features = processor(speech, return_tensors="pt", sampling_rate=16000).input_features.to(device)
  # get the forced decoder ids
  forced_decoder_ids = processor.get_decoder_prompt_ids(language=language, task="transcribe")
  # generate the transcription
  predicted_ids = model.generate(input_features, forced_decoder_ids=forced_decoder_ids)
  # decode the predicted ids
  transcription = processor.batch_decode(predicted_ids, skip_special_tokens=skip_special_tokens)[0]
  return transcription

def detect_mispronunciations(transcribed_text):
    transcribed_words = transcribed_text.lower().split()
    
    mispronounced = []
    valid_words = []
    
    # Check each word against CMU dictionary
    for word in transcribed_words:
        word_clean = word.lower().strip('.,!?;:')
        
        phones = pronouncing.phones_for_word(word_clean)
        
        if not phones:      
            mispronounced.append(word_clean)
        else:
            valid_words.append(word_clean)
            
    return {
        'mispronounced_words': mispronounced,
        'valid_words': valid_words,
        'total_words': len(transcribed_words),
        'mispronunciation_count': len(mispronounced)
    }
    
def get_audio_duration(audio_path):
    try:
        y, sr_val = librosa.load(audio_path)
        length = librosa.get_duration(y=y, sr=sr_val)  # in seconds
        
        hours = int(length // 3600)
        remaining = length % 3600
        mins = int(remaining // 60)
        seconds = int(remaining % 60)
        
        return hours, mins, seconds
    except Exception as e:
        print(f"Error reading audio: {e}")
        return 0, 0, 0

def detect_repeated_words(transcribed_text):
    """Detect repeated words using Counter"""
    words = transcribed_text.lower().split()
    
    # Common stop words to ignore
    stop_words = {'the', 'a', 'an', 'and', 'or', 'is', 'are', 'was', 'were', 
                  'be', 'been', 'of', 'in', 'to', 'for', 'i', 'you', 'he', 'she', 'it'}
    
    # Remove stop words and punctuation
    filtered_words = []
    for word in words:
        word_clean = word.lower().strip('.,!?;:')
        if word_clean not in stop_words and word_clean:
            filtered_words.append(word_clean)
    
    # Count word frequencies
    word_counts = Counter(filtered_words)
    
    # Get words that appear more than once
    repeated_words = {word: count for word, count in word_counts.items() if count > 1}
    
    return {
        'repeated_words': repeated_words,
        'total_repeated': len(repeated_words),
        'all_word_counts': word_counts
    }
    
# Calculate speech rate (words per minute - WPM)
def calculate_speech_rate(transcribed_text, audio_duration_seconds):
    # Count words in transcription
    words = transcribed_text.lower().split()
    word_count = len(words)
    
    # Convert duration from seconds to minutes
    duration_minutes = audio_duration_seconds / 60
    
    # Calculate WPM (words per minute)
    if duration_minutes > 0:
        wpm = word_count / duration_minutes
    else:
        wpm = 0
    
    if wpm < 120:
        speed_category = "Slow"
    elif wpm <= 150:
        speed_category = "Normal"
    else:
        speed_category = "Fast"
    
    return {
        'word_count': word_count,
        'duration_seconds': audio_duration_seconds,
        'duration_minutes': round(duration_minutes, 2),
        'wpm': round(wpm, 2),
        'speed_category': speed_category
    }
    

# source helper: https://github.com/ahmedayman9/Audio-Silence-Detection-and-Pause-Percentage-Calculation/blob/main/Pauses%20detection.ipynb
def detect_pauses(audio_path, threshold=0.005):
    try:
        # Load audio file
        y, sr_val = librosa.load(audio_path)
        energy = librosa.feature.rms(y=y)
        
        #silence less sensitive 
        silence_indices = np.where(energy < threshold)[1]
        
        silence_times = librosa.frames_to_time(silence_indices, sr=sr_val)
        frame_duration = librosa.get_duration(y=y, sr=sr_val) / len(energy[0])
        
        total_silence_time = round(frame_duration * len(silence_times), 2)
        total_audio_time = len(y) / sr_val
        pauses_percentage = round((total_silence_time / total_audio_time) * 100, 2)
        
        return {
            'total_silence_time': total_silence_time,
            'total_audio_time': total_audio_time,
            'pauses_percentage': pauses_percentage
        }
    except Exception as e:
        print(f"Error detecting pauses: {e}")
        return None

# Calculate overall score 0-100
# Source helper : https://stackoverflow.com/questions/27337331/how-do-i-make-a-score-counter-in-python
def calculate_overall_score(transcribed_text, audio_duration_seconds, audio_path):
    score = 100.0
    
    # Get metrics
    mis = detect_mispronunciations(transcribed_text)
    rep = detect_repeated_words(transcribed_text)
    sr = calculate_speech_rate(transcribed_text, audio_duration_seconds)
    pa = detect_pauses(audio_path) 

    mis_pct = (mis['mispronunciation_count'] / mis['total_words'] * 100) if mis['total_words'] > 0 else 0
    if mis_pct > 25:
        score -= 30
    elif mis_pct > 10:
        score -= 15
    elif mis_pct > 0:
        score -= 5
    

    wpm = sr['wpm']
    if wpm < 100 or wpm > 170:
        score -= 15
    elif wpm < 120 or wpm > 150:
        score -= 5
    
    
    if rep['total_repeated'] > 5:
        score -= 15
    elif rep['total_repeated'] > 2:
        score -= 10
    elif rep['total_repeated'] > 0:
        score -= 5
    
    if pa:
        pauses = pa['pauses_percentage']
    if pauses > 40:
        score -= 5 
    elif pauses > 25:
        score -= 3   
    elif pauses > 10:
        score -= 1  
            
    if audio_duration_seconds > 0:
        ratio = mis['total_words'] / audio_duration_seconds
        if ratio < 2.0:
            score -= 10
        elif ratio < 2.5:
            score -= 5
    
    final_score = max(0, min(100, score))
    
    
    feedback = []
    
    if mis_pct == 0:
        feedback.append("Perfect pronunciation ✓")
    elif mis_pct < 10:
        feedback.append("Good pronunciation ✓")
    elif mis_pct < 25:
        feedback.append("Work on pronunciation clarity ⚠")
    else:
        feedback.append("Practice pronunciation more ❌")
    
    if 120 <= wpm <= 150:
        feedback.append("Good speech rate ✓")
    elif wpm < 120:
        feedback.append("Speak faster (aim for 120-150 WPM) ⚠")
    else:
        feedback.append("Slow down (aim for 120-150 WPM) ⚠")
    
    if rep['total_repeated'] == 0:
        feedback.append("Good vocabulary variation ✓")
    elif rep['total_repeated'] <= 2:
        feedback.append("Decent vocabulary ✓")
    elif rep['total_repeated'] <= 5:
        feedback.append("Use more varied vocabulary ⚠")
    else:
        feedback.append("Reduce word repetition ❌")
        
    if pa:
        pauses = pa['pauses_percentage']
        if pauses <= 5:
            feedback.append("Good pause control ✓")
        elif pauses <= 15:
            feedback.append("Decent pause usage ✓")
        elif pauses <= 30:
            feedback.append("Reduce excessive pauses ⚠")
        else:
            feedback.append("Too many pauses, work on fluency ❌")
    
    if final_score >= 90:
        rating = "Excellent 🌟"
    elif final_score >= 75:
        rating = "Good 👍"
    elif final_score >= 60:
        rating = "Fair 👌"
    elif final_score >= 45:
        rating = "Needs Improvement ⚠️"
    else:
        rating = "Poor ❌"
    
    return {
        'score': round(final_score, 2),
        'rating': rating,
        'feedback': " | ".join(feedback),
        'mis_pct': round(mis_pct, 2),
        'wpm': wpm,
        'repeated': rep['total_repeated'],
        'pauses_percentage': pa['pauses_percentage'] if pa else 0,
        'mispronounced_words': mis['mispronounced_words'],
        'repeated_words': rep['repeated_words'],
    }

# to return calculate_overall_score and transcribe_audio to use it in the view
class AudioAnalyzer:
    def calculate_overall_score(self, transcribed_text, audio_duration_seconds, audio_path):
        return calculate_overall_score(transcribed_text, audio_duration_seconds, audio_path)
    
    def transcribe_audio(self, audio_path):
        try:
            result = get_transcription_whisper(audio_path, whisper_model, whisper_processor)
            return {'success': True, 'text': result}
        except Exception as e:
            return {'success': False, 'error': str(e)}

audio_analyzer = AudioAnalyzer()


