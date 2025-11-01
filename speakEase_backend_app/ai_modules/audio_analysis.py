# source helper https://thepythoncode.com/article/speech-recognition-in-python

import speech_recognition as sr
import os 
from pydub import AudioSegment
from pydub.silence import split_on_silence

from transformers import WhisperProcessor, WhisperForConditionalGeneration
import torch
import librosa
import torch

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

def get_phonemes(word):
    word = word.lower()
    if word in pronouncing_dict:
        return pronouncing_dict[word][0]  # list of phonemes
    else:
        # Use machine phoneme generator
        return g2p(word)

def phoneme_similarity(p1, p2):
    """Return similarity ratio between two phoneme lists"""
    return SequenceMatcher(None, p1, p2).ratio()

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

def get_large_audio_transcription_on_silence(path):
     # open the audio file using pydub
    sound = AudioSegment.from_file(path)  
    # split audio sound where silence is 700 miliseconds or more and get chunks
    chunks = split_on_silence(sound,
        # experiment with this value for your target audio file
        min_silence_len = 500,
        # adjust this per requirement
        silence_thresh = sound.dBFS-14,
        # keep the silence for 1 second, adjustable as well
        keep_silence=500,
    )
    folder_name = "audio-chunks"
    # create a directory to store the audio chunks
    if not os.path.isdir(folder_name):
        os.mkdir(folder_name)
    whole_text = ""
    # process each chunk 
    for i, audio_chunk in enumerate(chunks, start=1):
        # export audio chunk and save it in
        # the `folder_name` directory.
        chunk_filename = os.path.join(folder_name, f"chunk{i}.wav")
        audio_chunk.export(chunk_filename, format="wav")
        # recognize the chunk
        with sr.AudioFile(chunk_filename) as source:
            audio_listened = r.record(source)
            # try converting it to text
            try:
                text = r.recognize_google(audio_listened)
            except sr.UnknownValueError as e:
                print("Error:", str(e))
            else:
                text = f"{text.capitalize()}. "
                print(chunk_filename, ":", text)
                whole_text += text
    # return the text for all chunks detected
    return whole_text

# print(get_large_audio_transcription_on_silence("speakEase_backend_app/test_audio/record_out.wav"))

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
  """Load the audio file & convert to 16,000 sampling rate"""
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

def detect_mispronunciations(text):
    words = text.lower().split()
    mispronounced = []

    for word in words:
        phonemes = get_phonemes(word)
        # If Whisper recognized word incorrectly → phonemes far from typical
        similarity = phoneme_similarity(phonemes, get_phonemes(word))

        if similarity < 0.55:  
            mispronounced.append(word)

    return mispronounced

if __name__ == "__main__":
    
    expected_word = "sun" 
    
    english_transcription = get_transcription_whisper("speakEase_backend_app/test_audio/record_out (5).wav",
                            whisper_model,
                            whisper_processor,
                            language="english",
                            skip_special_tokens=True)
    print("English transcription:", english_transcription)
    
    english_mis = detect_mispronunciations(english_transcription)
    print("English Mispronounced Words:", english_mis)
    
    arabic_transcription = get_transcription_whisper("speakEase_backend_app/test_audio/record_arabic.wav",
                          whisper_model,
                          whisper_processor,
                          language="arabic",
                          skip_special_tokens=True)
    print("Arabic transcription:", arabic_transcription)
    
    arabic_mis = detect_mispronunciations(arabic_transcription)
    print("Arabic Mispronounced Words:", arabic_mis)