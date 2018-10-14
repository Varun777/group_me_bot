import os
import requests
import time
import ff_bot.utils as utils
from espnff import League
from operator import itemgetter

LEAGUE_ID = os.environ["LEAGUE_ID"]
LEAGUE_YEAR = os.environ["LEAGUE_YEAR"]
FIRST_LEAGUE_YEAR = os.environ["FIRST_LEAGUE_YEAR"]
LEAGUE = League(LEAGUE_ID, LEAGUE_YEAR)


# gets the provided weeks matchups during provided year
def get_scoreboard(week, year):
    league = League(LEAGUE_ID, year)
    return league.scoreboard(week)


# gets the provided weeks matchups during current year
def get_scoreboard_current_year(week):
    return LEAGUE.scoreboard(week)


# get most/least PointsFor through the provided week, in league history
def get_pf_through(total, week, descending):
    points = []
    week = min(max(0, week), 13)
    current_week = get_current_week()
    for y in range(int(LEAGUE_YEAR), int(FIRST_LEAGUE_YEAR)-1, -1):
        if descending or y < int(LEAGUE_YEAR) or week < current_week:
            s = get_team_data(y)
            for t in s:
                p = 0
                team_id = t["teamId"]
                for w in range(0, week):
                    if t["scheduleItems"][w]["matchups"][0]["homeTeamId"] == team_id:
                        p += t["scheduleItems"][w]["matchups"][0]["homeTeamScores"][0]
                    else:
                        p += t["scheduleItems"][w]["matchups"][0]["awayTeamScores"][0]
                points.append({
                    "points": p,
                    "owner": t["owners"][0]["firstName"] + " " + t["owners"][0]["lastName"],
                    "week": week,
                    "year": y
                })

    sorted_points = sorted(points, key=itemgetter('points'), reverse=descending)
    return sorted_points[:int(total)]


# get all-time standings
def get_standings_ever():
    standings = []
    team_dict = {}

    for y in range(int(LEAGUE_YEAR), int(FIRST_LEAGUE_YEAR)-1, -1):
        s = get_standings_data(y)
        for t in s:
            owner_id = t["owners"][0]["ownerId"]

            if owner_id in team_dict:
                team_dict[owner_id]["wins"] += t["record"]["overallWins"]
                team_dict[owner_id]["losses"] += t["record"]["overallLosses"]
                team_dict[owner_id]["ties"] += t["record"]["overallTies"]
            else:
                team_dict[owner_id] = {
                    "wins": t["record"]["overallWins"],
                    "losses": t["record"]["overallLosses"],
                    "ties": t["record"]["overallTies"],
                    "owner": t["owners"][0]["firstName"] + " " + t["owners"][0]["lastName"]
                }

    for t in team_dict:
        team_dict[t]["percentage"] = \
            float(team_dict[t]["wins"]/(team_dict[t]["losses"] + team_dict[t]["wins"] + team_dict[t]["ties"]))
        standings.append(team_dict[t])

    sorted_standings = sorted(standings, key=itemgetter('percentage'), reverse=True)
    return sorted_standings


# gets scores this year in order of points
def get_scores(total, descending):
    scores = []

    final_week = get_current_week()
    if descending:
        final_week = final_week + 1

    for w in range(1, final_week):
        for s in get_scoreboard_current_year(w):
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
        for s in get_scoreboard_current_year(w):
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
        for s in get_scoreboard_current_year(w):
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
def get_all_scores_ever(total, descending):
    scores = []

    for y in range(int(LEAGUE_YEAR), int(FIRST_LEAGUE_YEAR)-1, -1):
        if y == int(LEAGUE_YEAR):
            # descending (top scores), count current week
            if descending:
                final_week = get_current_week()
            # ascending (low scores), dont count current week
            else:
                final_week = get_current_week()-1
        else:
            final_week = 13

        teams = get_team_data(y)
        for t in teams:
            owner = t["owners"][0]["firstName"] + " " + t["owners"][0]["lastName"]
            team_id = t["teamId"]
            for s in t["scheduleItems"]:
                matchup = s["matchups"][0]

                if matchup["matchupTypeId"] == 0 and s["matchupPeriodId"] <= final_week:
                    if matchup["homeTeamId"] == team_id:
                        scores.append({
                            "owner": owner,
                            "score": matchup["homeTeamScores"][0],
                            "week": s["matchupPeriodId"],
                            "year": y
                        })
                    else:
                        scores.append({
                            "owner": owner,
                            "score": matchup["awayTeamScores"][0],
                            "week": s["matchupPeriodId"],
                            "year": y
                        })

    # sort list by points, and return top [total] scores
    sorted_scores = sorted(scores, key=itemgetter('score'), reverse=descending)
    return sorted_scores[:int(total)]


# gets top/bottom scoring rostered players ever
# def get_players_ever(total, position, descending):
#     players = []
#     if position is not None and str(position).upper() not in ["QB", "WR", "RB", "TE", "K", "D", "FLEX"]:
#         return []
#
#     for y in range(int(LEAGUE_YEAR), int(FIRST_LEAGUE_YEAR)-1, -1):
#         players.extend(get_players_year(total, position, y, descending))
#
#     sorted_players = sorted(players, key=itemgetter('points'), reverse=descending)
#     return sorted_players[:int(total)]


# gets top/bottom scoring players in the provided year
def get_players_year(total, position, year, descending):
    players = []
    if position is not None and str(position).upper() not in ["QB", "WR", "RB", "TE", "K", "D", "FLEX"]:
        return []

    if year == int(LEAGUE_YEAR):
        # descending (top scores), count current week
        if descending:
            final_week = get_current_week() + 1
        # ascending (low scores), dont count current week
        else:
            final_week = get_current_week()
    else:
        final_week = 14

    for w in range(1, final_week):
        players.extend(get_players_week(total, position, w, year, descending))

    sorted_players = sorted(players, key=itemgetter('points'), reverse=descending)
    return sorted_players[:int(total)]


# gets top/bottom scoring players in the provided week of the provided year
def get_players_week(total, position, week, year, descending):
    players = []
    if position is not None and str(position).upper() not in ["QB", "WR", "RB", "TE", "K", "D", "FLEX"]:
        return []

    for m in get_scoreboard_current_year(week):
        team_id = m.home_team.team_id
        b = get_boxscore_data(week, year, team_id)
        utils.out("getting players " + str(year) + " " + str(week) + " " + str(team_id))

        team0 = b["teams"][0]
        team1 = b["teams"][1]

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
    sorted_players = sorted(players, key=itemgetter('points'), reverse=descending)
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


# get boxscore data in json form for the provided week and year
# TODO: fix, this only works years where league was public
def get_boxscore_data(week, year, team_id):
    cookies = {
        'espn_s2': 'AEA4zGWW742Nu%2Bukdo3xanjijf5TxJkGbhoCjBLqoJopF6MC9rlfzkcR3jbQdabP6ADwwwZwEE7XIHkJ'
                   '8Tv0q1S7TNxcKHW0goamY4xhnvQGSFBsFXy9Y%2FMyHGr%2BeRrzCkza%2FtRNv60QjusWqHDUQpugB8lWr'
                   'canlDXl0zpDoXRBd2mEUQIab4dzUpwBZuImi%2FqoEerLkibucZ60okobcxL6jXtdBI%2BX%2BzSw%2BvDn'
                   'gwxbwDR6SKFiTgK7f1fy%2F%2B4nlf%2BddtFPlg02cVVdI8leQ7nL',
        'SWID': '{B703DBC7-66F7-45F2-9E1F-6C0F474E7BDD}'
    }

    r = requests.get("http://games.espn.com/ffl/api/v2/boxscore",
                     params={"leagueId": LEAGUE_ID, "seasonId": year, "matchupPeriodId": week, "teamId": team_id},
                     cookies=cookies)
    return r.json()["boxscore"]


# get scoreboard data in json form for the provided week and year
def get_scoreboard_data(week, year):
    cookies = {
        'espn_s2': 'AEA4zGWW742Nu%2Bukdo3xanjijf5TxJkGbhoCjBLqoJopF6MC9rlfzkcR3jbQdabP6ADwwwZwEE7XIHkJ'
                   '8Tv0q1S7TNxcKHW0goamY4xhnvQGSFBsFXy9Y%2FMyHGr%2BeRrzCkza%2FtRNv60QjusWqHDUQpugB8lWr'
                   'canlDXl0zpDoXRBd2mEUQIab4dzUpwBZuImi%2FqoEerLkibucZ60okobcxL6jXtdBI%2BX%2BzSw%2BvDn'
                   'gwxbwDR6SKFiTgK7f1fy%2F%2B4nlf%2BddtFPlg02cVVdI8leQ7nL',
        'SWID': '{B703DBC7-66F7-45F2-9E1F-6C0F474E7BDD}'
    }

    r = requests.get("http://games.espn.com/ffl/api/v2/scoreboard",
                     params={"leagueId": LEAGUE_ID, "seasonId": year, "matchupId": week},
                     cookies=cookies)
    return r.json()["scoreboard"]["matchups"]


# get standings data in json form for the provided year
def get_standings_data(year):
    cookies = {
        'espn_s2': 'AEA4zGWW742Nu%2Bukdo3xanjijf5TxJkGbhoCjBLqoJopF6MC9rlfzkcR3jbQdabP6ADwwwZwEE7XIHkJ'
                   '8Tv0q1S7TNxcKHW0goamY4xhnvQGSFBsFXy9Y%2FMyHGr%2BeRrzCkza%2FtRNv60QjusWqHDUQpugB8lWr'
                   'canlDXl0zpDoXRBd2mEUQIab4dzUpwBZuImi%2FqoEerLkibucZ60okobcxL6jXtdBI%2BX%2BzSw%2BvDn'
                   'gwxbwDR6SKFiTgK7f1fy%2F%2B4nlf%2BddtFPlg02cVVdI8leQ7nL',
        'SWID': '{B703DBC7-66F7-45F2-9E1F-6C0F474E7BDD}'
    }

    r = requests.get("http://games.espn.com/ffl/api/v2/standings",
                     params={"leagueId": LEAGUE_ID, "seasonId": year},
                     cookies=cookies)
    return r.json()["teams"]


# get team data in json form for the provided year
def get_team_data(year):
    cookies = {
        'espn_s2': 'AEA4zGWW742Nu%2Bukdo3xanjijf5TxJkGbhoCjBLqoJopF6MC9rlfzkcR3jbQdabP6ADwwwZwEE7XIHkJ'
                   '8Tv0q1S7TNxcKHW0goamY4xhnvQGSFBsFXy9Y%2FMyHGr%2BeRrzCkza%2FtRNv60QjusWqHDUQpugB8lWr'
                   'canlDXl0zpDoXRBd2mEUQIab4dzUpwBZuImi%2FqoEerLkibucZ60okobcxL6jXtdBI%2BX%2BzSw%2BvDn'
                   'gwxbwDR6SKFiTgK7f1fy%2F%2B4nlf%2BddtFPlg02cVVdI8leQ7nL',
        'SWID': '{B703DBC7-66F7-45F2-9E1F-6C0F474E7BDD}'
    }

    r = requests.get("http://games.espn.com/ffl/api/v2/teams",
                     params={"leagueId": LEAGUE_ID, "seasonId": year},
                     cookies=cookies)
    return r.json()["teams"]


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
