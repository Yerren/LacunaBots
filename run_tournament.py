"""
Runs a round-robin style tournament of Lacuna matches with bot players.
Each match consists of two games, one where each player goes first. A player needs to win both games to win the overall
match (if both players win one game each, the match is a draw).

NUM_MATCHES (int): The number of matches that each pairing of bots will play.
DRAW_GAME (bool): Whether to display the games as they are being played (disabling this speeds things up considerable).
MANUAL_CLICK_THROUGH (bool): Whether to wait for the user to press the left mouse button at each step of the game. This is ignored if DRAW_GAME is False.

Use left mouse button to progress through the game.
"""

from collections import defaultdict
from itertools import combinations
from game_resources import *
from bot_classes import *
from typing import Dict
import pandas as pd


NUM_MATCHES = 20
DRAW_GAME = False
MANUAL_CLICK_THROUGH = True


def run_game(game_manager: 'GameManager', player1: Player, player2: Player) -> Player:
    """
    Run a single game between two players and return the winner.

    Args:
        game_manager: The game manager object for the current game
        player1: First player
        player2: Second player

    Returns:
        Player object that won the game
    """

    game_manager.set_players([player1, player2])
    game_manager.reset_and_setup_game()

    result = {"game_status": 'in_progress'}
    while result["game_status"] == 'in_progress':
        result = game_manager.perform_game_step(wait_for_click=MANUAL_CLICK_THROUGH)

    return result["winner"]


def run_match(game_manager: 'GameManager', bot1_name: str, bot1_class: 'Bot', bot2_name: str, bot2_class: 'Bot') -> str:
    """
    Run a match (two games) between two bots and return the result.

    Args:
        game_manager: The game manager object for the current game
        bot1_name: Name of the first bot
        bot1_class: The first bot
        bot2_name: Name of the second bot
        bot2_class: The second bot

    Returns:
        String indicating match result: bot1_name, bot2_name, or "Draw"
    """
    player_colours = [(192, 192, 192), (255, 215, 0)]  # Silver and Gold
    player1 = game_manager.create_player(player_colours[0], bot1_name, PlayerType.AI, bot_class=bot1_class)
    player2 = game_manager.create_player(player_colours[1], bot2_name, PlayerType.AI, bot_class=bot2_class)

    # First game
    winner1 = run_game(game_manager, player1, player2)

    # Second game with swapped order
    winner2 = run_game(game_manager, player2, player1)

    # Because the player OBJECTS are returned as winner 1 and winner 2, it doesn't matter that the order of the players is swapped
    if winner1 == player1 and winner2 == player1:
        print(f"{bot1_name} vs {bot2_name}: {bot1_name} wins the match")
        return bot1_name  # Bot 1 wins the match
    elif winner1 == player2 and winner2 == player2:
        print(f"{bot1_name} vs {bot2_name}: {bot2_name} wins the match")
        return bot2_name  # Bot 2 wins the match
    else:
        print(f"{bot1_name} vs {bot2_name}: Draw")
        return "Draw"  # Match is a draw


def run_tournament(game_manager: 'GameManager', bots: Dict[str, Bot]) -> Dict[str, Dict[str, Dict[str, int]]]:
    """
    Run a tournament between all pairs of bots.

    Args:
        game_manager: The game manager object for the current game
        bots: Dictionary mapping bot names to their movement functions

    Returns:
        Nested dictionary containing win/loss/draw statistics for each bot pair
    """
    results = defaultdict(lambda: defaultdict(lambda: {"wins": 0, "losses": 0, "draws": 0}))

    for bot_1, bot_2 in combinations(bots.items(), 2):
        bot1_name, bot1_class = bot_1
        bot2_name, bot2_class = bot_2

        assert bot1_name != "Draw" and bot2_name != "Draw", "Bots cannot be named 'Draw'"

        for _ in range(NUM_MATCHES):
            match_result = run_match(game_manager, bot1_name, bot1_class, bot2_name, bot2_class)
            if match_result == bot1_name:
                results[bot1_name][bot2_name]["wins"] += 1
                results[bot2_name][bot1_name]["losses"] += 1
            elif match_result == bot2_name:
                results[bot1_name][bot2_name]["losses"] += 1
                results[bot2_name][bot1_name]["wins"] += 1
            else:
                results[bot1_name][bot2_name]["draws"] += 1
                results[bot2_name][bot1_name]["draws"] += 1

    return results


def display_results(results: Dict[str, Dict[str, Dict[str, int]]]) -> pd.DataFrame:
    """
    Display the tournament results in a formatted table.

    Args:
        results: Nested dictionary containing tournament statistics

    Returns:
        A pandas dataframe containing the tournament results in a matrix format
    """

    players = sorted(results.keys())

    # Create empty DataFrame with players as both index and columns
    matrix_df = pd.DataFrame(index=players, columns=players)

    # Fill the DataFrame
    for player1 in players:
        for player2 in players:
            if player1 == player2:
                matrix_df.loc[player1, player2] = '-'
            else:
                stats = results[player1][player2]
                matrix_df.loc[player1, player2] = f"W:{stats['wins']},D:{stats['draws']},L:{stats['losses']}"

    print(matrix_df.to_markdown())

    return matrix_df


if __name__ == "__main__":
    if DRAW_GAME:
        pygame.init()

    bots_dict = {
        "Random Bot": RandomBot(),
        "Max Distance Bot": MaxDistanceBot(),
        "Greedy Max Distance Bot": MaxDistanceGreedyBot(),
        "Worst Greedy Min Distance Bot": MinDistanceWorstGreedyBot(),
        # Add more bots here as needed
    }

    game_manager_obj = GameManager(display_game=DRAW_GAME)

    tournament_results = run_tournament(game_manager_obj, bots_dict)
    display_results(tournament_results)
