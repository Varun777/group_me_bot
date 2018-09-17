import time
import os

BOT_NAME = os.environ["BOT_NAME"]


# helper function to get current time as HH:MM:SS UTC
def get_time():
    return time.strftime("%T %Z", time.localtime(time.time()))


# immediately prints text to console with prefix [TIME][BOT_NAME].
def out(text):
    print("[" + get_time() + "][" + str.upper(BOT_NAME) + "] " + text, flush=True)
