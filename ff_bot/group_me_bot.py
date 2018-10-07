import requests
import json
import os
import random
import sys
import re
import threading
from apscheduler.schedulers.blocking import BlockingScheduler
import ff_bot.salter as salter
import ff_bot.utils as utils
import ff_bot.espn_ff_api as espn
import ff_bot.group_me_listener as group_listener

# environment vars
BOT_ID = os.environ["BOT_ID"]
BOT_NAME = os.environ["BOT_NAME"]
USER_ID = os.environ["USER_ID"]
GROUP_ID = os.environ["GROUP_ID"]
LATEST_TRADE_TIME = espn.get_latest_trade_time()


# Send message from bot to chat room
# Note: only images that are uploaded to groupme's image service will display
# See here: https://dev.groupme.com/docs/image_service
def send_message(text="", image_url=None):
    attachments = []
    if image_url is not None:
        attachments = [{
            "type": "image",
            "url": image_url
        }]

    template = {
        "bot_id": BOT_ID,
        "text": text,
        "attachments": attachments}
    headers = {'content-type': 'application/json'}
    requests.post("https://api.groupme.com/v3/bots/post", data=json.dumps(template), headers=headers)


# handle different response scenarios here.
# currently supports:
#    1) response = "@[BOT_NAME]", display greeting
#    2) response = "@[BOT_NAME] help", display list of commands
#    3) response = "@[BOT_NAME] show scores", display scores for current week
#    4) response = "@[BOT_NAME] show top [TOTAL] scores", display top [TOTAL] scores for current year
#    5) response = "@[BOT_NAME] show bottom [TOTAL] scores", display bottom [TOTAL] scores for current year
#    6) response = "@[BOT_NAME] show top [TOTAL] scores ever", display top [TOTAL] scores ever
#    7) response = "@[BOT_NAME] show top [TOTAL] players", display top [TOTAL] players for current week
#    8) response = "@[BOT_NAME] show top [TOTAL] players [YEAR]", display top [TOTAL] players for year
#    9) response = "@[BOT_NAME] salt [USER]", display random insult to [USER]
#    10) response = "@[BOT_NAME] die", kill program
#    11) response contains "wonder", display arrested development reference
#
# future support:
#    1) ?
def handle_response(user_from, group_id, text):
    # get the text from response. if exception, simply return
    try:
        at_bot = "@" + BOT_NAME

        # ignore response if it comes from the bot, or from a different group
        if str.lower(user_from).__eq__(str.lower(BOT_NAME)) or group_id != GROUP_ID:
            return
        if text == at_bot:
            handle_bot_name()
        elif text == at_bot + " help":
            handle_bot_help()
        elif text == at_bot + " show scores":
            handle_bot_scores()
        elif str.startswith(text, at_bot + " salt "):
            handle_bot_salt(user_from, str.split(text, "salt ", 1)[1])
        elif text == at_bot + " die":
            kill_bot()
        elif re.match(r'^' + at_bot + ' show top \d+ players$', text):
            total = re.search(r'\d+', text).group()
            handle_bot_top_players_week(total)
        elif re.match(r'^' + at_bot + ' show top \d+ players \d+$', text):
            total = re.findall(r'\d+', text)[0]
            year = re.findall(r'\d+', text)[1]
            handle_bot_top_players_year(total, year)
        elif re.match(r'^' + at_bot + ' show top \d+ scores$', text):
            total = re.search(r'\d+', text).group()
            handle_bot_top_scores(total)
        elif re.match(r'^' + at_bot + ' show bottom \d+ scores$', text):
            total = re.search(r'\d+', text).group()
            handle_bot_bottom_scores(total)
        # elif re.match(r'^' + at_bot + ' show top \d+ scores ever$', text):
        #     total = re.search(r'\d+', text).group()
        #     handle_bot_top_scores_ever(total)
        elif re.match(r'^' + at_bot + ' show jujus$', text):
            handle_bot_jujus()
        elif re.match(r'^' + at_bot + ' show salties$', text):
            handle_bot_salties()
        elif str.__contains__(str.lower(text), "wonder"):
            handle_bot_wonder()
        elif str.__contains__(str.lower(text), "same"):
            handle_bot_same()
    except Exception as ex:
        utils.out("Exception in handle_response: " + ex.__repr__())
        return


# handle when response = "@[BOT_NAME]"
# display greeting
def handle_bot_name():
    send_message("you rang? type \"@" + BOT_NAME + " help\" to see what i can do.")


# handle when response = "@[BOT_NAME] help"
# display command list
def handle_bot_help():
    send_message("commands:\n" +
                 "@" + BOT_NAME + " help -- show list of commands\n" +
                 "@" + BOT_NAME + " show scores -- show this weeks scores\n"
                 "@" + BOT_NAME + " show top [TOTAL] scores -- show this years top scores\n"
                 "@" + BOT_NAME + " show bottom [TOTAL] scores -- show this years bottom scores\n"
                 "@" + BOT_NAME + " show jujus -- show this years jujus\n"
                 "@" + BOT_NAME + " show salties -- show this years salties\n"
                 "@" + BOT_NAME + " show top [TOTAL] players -- show this weeks top players\n"
                 "@" + BOT_NAME + " show top [TOTAL] players [YEAR] -- show the years top players\n"
                 "@" + BOT_NAME + " salt [USER] -- throw salt at [USER]\n")


# handle when response = "@[BOT_NAME] salt [USER]"
# display random salty comment towards user_to
def handle_bot_salt(user_from, user_to):
    if str.__contains__(str.lower(user_to), str.lower(BOT_NAME)):
        send_message("listen here you lil shit...")
        return

    number = random.randint(1, 100)
    # easter egg: do this 10% of the time..
    if number <= 10:
        send_message(user_from + " likes little boys.")
    # easter egg: do this 20% of the time..
    elif 10 < number <= 20:
        send_message("how dare you, " + user_from + ", she's a nice lady!")
    else:
        send_message(salter.throw_salt(user_to))


# handle when response contains "wonder"
# display arrested development reference
def handle_bot_wonder():
    send_message("did somebody say wonder?!")


# handle when response contains "same"
# display arrested development reference
def handle_bot_same():
    send_message("same")


# handle when response = "@[BOT_NAME] show scores"
# display scores for current week
def handle_bot_scores():
    matchups = espn.get_scoreboard(espn.get_current_week(), espn.LEAGUE_YEAR)
    scores = ""

    for m in matchups:
        if m.home_score >= m.away_score:
            first_team_name = m.home_team.team_name
            first_team_score = m.home_score
            second_team_name = m.away_team.team_name
            second_team_score = m.away_score
        else:
            first_team_name = m.away_team.team_name
            first_team_score = m.away_score
            second_team_name = m.home_team.team_name
            second_team_score = m.home_score

        scores += '%s (%.2f) - (%.2f) %s\n' % (first_team_name, first_team_score, second_team_score, second_team_name)

    send_message(scores)


# handle when response = "@[BOT_NAME] show jujus"
# display all of this years jujus
def handle_bot_jujus():
    jujus = espn.get_jujus()

    response = "This Year's JuJus:\n"
    for juju in jujus:
        response += "%s (%.2f-%.2f) - wk %d\n" % (juju["team"], juju["score"], juju["vs_score"], juju["week"])

    send_message(response)


# handle when response = "@[BOT_NAME] show salties"
# display all of this years salties
def handle_bot_salties():
    salties = espn.get_salties()

    response = "This Year's Salties:\n"
    for salty in salties:
        response += "%s (%.2f-%.2f) - wk %d\n" % (salty["team"], salty["score"], salty["vs_score"], salty["week"])

    send_message(response)


# handle when response = "@[BOT_NAME] show top [TOTAL] scores"
# display top [TOTAL] scores for the current season
def handle_bot_top_scores(total):
    total = min(int(total), 25)
    scores = espn.get_scores(total, True)

    response = "This Year's Top " + str(len(scores)) + " Scores:\n"
    for score in scores:
        response += "%.2f - %s (%d)" % (score["score"], score["team"], score["week"])
        if not score["win"]:
            response += " *"
        response += "\n"

    response += "(*) = lost"

    send_message(response)


# handle when response = "@[BOT_NAME] show bottom [TOTAL] scores"
# display bottom [TOTAL] scores for the current season
def handle_bot_bottom_scores(total):
    total = min(int(total), 25)
    scores = espn.get_scores(total, False)

    response = "This Year's Worst " + str(len(scores)) + " Scores:\n"
    for score in scores:
        response += "%.2f - %s (%d)" % (score["score"], score["team"], score["week"])
        if score["win"]:
            response += " *"
        response += "\n"

    response += "(*) = won"

    send_message(response)


# handle when response = "@[BOT_NAME] show top [TOTAL] scores ever"
# display top [TOTAL] players for the current season
def handle_bot_top_scores_ever(total):
    total = min(int(total), 25)
    scores = espn.get_top_scores_ever(total)

    response = "Top " + str(len(scores)) + " Scores OF ALL TIME:\n"
    for score in scores:
        response += "%.2f - %s - %d (%d)\n" % (score["score"], score["owner"], score["year"], score["week"])

    send_message(response)


# handle when response = "@[BOT_NAME] show top [TOTAL] players"
# display top [TOTAL] players for the current week
def handle_bot_top_players_week(total):
    total = min(int(total), 25)
    players = espn.get_top_players(total, espn.get_current_week())

    response = "This Week's Top " + str(len(players)) + " Rostered Players:\n"
    for player in players:
        response += "%.2f - %s (%s) - %s" % (player["points"], player["name"], player["position"], player["team"])
        if not player["started"]:
            response += " *"
        response += "\n"

    response += "(*) = bench player"

    send_message(response)


# handle when response = "@[BOT_NAME] show top [TOTAL] players [YEAR]"
# display top [TOTAL] players for the current week
def handle_bot_top_players_year(total, year):
    if int(year) != int(espn.LEAGUE_YEAR):
        send_message("i only support " + str(espn.LEAGUE_YEAR))
        return

    total = min(int(total), 25)
    players = espn.get_top_players_year(total)

    response = str(year) + "'s Top " + str(len(players)) + " Rostered Players:\n"
    for player in players:
        response += "%.2f - %s (%s) - %s (%d)" % \
                    (player["points"], player["name"], player["position"], player["team"], player["week"])
        if not player["started"]:
            response += " *"
        response += "\n"

    response += "(*) = bench player"

    send_message(response)


# called from scheduler
# checks if there has been a new trade since the last attempt
# handles scenario by sending bot message
def handle_trade_alert():
    utils.out("Handle trade alert.")
    global LATEST_TRADE_TIME
    latest_trade = espn.get_latest_trade()

    # if no trade has occurred, simply return
    if latest_trade is None:
        return

    if latest_trade["time"] > LATEST_TRADE_TIME:
        LATEST_TRADE_TIME = latest_trade["time"]

        team_0 = latest_trade["teams"][0]
        team_1 = latest_trade["teams"][1]
        players_0 = ""
        players_1 = ""

        for p in latest_trade["players"]:
            if p["from"] == team_1["id"]:
                players_0 += p["name"] + " " + "(" + p["position"] + ")\n"
            else:
                players_1 += p["name"] + " " + "(" + p["position"] + ")\n"

        send_message(image_url="https://i.groupme.com/500x281.jpeg.87bd736636764acf86e1bd131a6f9373")
        send_message(team_0["name"] + " and " + team_1["name"] + " have agreed on a trade, "
                     "multiple sauces tell " + str.lower(BOT_NAME) + ". Here are the details...\n\n" +
                     team_0["abbrev"] + " receives:\n" +
                     players_0 + "\n" +
                     team_1["abbrev"] + " receives:\n" +
                     players_1)


# kill program
def kill_bot():
    send_message("k bye.")
    sys.exit(0)


# initialize scheduler
def init_scheduler():
    # Monday evening alert showing the top 10 players from the previous week
    # Monday evening alert showing if any scores broke through the top 10 scores of the year
    # Tuesday/Wednesday morning alert showing which players were recently added from waivers
    # Thursday morning alert showing what players to watch in the Thursday night game
    scheduler = BlockingScheduler()
    # check for new trades
    scheduler.add_job(handle_trade_alert, 'interval', seconds=30)
    scheduler.start()


# main class
def bot_main():
    t1 = threading.Thread(target=init_scheduler, args=())
    t1.daemon = True
    t1.start()

    group_listener.init(handle_response)


if __name__ == '__main__':
    bot_main()
