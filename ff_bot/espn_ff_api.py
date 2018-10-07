import os
import requests
import time
import ff_bot.utils as utils
from espnff import League
from operator import itemgetter

LEAGUE_ID = os.environ["LEAGUE_ID"]
LEAGUE_YEAR = os.environ["LEAGUE_YEAR"]


# gets the provided weeks matchups
def get_scoreboard(week, year):
    league = League(LEAGUE_ID, year)
    return league.scoreboard(week)


# get final week of the regular season for provided year
def get_final_week(year):
    league = League(LEAGUE_ID, year)
    return league.settings.reg_season_count


# gets scores this year in order of points
def get_scores(total, descending):
    scores = []

    final_week = get_current_week()
    if descending:
        final_week = final_week + 1

    for w in range(1, final_week):
        for s in get_scoreboard(w, LEAGUE_YEAR):
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

    # sort list by points, and return [total] scores
    sorted_scores = sorted(scores, key=itemgetter('score'), reverse=descending)
    return sorted_scores[:int(total)]


# a juju describes a week in which a fantasy football team:
#   1) has a bottom-five score for the week
#   2) is below the average score for that week
#   3) wins
def get_jujus():
    jujus = []

    for w in range(1, get_current_week()):
        scores = []
        winners = []
        total_points = 0
        for s in get_scoreboard(w, LEAGUE_YEAR):
            if s.home_score < s.away_score:
                winners.append({
                    "team": s.away_team.team_name,
                    "score": s.away_score,
                    "vs_team": s.home_team.team_name,
                    "vs_score": s.home_score,
                    "week": w
                })
            else:
                winners.append({
                    "team": s.home_team.team_name,
                    "score": s.home_score,
                    "vs_team": s.away_team.team_name,
                    "vs_score": s.away_score,
                    "week": w
                })
            scores.append(s.home_score)
            scores.append(s.away_score)
            total_points += (s.home_score + s.away_score)
        avg = total_points/len(scores)
        bottom_scores = sorted(scores, reverse=True)[:5]

        for winner in winners:
            if winner["score"] < avg and winner["score"] <= bottom_scores[0]:
                jujus.append(winner)

    return jujus


# a salty describes a week in which a fantasy football team:
#   1) has a top-five score for the week
#   2) is above the average score for the week
#   3) loses
def get_salties():
    salties = []

    for w in range(1, get_current_week()):
        scores = []
        losers = []
        total_points = 0
        for s in get_scoreboard(w, LEAGUE_YEAR):
            if s.home_score > s.away_score:
                losers.append({
                    "team": s.away_team.team_name,
                    "score": s.away_score,
                    "vs_team": s.home_team.team_name,
                    "vs_score": s.home_score,
                    "week": w
                })
            else:
                losers.append({
                    "team": s.home_team.team_name,
                    "score": s.home_score,
                    "vs_team": s.away_team.team_name,
                    "vs_score": s.away_score,
                    "week": w
                })
            scores.append(s.home_score)
            scores.append(s.away_score)
            total_points += (s.home_score + s.away_score)
        avg = total_points/len(scores)
        top_scores = sorted(scores, reverse=False)[:5]

        for loser in losers:
            if loser["score"] > avg and loser["score"] >= top_scores[0]:
                salties.append(loser)

    return salties


# get top scores of all time
def get_top_scores_ever(total):
    scores = []

    # TODO: replace 2012 with calculated first league year
    for y in range(int(LEAGUE_YEAR), 2012, -1):
        utils.out(str(y))
        for w in range(1, get_final_week(y) + 1):
            for s in get_scoreboard(w, y):
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


# gets top scoring players in the current year
def get_top_players_year(total, position):
    players = []
    if position is not None and str(position).upper() not in ["QB", "WR", "RB", "TE", "K", "D", "FLEX"]:
        return []

    for w in range(1, get_current_week() + 1):
        players.extend(get_top_players(total, position, w))
    sorted_players = sorted(players, key=itemgetter('points'), reverse=True)
    return sorted_players[:int(total)]


# gets top scoring players in the provided week
def get_top_players(total, position, week):
    players = []
    if position is not None and str(position).upper() not in ["QB", "WR", "RB", "TE", "K", "D", "FLEX"]:
        return []

    for m in get_scoreboard(week, LEAGUE_YEAR):
        team_id = m.home_team.team_id
        r = requests.get("http://games.espn.com/ffl/api/v2/boxscore",
                         params={"leagueId": LEAGUE_ID, "seasonId": LEAGUE_YEAR, "matchupPeriodId": week, "teamId": team_id})

        team0 = r.json()["boxscore"]["teams"][0]
        team1 = r.json()["boxscore"]["teams"][1]

        # add players from team0 to players list
        for slot in team0["slots"]:
            if "player" in slot:
                name = slot["player"]["firstName"] + " " + slot["player"]["lastName"]
                pos = get_position(slot["player"]["defaultPositionId"])
                team_name = team0["team"]["teamAbbrev"]
                started = not slot["slotCategoryId"] == 20
                if "appliedStatTotal" in slot["currentPeriodRealStats"]:
                    points = slot["currentPeriodRealStats"]["appliedStatTotal"]
                else:
                    points = 0

                if(position is None or str(position).upper().__eq__(pos) or
                        (str(position).upper().__eq__("FLEX") and
                         str(pos).upper() in ["WR", "RB", "TE"])):
                    player_obj = {
                        "name": name,
                        "position": pos,
                        "points": points,
                        "team": team_name,
                        "started": started,
                        "week": week
                    }
                    players.append(player_obj)

        # add players from team1 to players list
        for slot in team1["slots"]:
            if "player" in slot:
                name = slot["player"]["firstName"] + " " + slot["player"]["lastName"]
                pos = get_position(slot["player"]["defaultPositionId"])
                team_name = team1["team"]["teamAbbrev"]
                started = not slot["slotCategoryId"] == 20
                if "appliedStatTotal" in slot["currentPeriodRealStats"]:
                    points = slot["currentPeriodRealStats"]["appliedStatTotal"]
                else:
                    points = 0

                if(position is None or str(position).upper().__eq__(pos) or
                        (str(position).upper().__eq__("FLEX") and
                         str(pos).upper() in ["WR", "RB", "TE"])):
                    player_obj = {
                        "name": name,
                        "position": pos,
                        "points": points,
                        "team": team_name,
                        "started": started,
                        "week": week
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


# get the current week
def get_current_week():
    r = requests.get("http://games.espn.com/ffl/api/v2/scoreboard",
                     params={"leagueId": LEAGUE_ID, "seasonId": LEAGUE_YEAR})
    return r.json()["scoreboard"]["matchupPeriodId"]
