"""
Runs a single game of Lacuna with human and/or bot players. Use left mouse button to progress through the game.
"""

from game_resources import *
from bot_classes import *
import random
import numpy as np
from bot_classes_yerren import *


def main() -> None:
    pygame.init()
    random.seed(1)
    np.random.seed(1)
    game_manager = GameManager(display_game=False, num_player_tokens=4)

    player_colours = [(192, 192, 192), (255, 215, 0)]  # Silver and Gold
    # players = [
    #     game_manager.create_player(player_colours[0], "Player 1", PlayerType.AI, bot_class=RandomBot()),
    #     game_manager.create_player(player_colours[1], "Player 2", PlayerType.AI, bot_class=MaxClosestPiecesBot())
    # ]

    players = [
        game_manager.create_player(player_colours[0], "Player 1", PlayerType.AI, bot_class=MaxClosestPiecesBot()),
        game_manager.create_player(player_colours[1], "Player 2", PlayerType.AI, bot_class=MinimaxBot(resolution=7, max_depth=2, order_moves=False, one_step_lookahead=True))
    ]
    # players = [
    #     game_manager.create_player(player_colours[0], "Player 1", PlayerType.HUMAN),
    #     game_manager.create_player(player_colours[1], "Player 2", PlayerType.HUMAN)
    # ]

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
