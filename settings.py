API_TOKEN = "BAD TOKEN"
REPAIR_CHAT_ID = 0

# for locally rewrite settings add it to settings_local.py
try:
    from settings_local import *
except ModuleNotFoundError as err:
    pass