import requests


def get_player_ids():
    url = 'https://bdfed.stitch.mlbinfra.com/bdfed/stats/player'

    params = {
        'stitch_env': 'prod',
        'season': '2023',
        'sportId': '1',
        'stats': 'season',
        'group': 'hitting',
        'gameType': 'R',
        'limit': '250',
        'offset': '0',
        'sortStat': 'gamesPlayed',
        'order': 'desc',
        'teamId': '110'  # Orioles
    }

    response = requests.get(url, params=params)
    json = response.json()
    player_ids = [{k: player[k] for k in ['playerId', 'playerName']} for player in json['stats']]
    return player_ids


def get_player_game_hit_log(player_id):
    url = f'https://statsapi.mlb.com/api/v1/people/{player_id}/stats'

    params = {
        'stats': 'gameLog',
        'leagueListId': 'mlb_hist',
        'group': 'hitting',
        'gameType': 'R',
        'sitCodes': '1,2,3,4,5,6,7,8,9,10,11,12',
        'hydrate': 'team',
        'season': '2023',
        'language': 'en'
    }

    response = requests.get(url, params=params)
    json = response.json()
    game_hit_log = [{k: game['stat'][k] for k in ['hits']} for game in json['stats'][0]['splits']]
    return game_hit_log


def get_player_percentage_hit_games(player_id):
    game_hit_log = get_player_game_hit_log(player_id)
    games_played = len(game_hit_log)
    games_with_a_hit = len([game for game in game_hit_log if game['hits'] > 0])
    return games_with_a_hit / games_played


players = get_player_ids()
players_game_hit_percent = [
    {
        'player': player['playerName'],
        'percent_games_with_hit': get_player_percentage_hit_games(player['playerId'])
    }
    for player
    in players
]

print(f"{'Player':<20} | {'% Games with Hit':>15}")

# Print separator
print('-' * 28)

# Print table rows
for stat in sorted(players_game_hit_percent, key=lambda x: x['percent_games_with_hit'], reverse=True):
    percent = round(stat['percent_games_with_hit'] * 100, 2)
    print(f"{stat['player']:<20} | {percent:>15.2f}")
