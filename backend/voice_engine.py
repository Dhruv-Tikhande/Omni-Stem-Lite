# voice_engine.py
from faster_whisper import WhisperModel
import time

model_size = "small" # We use small for testing speed

print("Loading Omni-STEM Voice Engine...")
# Using CPU for now so it works on any laptop
model = WhisperModel(model_size, device="cpu", compute_type="int8")

def transcribe_audio(audio_file_path):
    start_time = time.time()
    print(f"Listening to {audio_file_path}...")
    
    segments, info = model.transcribe(audio_file_path, beam_size=5)
    
    print(f"Detected language: '{info.language}' with {info.language_probability*100:.1f}% confidence")
    
    full_text = ""
    for segment in segments:
        full_text += segment.text + " "
        
    end_time = time.time()
    print(f"Transcription Latency: {end_time - start_time:.2f} seconds")
    print(f"User Query: {full_text.strip()}")

# Make sure this matches the name of the file you recorded!
transcribe_audio("test_audio.wav")