import parselmouth
from parselmouth.praat import call
import json

def analyze_audio_segment(sound, start_time, end_time):
    segment = sound.extract_part(from_time=start_time, to_time=end_time, preserve_times=True)
    
    pitch = call(segment, "To Pitch", 0.0, 75, 500)
    pulses = call([segment, pitch], "To PointProcess (cc)")
    voice_report = call([segment, pitch, pulses], "Voice report", 0.0, 0.0, 75, 500, 1.3, 1.6, 0.03, 0.45)
    
    return voice_report

def parse_voice_report(report):
    lines = report.split('\n')
    parsed_report = {
        "Pitch": {},
        "Pulses": {},
        "Voicing": {},
        "Jitter": {},
        "Shimmer": {},
        "Harmonicity": {}
    }
    current_section = None
    
    for line in lines:
        if line.startswith("Pitch:"):
            current_section = "Pitch"
        elif line.startswith("Pulses:"):
            current_section = "Pulses"
        elif line.startswith("Voicing:"):
            current_section = "Voicing"
        elif line.startswith("Jitter:"):
            current_section = "Jitter"
        elif line.startswith("Shimmer:"):
            current_section = "Shimmer"
        elif line.startswith("Harmonicity of the voiced parts only:"):
            current_section = "Harmonicity"
        elif current_section and line.strip():
            key, value = line.split(':', 1)
            parsed_report[current_section][key.strip()] = value.strip()
    
    return parsed_report

def analyze_audio_in_intervals(file_path, interval_duration=5):
    sound = parselmouth.Sound(file_path)
    total_duration = sound.get_total_duration()
    all_reports = []

    for start_time in range(0, int(total_duration), interval_duration):
        end_time = min(start_time + interval_duration, total_duration)
        report = analyze_audio_segment(sound, start_time, end_time)
        parsed_report = parse_voice_report(report)
        interval_report = {
            "start_time": start_time,
            "end_time": end_time,
            "report": parsed_report
        }
        all_reports.append(interval_report)

    return all_reports

def save_reports_to_json(reports, output_file):
    with open(output_file, 'w') as f:
        json.dump(reports, f, indent=4)

# Example usage
file_path = "C:/Users/simon/.vscode/otree/Meeting_Analyse/temp_audio.wav"  # Update with the correct path to your file
output_file = "Test/voice_report.json"
reports = analyze_audio_in_intervals(file_path, interval_duration=5)
save_reports_to_json(reports, output_file)
print(f"Voice reports saved to {output_file}")
