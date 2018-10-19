import os
import requests
import random
import ff_bot.utils as utils

GIPHY_KEY = os.environ["GIPHY_KEY"]


# get the current week
def get_random_gif(search_term):
    final_search_term = str(search_term).replace(" ", "+")
    r = requests.get("https://api.giphy.com/v1/gifs/search",
                     params={"api_key": GIPHY_KEY, "q": final_search_term, "limit": 100, "offset": 0, "rating": "PG-13", "lang": "en"})
    data = r.json()["data"]

    if len(data) == 0:
        return "i couldnt find a gif for that.."

    index = random.randint(0, len(data)-1)
    return r.json()["data"][index]["images"]["fixed_height"]["url"]

