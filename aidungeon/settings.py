import os

WEB_HOST = os.getenv('WEB_HOST', 'localhost')
WEB_PORT = int(os.getenv('WEB_PORT', 8080))

AIDUNGEON_PATH = '/aidungeon'
