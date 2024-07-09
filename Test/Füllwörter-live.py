import os
import json
import re
import numpy as np
import time
from collections import defaultdict
import whisper_timestamped as whisper
from scipy.io import wavfile
from pydub import AudioSegment

def extract_audio(audio_path):
    sound = AudioSegment.from_wav(audio_path)
    sound = sound.set_channels(1).set_frame_rate(16000)
    sound.export(audio_path, format="wav")
    
    return audio_path

def transcribe_audio_with_disfluencies(audio_path):
    model = whisper.load_model("tiny")
    result = whisper.transcribe(model, audio_path, language="en", detect_disfluencies=True)
    segments = result["segments"]
    
    return segments, result["text"]

def extract_filler_words(transcription, additional_filler_words):
    filler_word_pattern = re.compile(r'\[\*\]')
    additional_filler_words_set = set(word.lower() for word in additional_filler_words)
    filler_words_by_minute = defaultdict(list)

    for segment in transcription:
        words_buffer = []
        for word_info in segment['words']:
            word_text = word_info['text']
            words_buffer.append((word_text, word_info['start']))

            if filler_word_pattern.search(word_text.lower()) or word_text.lower() in additional_filler_words_set:
                minute = int(word_info['start'] // 60)
                filler_words_by_minute[minute].append(word_text)
                words_buffer = []

            for i in range(len(words_buffer)):
                phrase = ' '.join(w[0].lower() for w in words_buffer[i:])
                if phrase in additional_filler_words_set:
                    minute = int(words_buffer[i][1] // 60)
                    filler_words_by_minute[minute].append(' '.join(w[0] for w in words_buffer[i:]))
                    words_buffer = []
                    break

    return filler_words_by_minute

def save_filler_word_analysis(filler_words_by_minute, output_path):
    analysis_results = {minute: {"fillers_count": len(filler_words)} for minute, filler_words in filler_words_by_minute.items()}
    with open(output_path, 'w') as outfile:
        json.dump(analysis_results, outfile, indent=4)
    print(f"Filler word analysis saved to {output_path}")

def main():
    additional_filler_words = ["um", "umm", "uum", "ah", "aah", "ahh", "uh", "uuh", "uhh", "er", "eer", "err", "so", "soo", "okay", "sorry", "well", "but", "right", "and so", "you know", "i think", "ähm", "äh", "öhm", "hmm"]

    while True:
        audio_path = "temp_audio.wav"
        extract_audio(audio_path)

        segments, transcription = transcribe_audio_with_disfluencies(audio_path)
        filler_words_by_minute = extract_filler_words(segments, additional_filler_words)
        save_filler_word_analysis(filler_words_by_minute, "filler_word_analysis.json")
        
        time.sleep(5)

if __name__ == "__main__":
    main()
