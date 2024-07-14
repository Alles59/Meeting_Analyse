import os
import re
import json
from collections import defaultdict
from moviepy.editor import VideoFileClip
from pydub import AudioSegment
import whisper_timestamped as whisper
from textblob import TextBlob
import pandas as pd


def extract_audio(video_path):
    """
    Extrahiert die Audiospur aus einer Video- oder Audiodatei und konvertiert sie in das richtige Format.

    :param video_path: Pfad zur Video- oder Audiodatei.
    :return: Pfad zur verarbeiteten Audiodatei.
    """
    if not os.path.isfile(video_path):
        raise FileNotFoundError(f"The file {video_path} does not exist.")

    # Prüfen, ob die Datei ein Video oder Audio ist, basierend auf der Dateierweiterung
    if video_path.lower().endswith(('.mp4', '.mkv', '.mov', '.avi')):
        video_clip = VideoFileClip(video_path)
        audio_clip = video_clip.audio
        audio_path = "temp_audio.wav"
        audio_clip.write_audiofile(audio_path, codec='pcm_s16le')
    elif video_path.lower().endswith(('.mp3', '.wav')):
        audio_path = video_path
    else:
        raise ValueError(
            "Unsupported file format. Please provide a video (.mp4, .mkv, .mov, .avi) or audio (.mp3, .wav) file.")

    # Sicherstellen, dass das Audio im richtigen Format vorliegt (mono PCM)
    sound = AudioSegment.from_file(audio_path)
    sound = sound.set_channels(1).set_frame_rate(16000)
    temp_audio_path = "processed_audio.wav"
    sound.export(temp_audio_path, format="wav")

    return temp_audio_path


def transcribe_audio_with_disfluencies(audio_path):
    """
    Transkribiert die Audiodatei und erkennt Dysfluencies.

    :param audio_path: Pfad zur Audiodatei.
    :return: Segmente der Transkription und der vollständige Transkriptions-Text.
    """
    # Whisper-Modell laden
    model = whisper.load_model("tiny")

    # Audio mit Zeitstempeln transkribieren und Dysfluencies erkennen
    result = whisper.transcribe(model, audio_path, language="en", detect_disfluencies=True)
    segments = result["segments"]

    return segments, result["text"]


def extract_filler_words_and_disfluencies(segment, additional_filler_words):
    """
    Extrahiert Füllwörter und Dysfluencies aus einem Transkriptionssegment.

    :param segment: Ein Segment der Transkription.
    :param additional_filler_words: Zusätzliche Füllwörter, die erkannt werden sollen.
    :return: Liste der Füllwörter und Anzahl der Dysfluencies.
    """
    # Regulärer Ausdruck, um Wörter mit [*] zu erkennen
    filler_word_pattern = re.compile(r'\[\*\]')

    # Set zusätzlicher Füllwörter für exakte Übereinstimmung, Groß- und Kleinschreibung ignorieren
    additional_filler_words_set = set(word.lower() for word in additional_filler_words)

    filler_words = []
    disfluencies_count = 0
    word_list = [word_info['text'].lower() for word_info in segment['words']]

    # Einzelne Füllwörter und Dysfluencies zählen
    for i, word_info in enumerate(segment['words']):
        word_text = word_info['text'].lower()
        if word_text in additional_filler_words_set:
            filler_words.append(word_info['text'])
        if filler_word_pattern.search(word_text):
            disfluencies_count += 1

    # Mehrwort-Füllwörter zählen
    for i in range(len(word_list) - 1):
        two_word_phrase = ' '.join(word_list[i:i + 2])
        if two_word_phrase in additional_filler_words_set:
            filler_words.append(f'{segment["words"][i]["text"]} {segment["words"][i + 1]["text"]}')

    return filler_words, disfluencies_count


def calculate_duration(start, end):
    """
    Berechnet die Dauer in Sekunden zwischen Start- und Endzeit.

    :param start: Startzeit in Sekunden.
    :param end: Endzeit in Sekunden.
    :return: Dauer in Sekunden.
    """
    duration = float(end) - float(start)
    return duration


def calculate_wpm(duration, word_count):
    """
    Berechnet die Wörter pro Minute (WPM).

    :param duration: Dauer in Sekunden.
    :param word_count: Anzahl der Wörter.
    :return: Wörter pro Minute.
    """
    minutes = duration / 60
    return word_count / minutes if minutes > 0 else 0


def process_segments(segments, additional_filler_words):
    """
    Verarbeitet die Segmente der Transkription und berechnet verschiedene Metriken.

    :param segments: Liste der Transkriptionssegmente.
    :param additional_filler_words: Zusätzliche Füllwörter, die erkannt werden sollen.
    :return: DataFrame mit den berechneten Metriken.
    """
    durations = []
    texts = []
    wpms = []
    filler_counts = []
    ratios = []
    filler_per_minute = []
    polarities = []
    subjectivities = []
    filler_word_details_list = []
    dysfluencies_counts = []

    for segment in segments:
        start = segment['start']
        end = segment['end']
        text = segment['text']
        duration = calculate_duration(start, end)
        word_count = len(text.split())
        blob = TextBlob(text)
        subjectivity = blob.sentiment.subjectivity
        polarity = blob.sentiment.polarity
        wpm = calculate_wpm(duration, word_count)

        durations.append(duration)
        texts.append(text)
        wpms.append(wpm)
        polarities.append(polarity)
        subjectivities.append(subjectivity)

        filler_words, dysfluencies_count = extract_filler_words_and_disfluencies(segment, additional_filler_words)
        total_filler_words = len(filler_words)
        filler_word_details = ', '.join(f'{word}: {filler_words.count(word)}' for word in set(filler_words))

        total_filler_and_dysfluencies = total_filler_words + dysfluencies_count
        total_words = len(blob.words)
        ratio_filler = total_filler_and_dysfluencies / total_words if total_words > 0 else 0
        filler_per_min = total_filler_and_dysfluencies * (60 / duration) if duration > 0 else 0

        filler_counts.append(total_filler_and_dysfluencies)
        ratios.append(ratio_filler)
        filler_per_minute.append(filler_per_min)
        filler_word_details_list.append(filler_word_details)
        dysfluencies_counts.append(dysfluencies_count)

        print(f"Start: {start}, End: {end}, Duration: {duration:.3f} seconds, WPM: {wpm:.2f}, "
              f"Text: {text}, Polarity: {polarity:.2f}, Subjectivity: {subjectivity:.2f}, "
              f"Filler words: {total_filler_words}, Filler ratio: {ratio_filler:.2f}, "
              f"Filler per minute: {filler_per_min:.2f}, Dysfluencies: {dysfluencies_count}")

    # Ergebnisse in ein DataFrame umwandeln
    data = {
        'Duration (s)': durations,
        'Text': texts,
        'WPM': wpms,
        'Filler count': filler_counts,
        'Filler ratio': ratios,
        'Filler per minute': filler_per_minute,
        'Polarity': polarities,
        'Subjectivity': subjectivities,
        'Filler word details': filler_word_details_list,
        'Dysfluencies count': dysfluencies_counts
    }
    df = pd.DataFrame(data)

    # DataFrame in eine Excel-Datei speichern
    df.to_excel('output.xlsx', index=False)
    print("\nErgebnisse wurden in 'output.xlsx' gespeichert.")

    return df


def main(video_path):
    """
    Hauptfunktion, die die Audiodatei extrahiert, transkribiert und die Segmente verarbeitet.

    :param video_path: Pfad zur Video- oder Audiodatei.
    """
    audio_path = extract_audio(video_path)

    # Zusätzliche Füllwörter definieren
    additional_filler_words = ["um", "umm", "uum", "ah", "aah", "ahh", "uh", "uuh", "uhh", "er", "eer", "err", "so",
                               "soo", "okay", "sorry", "well", "but", "right", "and so", "you know", "i think", "ähm",
                               "äh", "öhm", "hmm"]

    segments, _ = transcribe_audio_with_disfluencies(audio_path)
    process_segments(segments, additional_filler_words)


if __name__ == "__main__":
    video_path = "video.mp4"  # Pfad zu Ihrer Video- oder Audiodatei
    main(video_path)
