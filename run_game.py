"""
Runs a single game of Lacuna with human and/or bot players. Use left mouse button to progress through the game.
"""

from game_resources import *
from bot_classes import MaxDistanceBot, MinDistanceWorstGreedyBot, MaxDistanceGreedyBot, RandomBot
import random
import numpy as np


def main() -> None:
    """
    Main game loop function.

    Initializes the game window, sets up players, and runs the main game loop.
    Players can be configured as either AI or Human players.
    """
    pygame.init()
    random.seed(1)
    np.random.seed(1)
    game_manager = GameManager(display_game=True)

    player_colours = [(192, 192, 192), (255, 215, 0)]  # Silver and Gold
    players = [
        game_manager.create_player(player_colours[0], "Player 1", PlayerType.AI, bot_class=MinDistanceWorstGreedyBot()),
        game_manager.create_player(player_colours[1], "Player 2", PlayerType.AI, bot_class=MaxDistanceGreedyBot())
    ]

    game_manager.set_players(players)
    game_manager.reset_and_setup_game()

    result = {"game_status": 'in_progress'}
    while result["game_status"] == 'in_progress':
        result = game_manager.perform_game_step()

    if result["game_status"] == 'finished':
        print(f"Game over. {result['winner'].name} wins!")

    pygame.quit()


if __name__ == "__main__":
    main()