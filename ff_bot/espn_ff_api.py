from espnff import League
import os

LEAGUE_ID = os.environ["LEAGUE_ID"]
LEAGUE_YEAR = os.environ["LEAGUE_YEAR"]
league = League(LEAGUE_ID, LEAGUE_YEAR)


def test():
    # gets current week's Matchups
    return league.league_id
