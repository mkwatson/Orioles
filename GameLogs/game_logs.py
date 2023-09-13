from functools import reduce
from typing import List, Dict

import pyperclip
import requests

API_BASE = "https://statsapi.mlb.com/api/v1"
SEASON = '2023'
TEAM_ID = {
    'Orioles': 110,
    'Twins': 142,
    'Rays': 139
}


def fetch_json(url: str, params: Dict) -> Dict:
    return requests.get(url, params=params).json()


def get_player_ids_params(team_id) -> Dict:
    return {
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
        'teamId': team_id
    }


def get_player_game_hit_log_params(player_id: str) -> Dict:
    return {
        'stats': 'gameLog',
        'leagueListId': 'mlb_hist',
        'group': 'hitting',
        'gameType': 'R',
        'sitCodes': '1,2,3,4,5,6,7,8,9,10,11,12',
        'hydrate': 'team',
        'season': SEASON,
        'language': 'en'
    }


def get_player_ids(team_name) -> List[Dict]:
    url = 'https://bdfed.stitch.mlbinfra.com/bdfed/stats/player'
    team_id = TEAM_ID[team_name]
    return [{k: player[k] for k in ['playerId', 'playerName']}
            for player in fetch_json(url, get_player_ids_params(team_id))['stats']]


def get_player_game_hit_log(player_id: str) -> List[Dict]:
    url = f"{API_BASE}/people/{player_id}/stats"
    return [{k: game['stat'][k] for k in ['hits']} | {'date': game['date']}
            for game in fetch_json(url, get_player_game_hit_log_params(player_id))['stats'][0]['splits']]


def get_weighted_player_percentage_hit_games(game_log: List[Dict[str, int]]) -> float:
    decay_factor = 0.95

    def reducer(acc, game):
        _weighted_sum, _normalizing_sum, current_weight = acc
        hits = game['hits']
        new_weighted_sum = _weighted_sum + (hits > 0) * current_weight
        new_normalizing_sum = _normalizing_sum + current_weight
        new_current_weight = current_weight * decay_factor
        return new_weighted_sum, new_normalizing_sum, new_current_weight

    weighted_sum, normalizing_sum, _ = reduce(lambda acc, game: reducer(acc, game), reversed(game_log),
                                              (0, 0, 1))
    return weighted_sum / normalizing_sum if normalizing_sum else 0


def get_player_percentage_hit_games(player_id: str) -> Dict[str, int]:
    game_hit_log = get_player_game_hit_log(player_id)
    games_played = len(game_hit_log)
    games_with_a_hit = sum(game['hits'] > 0 for game in game_hit_log)
    return {
        'percent_games_with_hit': games_with_a_hit / games_played,
        'weighted_percent_games_with_hit': get_weighted_player_percentage_hit_games(game_hit_log)
    }


def print_markdown_table(player_data):
    print("| Player Name | Percent Games with Hit | Weighted Percent Games with Hit |")
    print("| ----------- | ---------------------- | ------------------------------- |")

    for player in player_data:
        print(
            f"| {player['player']} | {player['percent_games_with_hit']:.2f} | {player['weighted_percent_games_with_hit']:.2f} |")


def copy_table_to_clipboard(player_data):
    # Extract headers
    headers = player_data[0].keys()
    header_str = '\t'.join(headers)

    # Extract values for each dictionary and convert to a tab-delimited string
    rows = ['\t'.join(map(str, d.values())) for d in player_data]

    # Combine headers and rows
    table_str = '\n'.join([header_str] + rows)

    # Copy to clipboard
    pyperclip.copy(table_str)

    print("[INFO] Copied table to clipboard")


def main():
    team_name = 'Rays'
    players = get_player_ids(team_name)
    players_game_hit_percent = [
        {'player': player['playerName'], **get_player_percentage_hit_games(player['playerId'])}
        for player in players
    ]

    sorted_player_data = sorted(players_game_hit_percent, key=lambda x: x['weighted_percent_games_with_hit'],
                                reverse=True)

    # print_markdown_table(sorted_player_data)
    copy_table_to_clipboard(sorted_player_data)


if __name__ == "__main__":
    main()
