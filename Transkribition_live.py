import os
import sys
import json
import re
import numpy as np
from collections import defaultdict
from moviepy.editor import VideoFileClip
from pydub import AudioSegment
import whisper_timestamped as whisper

def extract_audio(video_path):
    if not os.path.isfile(video_path):
        raise FileNotFoundError(f"The file {video_path} does not exist.")
    
    video_clip = VideoFileClip(video_path)
    audio_clip = video_clip.audio
    audio_path = "temp_audio.wav"
    audio_clip.write_audiofile(audio_path, codec='pcm_s16le')
    
    # Ensure the audio is in the correct format (mono PCM)
    sound = AudioSegment.from_wav(audio_path)
    sound = sound.set_channels(1).set_frame_rate(16000)
    sound.export(audio_path, format="wav")
    
    return audio_path

def transcribe_audio_with_disfluencies(audio_path):
    # Load the Whisper model
    model = whisper.load_model("tiny")
    
    # Transcribe audio with timestamps and detect disfluencies
    result = whisper.transcribe(model, audio_path, language="en", detect_disfluencies=True)
    segments = result["segments"]
    
    return segments, result["text"]

def extract_filler_words(transcription, additional_filler_words):
    # Regular expression to match words with [*]
    filler_word_pattern = re.compile(r'\[\*\]')
    
    # Create a set of additional filler words for exact matching, ignoring case
    additional_filler_words_set = set(word.lower() for word in additional_filler_words)
    
    filler_words_by_minute = defaultdict(list)

    for segment in transcription:
        words_buffer = []
        for word_info in segment['words']:
            word_text = word_info['text']  # Keep the original case for output
            words_buffer.append((word_text, word_info['start']))
            
            # Check for single-word fillers
            if filler_word_pattern.search(word_text.lower()) or word_text.lower() in additional_filler_words_set:
                minute = int(word_info['start'] // 60)
                filler_words_by_minute[minute].append(word_text)
                words_buffer = []

            # Check for multi-word fillers
            for i in range(len(words_buffer)):
                phrase = ' '.join(w[0].lower() for w in words_buffer[i:])
                if phrase in additional_filler_words_set:
                    minute = int(words_buffer[i][1] // 60)
                    filler_words_by_minute[minute].append(' '.join(w[0] for w in words_buffer[i:]))  # Append original case
                    words_buffer = []
                    break

    return filler_words_by_minute

def save_filler_word_analysis(filler_words_by_minute, output_path):
    analysis_results = {minute: {"fillers_count": len(filler_words)} for minute, filler_words in filler_words_by_minute.items()}
    with open(output_path, 'w') as outfile:
        json.dump(analysis_results, outfile, indent=4)
    print(f"Filler word analysis saved to {output_path}")

def main(video_path, output_path):
    audio_path = extract_audio(video_path)

    # Define the additional filler words in the code
    additional_filler_words = ["um", "umm", "uum", "ah", "aah", "ahh", "uh", "uuh", "uhh", "er", "eer", "err", "so", "soo", "okay", "sorry", "well", "but", "right", "and so", "you know", "i think", "ähm", "äh", "öhm", "hmm"]

    segments, transcription = transcribe_audio_with_disfluencies(audio_path)

    filler_words_by_minute = extract_filler_words(segments, additional_filler_words)
    save_filler_word_analysis(filler_words_by_minute, output_path)

if __name__ == "__main__":
    if len(sys.argv) != 3:
        print("Usage: python Transkribition_live.py <path_to_video> <path_to_output_json>")
        sys.exit(1)

    video_path = sys.argv[1]
    output_path = "_static/global/filler_word_analysis.json"

    if not os.path.isfile(video_path):
        raise FileNotFoundError(f"The file {video_path} does not exist.")
    
    main(video_path, output_path)
