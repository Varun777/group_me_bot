from espnff import League
import os

LEAGUE_ID = os.environ["LEAGUE_ID"]
LEAGUE_YEAR = os.environ["LEAGUE_YEAR"]
league = League(LEAGUE_ID, LEAGUE_YEAR)


# gets current week's matchups
def get_current_scores():
    return league.scoreboard()
