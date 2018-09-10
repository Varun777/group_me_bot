from espnff import League
import os
import requests
from operator import itemgetter

LEAGUE_ID = os.environ["LEAGUE_ID"]
LEAGUE_YEAR = os.environ["LEAGUE_YEAR"]
league = League(LEAGUE_ID, LEAGUE_YEAR)


# gets the provided weeks matchups
def get_scores(week):
    return league.scoreboard(week)


# gets top scoring players in the provided week
def get_top_players(total, week):
    players = []

    if total > 20:
        total = 20

    for m in get_scores(week):
        team_id = m.home_team.team_id
        r = requests.get("http://games.espn.com/ffl/api/v2/boxscore",
                         params={"leagueId": LEAGUE_ID, "seasonId": LEAGUE_YEAR, "matchupPeriodId": week, "teamId": team_id})

        team0 = r.json()["boxscore"]["teams"][0]
        team1 = r.json()["boxscore"]["teams"][1]

        # add players from team0 to players list
        for slot in team0["slots"]:
            name = slot["player"]["firstName"] + " " + slot["player"]["lastName"]
            position = get_position(slot["player"]["defaultPositionId"])
            if "appliedStatTotal" in slot["currentPeriodRealStats"]:
                points = slot["currentPeriodRealStats"]["appliedStatTotal"]
            else:
                points = 0
            team_name = team0["team"]["teamAbbrev"]

            player_obj = {
                "name": name,
                "position": position,
                "points": points,
                "team": team_name
            }
            players.append(player_obj)

        # add players from team1 to players list
        for slot in team1["slots"]:
            name = slot["player"]["firstName"] + " " + slot["player"]["lastName"]
            position = get_position(slot["player"]["defaultPositionId"])
            if "appliedStatTotal" in slot["currentPeriodRealStats"]:
                points = slot["currentPeriodRealStats"]["appliedStatTotal"]
            else:
                points = 0
            team_name = team1["team"]["teamAbbrev"]

            player_obj = {
                "name": name,
                "position": position,
                "points": points,
                "team": team_name
            }
            players.append(player_obj)

    # sort list by points, and return top [total] players
    sorted_players = sorted(players, key=itemgetter('points'), reverse=True)
    return sorted_players[:int(total)]


# converts positionId to String
def get_position(position_id):
    if position_id == 1:
        return "QB"
    elif position_id == 2:
        return "RB"
    elif position_id == 3:
        return "WR"
    elif position_id == 4:
        return "TE"
    elif position_id == 16:
        return "K"
    else:
        return "N/A"
