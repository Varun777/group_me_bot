import os
from datetime import datetime
from pytz import timezone
import pytz

BOT_NAME = os.environ["BOT_NAME"]


# helper function to get current time as HH:MM:SS UTC
def get_time():
    local_time = datetime.now(tz=pytz.utc).astimezone(timezone('US/Pacific'))
    return local_time.strftime("%T")


# immediately prints text to console with prefix [TIME][BOT_NAME].
def out(text):
    print("[" + get_time() + "][" + str.upper(BOT_NAME) + "] " + text, flush=True)
