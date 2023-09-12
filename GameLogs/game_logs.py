import requests
from typing import List, Dict

API_BASE = "https://statsapi.mlb.com/api/v1"
SEASON = '2023'


def fetch_json(url: str, params: Dict) -> Dict:
    return requests.get(url, params=params).json()


def get_player_ids() -> List[Dict]:
    url = 'https://bdfed.stitch.mlbinfra.com/bdfed/stats/player'
    params = {
        'stitch_env': 'prod',
        'season': SEASON,
        'sportId': '1',
        'stats': 'season',
        'group': 'hitting',
        'gameType': 'R',
        'limit': '250',
        'offset': '0',
        'sortStat': 'gamesPlayed',
        'order': 'desc',
        'teamId': '110'
    }
    return [
        {k: player[k] for k in ['playerId', 'playerName']}
        for player in fetch_json(url, params)['stats']
    ]


def get_player_game_hit_log(player_id: str) -> List[Dict]:
    url = f"{API_BASE}/people/{player_id}/stats"
    params = {
        'stats': 'gameLog',
        'leagueListId': 'mlb_hist',
        'group': 'hitting',
        'gameType': 'R',
        'sitCodes': '1,2,3,4,5,6,7,8,9,10,11,12',
        'hydrate': 'team',
        'season': SEASON,
        'language': 'en'
    }
    return [
        {k: game['stat'][k] for k in ['hits']}
        for game in fetch_json(url, params)['stats'][0]['splits']
    ]


def get_player_percentage_hit_games(player_id: str) -> float:
    game_hit_log = get_player_game_hit_log(player_id)
    games_played = len(game_hit_log)
    games_with_a_hit = sum(game['hits'] > 0 for game in game_hit_log)
    return games_with_a_hit / games_played


if __name__ == "__main__":
    players = get_player_ids()
    players_game_hit_percent = [
        {
            'player': player['playerName'],
            'percent_games_with_hit': get_player_percentage_hit_games(player['playerId'])
        }
        for player in players
    ]

    print(f"{'Player':<20} | {'% Games with Hit':>15}")
    print('-' * 28)
    for stat in sorted(players_game_hit_percent, key=lambda x: x['percent_games_with_hit'], reverse=True):
        percent = round(stat['percent_games_with_hit'] * 100, 2)
        print(f"{stat['player']:<20} | {percent:>15.2f}")
