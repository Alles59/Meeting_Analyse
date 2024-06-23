from otree.api import *
import threading
import json
import os
from django.http import JsonResponse, HttpResponse
from django.views.decorators.csrf import csrf_exempt
from django.core.files.storage import default_storage
from django.core.files.base import ContentFile

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

def start_audio_analysis(video_path):
    abs_video_path = os.path.abspath(video_path)
    os.environ['VIDEO_PATH'] = abs_video_path
    os.system(f'python Meeting_Analyse/Echtzeit.py')

@csrf_exempt
def upload_video(request):
    if request.method == 'POST':
        video_file = request.FILES['videoFile']
        video_path = default_storage.save(video_file.name, ContentFile(video_file.read()))
        
        # Start the audio analysis after the video is uploaded
        threading.Thread(target=start_audio_analysis, args=(video_path,)).start()
        
        return JsonResponse({'video_path': video_path})
    return HttpResponse(status=400)

def fetch_audio_analysis(request):
    if os.path.exists('Meeting_Analyse/audio_analysis.json'):
        with open('Meeting_Analyse/audio_analysis.json', 'r') as file:
            data = json.load(file)
    else:
        data = {
            "mean_pitch": 0,
            "std_pitch": 0,
            "hnr": 0,
            "zcr": 0,
            "mean_intensity_spl": 0,
        }
    return JsonResponse(data)

# PAGES

class MyPage(Page):
    form_model = "player"
    form_fields = ["analyse_audio"]

    @staticmethod
    def before_next_page(player: Player, timeout_happened):
        if player.analyse_audio:
            threading.Thread(target=start_audio_analysis, args=('video.mp4',)).start()

class Results(Page):
    @staticmethod
    def vars_for_template(player: Player):
        if os.path.exists('Meeting_Analyse/audio_analysis.json'):
            with open('Meeting_Analyse/audio_analysis.json', 'r') as file:
                result = json.load(file)
        else:
            result = {
                "mean_pitch": 0,
                "std_pitch": 0,
                "hnr": 0,
                "zcr": 0,
                "mean_intensity_spl": 0,
            }
        return {
            "result": result,
            "analyse_audio": player.analyse_audio
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
