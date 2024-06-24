import moviepy.editor as mp
import sys
import os

def extract_audio_from_video(video_path):
    # Überprüfen, ob die Datei existiert
    if not os.path.isfile(video_path):
        print(f"Die Datei {video_path} existiert nicht.")
        return

    # Video laden
    video = mp.VideoFileClip(video_path)

    # Audiodatei extrahieren
    audio = video.audio
    audio_output_path = os.path.splitext(video_path)[0] + ".wav"
    audio.write_audiofile(audio_output_path)

    print(f"Audio wurde erfolgreich extrahiert und gespeichert unter: {audio_output_path}")

if __name__ == "__main__":
    # Überprüfen, ob ein Dateipfad als Argument übergeben wurde
    if len(sys.argv) != 2:
        print("Verwendung: python extract_audio.py <path_to_video>")
        sys.exit(1)

    video_path = sys.argv[1]
    extract_audio_from_video(video_path)
