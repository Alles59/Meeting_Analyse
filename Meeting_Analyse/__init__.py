from otree.api import *
import threading
import os
import json
from django.http import JsonResponse, HttpResponse
from django.views.decorators.csrf import csrf_exempt
from django.core.files.storage import FileSystemStorage
from django.conf import settings

doc = """
Your app description
"""

class C(BaseConstants):
    NAME_IN_URL = 'Meeting_Analyse'
    PLAYERS_PER_GROUP = None
    NUM_ROUNDS = 1

class Subsession(BaseSubsession):
    pass

class Group(BaseGroup):
    pass

class Player(BasePlayer):
    analyse_audio = models.BooleanField(choices=[
        [False, 'off'],
        [True, 'on'],
    ])
    video_path = models.StringField()

def extract_audio(video_path):
    abs_video_path = os.path.abspath(video_path)
    os.system(f'python extract_audio.py "{abs_video_path}"')

def analyze_audio(wav_path):
    abs_wav_path = os.path.abspath(wav_path)
    os.system(f'python Echtzeit-Videoaudio.py "{abs_wav_path}"')

@csrf_exempt
def upload_video(request):
    if request.method == 'POST':
        video_file = request.FILES['videoFile']
        fs = FileSystemStorage(location=os.path.join(settings.BASE_DIR, 'static', 'videos'))
        video_path = fs.save(video_file.name, video_file)
        video_url = fs.url(video_path)
        
        # Start the audio extraction and analysis after the video is uploaded
        threading.Thread(target=extract_audio, args=(os.path.join(settings.BASE_DIR, 'static', 'videos', video_path),)).start()
        wav_path = os.path.splitext(video_path)[0] + ".wav"
        threading.Thread(target=analyze_audio, args=(os.path.join(settings.BASE_DIR, 'static', 'videos', wav_path),)).start()
        
        return JsonResponse({'video_path': video_url})
    return HttpResponse(status=400)

def fetch_audio_analysis(request):
    current_time = int(request.GET.get('time', 0))
    analysis_file_path = 'Meeting_Analyse/audio_analysis.json'
    if os.path.exists(analysis_file_path):
        with open(analysis_file_path, 'r') as file:
            data = json.load(file)
            # Assuming data is structured to contain timestamps
            result = data.get(str(current_time), {
                "mean_pitch": 0,
                "std_pitch": 0,
                "hnr": 0,
                "zcr": 0,
            })
    else:
        result = {
            "mean_pitch": 0,
            "std_pitch": 0,
            "hnr": 0,
            "zcr": 0,
        }
    return JsonResponse(result)

class MyPage(Page):
    form_model = 'player'
    form_fields = ['analyse_audio', 'video_path']

    @staticmethod
    def before_next_page(player: Player, timeout_happened):
        if player.analyse_audio:
            threading.Thread(target=extract_audio, args=(player.video_path,)).start()

class Results(Page):
    @staticmethod
    def vars_for_template(player: Player):
        # Ensure that the video path is correctly formatted
        return {
            "video_path": f"/static/videos/{os.path.basename(player.video_path)}"
        }

page_sequence = [MyPage, Results]

# URL routing for upload and fetch functions
def custom_urls():
    from django.urls import path

    urlpatterns = [
        path('upload_video', upload_video, name='upload_video'),
        path('fetch_audio_analysis', fetch_audio_analysis, name='fetch_audio_analysis'),
    ]
    return urlpatterns

urlpatterns = custom_urls()
