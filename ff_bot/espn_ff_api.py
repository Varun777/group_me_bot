import os
import requests
import time
from espnff import League
from operator import itemgetter

LEAGUE_ID = os.environ["LEAGUE_ID"]
LEAGUE_YEAR = os.environ["LEAGUE_YEAR"]


# gets the provided weeks matchups
def get_scores(week, year):
    league = League(LEAGUE_ID, year)
    return league.scoreboard(week)


# get final week of the regular season for provided year
def get_final_week(year):
    league = League(LEAGUE_ID, year)
    return league.settings.reg_season_count


# gets top scores this year
def get_top_scores(total):
    scores = []
    total = min(total, 25)

    current_week = get_current_week()
    for w in range(1, current_week):
        for s in get_scores(w, LEAGUE_YEAR):
            score_obj0 = {
                "team": s.home_team.team_name,
                "score": s.home_score,
                "week": w,
                "win": s.home_score > s.away_score
            }
            score_obj1 = {
                "team": s.away_team.team_name,
                "score": s.away_score,
                "week": w,
                "win": s.away_score > s.home_score
            }

            scores.append(score_obj0)
            scores.append(score_obj1)

    # sort list by points, and return top [total] scores
    sorted_scores = sorted(scores, key=itemgetter('score'), reverse=True)
    return sorted_scores[:int(total)]


# get top scores of all time
def get_top_scores_ever(total):
    scores = []
    total = min(total, 25)

    # TODO: replace 2012 with calculated first league year
    for y in range(int(LEAGUE_YEAR), 2012, -1):
        for w in range(1, get_final_week(y)+1):
            for s in get_scores(w, y):
                score_obj0 = {
                    "owner": s.home_team.owner,
                    "score": s.home_score,
                    "week": w,
                    "year": y
                }
            score_obj1 = {
                "owner": s.away_team.owner,
                "score": s.away_score,
                "week": w,
                "year": y
            }

            scores.append(score_obj0)
            scores.append(score_obj1)

    # sort list by points, and return top [total] scores
    sorted_scores = sorted(scores, key=itemgetter('score'), reverse=True)
    return sorted_scores[:int(total)]


# gets top scoring players in the provided week
def get_top_players(total, week):
    players = []
    total = min(total, 25)

    for m in get_scores(week, LEAGUE_YEAR):
        team_id = m.home_team.team_id
        r = requests.get("http://games.espn.com/ffl/api/v2/boxscore",
                         params={"leagueId": LEAGUE_ID, "seasonId": LEAGUE_YEAR, "matchupPeriodId": week, "teamId": team_id})

        team0 = r.json()["boxscore"]["teams"][0]
        team1 = r.json()["boxscore"]["teams"][1]

        # add players from team0 to players list
        for slot in team0["slots"]:
            if "player" in slot:
                name = slot["player"]["firstName"] + " " + slot["player"]["lastName"]
                position = get_position(slot["player"]["defaultPositionId"])
                team_name = team0["team"]["teamAbbrev"]
                started = not slot["slotCategoryId"] == 20
                if "appliedStatTotal" in slot["currentPeriodRealStats"]:
                    points = slot["currentPeriodRealStats"]["appliedStatTotal"]
                else:
                    points = 0

                player_obj = {
                    "name": name,
                    "position": position,
                    "points": points,
                    "team": team_name,
                    "started": started
                }
                players.append(player_obj)

        # add players from team1 to players list
        for slot in team1["slots"]:
            if "player" in slot:
                name = slot["player"]["firstName"] + " " + slot["player"]["lastName"]
                position = get_position(slot["player"]["defaultPositionId"])
                team_name = team1["team"]["teamAbbrev"]
                started = not slot["slotCategoryId"] == 20
                if "appliedStatTotal" in slot["currentPeriodRealStats"]:
                    points = slot["currentPeriodRealStats"]["appliedStatTotal"]
                else:
                    points = 0

                player_obj = {
                    "name": name,
                    "position": position,
                    "points": points,
                    "team": team_name,
                    "started": started
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
    elif position_id == 5:
        return "K"
    elif position_id == 16:
        return "D"
    else:
        return "N/A"


# gets name of the team with the provided team id
def get_team(team_id):
    r = requests.get("http://games.espn.com/ffl/api/v2/teams",
                     params={"leagueId": LEAGUE_ID, "seasonId": LEAGUE_YEAR})
    teams = r.json()["teams"]
    for t in teams:
        if t["teamId"] == team_id:
            return {
                "name": t["teamLocation"] + " " + t["teamNickname"],
                "abbrev": t["teamAbbrev"],
                "id": team_id
            }

    return None


# gets the most recent transaction with transactionLogItemtypeId equal to tran_id
#
# tranType = 1: Moved
# tranType = 2: Added
# tranType = 3: Dropped
# tranType = 4: Traded
# tranType = 5: Drafted
# tranType = 11: Trade Accepted?
def get_latest_trade_time():
    r = requests.get("http://games.espn.com/ffl/api/v2/recentActivity",
                     params={"leagueId": LEAGUE_ID, "seasonId": LEAGUE_YEAR})
    transactions = r.json()["items"]
    for t in transactions:
        if "transactionLogItemTypeId" in t and t["transactionLogItemTypeId"] == 11:
            pattern = "%Y-%m-%dT%H:%M:%S.%fZ"
            epoch = int(time.mktime(time.strptime(t["date"], pattern)))
            return epoch
    return -1


def get_latest_trade():
    r = requests.get("http://games.espn.com/ffl/api/v2/recentActivity",
                     params={"leagueId": LEAGUE_ID, "seasonId": LEAGUE_YEAR})
    transactions = r.json()["items"]
    for t in transactions:
        if "transactionLogItemTypeId" in t and t["transactionLogItemTypeId"] == 11:
            players = []
            pending_items = t["pendingMoveItems"]
            for p in pending_items:
                r = requests.get("http://games.espn.com/ffl/api/v2/playerInfo",
                                 params={"playerId": p["playerId"]})

                player = r.json()["playerInfo"]["players"][0]["player"]
                name = player["firstName"] + " " + player["lastName"]
                position = get_position(player["defaultPositionId"])

                players.append({
                    "name": name,
                    "position": position,
                    "from": p["fromTeamId"],
                    "to": p["toTeamId"]
                })

            teams = []
            if t["teamsInvolved"] is not None:
                for team_id in t["teamsInvolved"]:
                    teams.append(get_team(team_id))

            pattern = "%Y-%m-%dT%H:%M:%S.%fZ"
            return {
                "teams": teams,
                "players": players,
                "time": int(time.mktime(time.strptime(t["date"], pattern)))
            }

    return None


# gets the most recent trades
#
# tranType = 1: Moved
# tranType = 2: Added
# tranType = 3: Dropped
# tranType = 4: Traded
# tranType = 5: Drafted
def get_latest_trades(limit):
    return None


# get the current week
def get_current_week():
    r = requests.get("http://games.espn.com/ffl/api/v2/scoreboard",
                     params={"leagueId": LEAGUE_ID, "seasonId": LEAGUE_YEAR})
    return r.json()["scoreboard"]["matchupPeriodId"]
