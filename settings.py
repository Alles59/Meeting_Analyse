from os import environ

SESSION_CONFIGS = [
    dict(
        name='Meeting_Analyse',
        display_name="Meeting Analyse",
        num_demo_participants=1,
        app_sequence=['Meeting_Analyse'],
    ),
]

INSTALLED_APPS = ['otree', 'Meeting_Analyse']

SESSION_CONFIG_DEFAULTS = dict(
    real_world_currency_per_point=1.00, participation_fee=0.00, doc=""
)

PARTICIPANT_FIELDS = []
SESSION_FIELDS = []

LANGUAGE_CODE = 'en'
REAL_WORLD_CURRENCY_CODE = 'USD'
USE_POINTS = False

ADMIN_USERNAME = 'admin'
ADMIN_PASSWORD = environ.get('OTREE_ADMIN_PASSWORD')

DEMO_PAGE_INTRO_HTML = """ """

SECRET_KEY = '4295757790207'
