import whisper_timestamped as whisper
import re
from collections import defaultdict

def extract_filler_words(transcription, additional_filler_words):
    # Regular expression to match words with [*]
    filler_word_pattern = re.compile(r'\[\*\]')
    
    # Create a set of additional filler words for exact matching, ignoring case
    additional_filler_words_set = set(word.lower() for word in additional_filler_words)
    
    filler_words_by_minute = defaultdict(list)

    for segment in transcription['segments']:
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

# List of additional filler words
additional_filler_words = ["um", "umm", "uum", "ah", "aah", "ahh", "uh", "uuh", "uhh", "er", "eer", "err", "so", "soo", "okay", "sorry", "well", "but", "right", "and so", "you know", "i think", "ähm", "äh", "öhm", "hmm"]

# Load the audio
audio = whisper.load_audio("temp_audio.wav")

# Load the model
model = whisper.load_model("tiny", device="cpu")

# Transcribe the audio
result = whisper.transcribe(model, audio, language="en", detect_disfluencies=True)

# Extract filler words
filler_words_by_minute = extract_filler_words(result, additional_filler_words)

# Print the filler words by minute
for minute, filler_words in filler_words_by_minute.items():
    print(f"Minute {minute}: {filler_words}")
