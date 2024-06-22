from otree.api import *


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
    ]
)


# PAGES

class MyPage(Page):
    form_model = "player"
    form_fields = ["analyse_audio"]

class Results(Page):

    @staticmethod
    def vars_for_template(player: Player):
        result = player.analyse_audio
        return {
        "result": result
        }

page_sequence = [MyPage, Results]
