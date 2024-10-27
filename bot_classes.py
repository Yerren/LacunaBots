import numpy as np
from abc import ABC
from game_resources import GameManager
import logging


class Bot(ABC):
    """
    Abstract class that defines the interface for a Lacuna bot.
    """
    def make_move(self, game_manager: 'GameManager'):
        """
        Implement this method to make the bot choose a move. It should return a tuple (selected_pieces, token_position),
        where selected_pieces is a list containing the two selected pieces and token_position is the position of the
        where the player token should be placed.

        Args:
            game_manager (GameManager): Current game state manager.

        """
        pass


class RandomBot(Bot):
    def make_move(self, game_manager: 'GameManager'):
        game_state, placed_player_tokens, game_pieces_captured_by_colour = game_manager.get_normalized_game_state()

        valid_placements = []
        while not valid_placements:
            possible_moves = []
            for colour_index, colour_state in game_state.items():
                connections = colour_state['connections']
                # coordinates = colour_state['coordinates']
                colour_pieces = colour_state['pieces']

                for index_i in range(connections.shape[0]):
                    for index_j in range(connections.shape[1]):
                        if connections[index_i, index_j]:
                            possible_moves.append([colour_pieces[index_i], colour_pieces[index_j]])

            selected_pieces = possible_moves[np.random.choice(len(possible_moves))]

            valid_placements = game_manager.get_valid_token_placements(selected_pieces)

            if valid_placements:
                return selected_pieces, valid_placements[np.random.choice(len(valid_placements))]


class MaxDistanceBot(Bot):
    def __init__(self):
        self.random_bot = RandomBot()

    def make_move(self, game_manager: 'GameManager'):
        game_state, placed_player_tokens, game_pieces_captured_by_colour = game_manager.get_normalized_game_state()

        max_distance_comparator = -1
        for colour_index, colour_state in game_state.items():
            connections = colour_state['connections']
            coordinates = colour_state['coordinates']
            colour_pieces = colour_state['pieces']

            for index_i in range(connections.shape[0]):
                for index_j in range(connections.shape[1]):
                    if connections[index_i, index_j]:
                        x1, y1 = coordinates[index_i]
                        x2, y2 = coordinates[index_j]
                        distance_comparator = (x2 - x1) ** 2 + (y2 - y1) ** 2  # Note: no sqrt because we are just comparing the distances.

                        if distance_comparator > max_distance_comparator:
                            max_distance_comparator = distance_comparator
                            selected_pieces = [colour_pieces[index_i], colour_pieces[index_j]]

        valid_placements = game_manager.get_valid_token_placements(selected_pieces)
        if valid_placements:
            return selected_pieces, valid_placements[len(valid_placements) // 2]
        else:
            # Fallback in case it returns no valid_placements somehow
            logging.info("MaxDistanceBot: Doing random move")
            return self.random_bot.make_move(game_manager)


class MaxDistanceGreedyBot(Bot):
    def __init__(self):
        self.random_bot = RandomBot()

    def make_move(self, game_manager: 'GameManager'):
        game_state, placed_player_tokens, game_pieces_captured_by_colour = game_manager.get_normalized_game_state()
        current_player_index = game_manager.current_player_index

        # Order colours by:
        # 1. Neither player has more than NUM_PIECES // 2 + 1
        # 2. Current player has the largest difference in captured pieces compared to other player
        current_player_captures = game_pieces_captured_by_colour[current_player_index]
        other_player_captures = game_pieces_captured_by_colour[1 - current_player_index]

        greedy_colour_order_array = np.zeros(game_manager.num_colours)
        for key in current_player_captures.keys():
            if current_player_captures[key] < game_manager.num_pieces // 2 + 1 and other_player_captures[key] < game_manager.num_pieces // 2 + 1:
                greedy_score = current_player_captures[key] - other_player_captures[key]
            else:
                greedy_score = -game_manager.num_pieces
            greedy_colour_order_array[key] = greedy_score

        greedy_colour_order = np.argsort(-greedy_colour_order_array)

        max_distance_comparator = -1
        for greedy_colour_choice in greedy_colour_order:

            colour_state = game_state[greedy_colour_choice]
            connections = colour_state['connections']
            coordinates = colour_state['coordinates']
            colour_pieces = colour_state['pieces']

            selected_pieces = []
            for index_i in range(connections.shape[0]):
                for index_j in range(connections.shape[1]):
                    if connections[index_i, index_j]:
                        x1, y1 = coordinates[index_i]
                        x2, y2 = coordinates[index_j]
                        distance_comparator = (x2 - x1) ** 2 + (y2 - y1) ** 2  # Note: no sqrt because we are just comparing the distances.

                        if distance_comparator > max_distance_comparator:
                            max_distance_comparator = distance_comparator
                            selected_pieces = [colour_pieces[index_i], colour_pieces[index_j]]

            if selected_pieces:
                valid_placements = game_manager.get_valid_token_placements(selected_pieces)
                if valid_placements:
                    return selected_pieces, valid_placements[len(valid_placements) // 2]

        # Fallback in case it returns no valid_placements somehow
        logging.info("MaxDistanceGreedyBot: Doing random move")
        return self.random_bot.make_move(game_manager)


class MinDistanceWorstGreedyBot(Bot):
    def __init__(self):
        self.random_bot = RandomBot()

    def make_move(self, game_manager: 'GameManager'):

        game_state, placed_player_tokens, game_pieces_captured_by_colour = game_manager.get_normalized_game_state()
        current_player_index = game_manager.current_player_index

        # Order colours by:
        # 1. Neither player has more than NUM_PIECES // 2 + 1
        # 2. Current player has the largest difference in captured pieces compared to other player
        current_player_captures = game_pieces_captured_by_colour[current_player_index]
        other_player_captures = game_pieces_captured_by_colour[1 - current_player_index]

        greedy_colour_order_array = np.zeros(game_manager.num_colours)
        for key in current_player_captures.keys():
            if current_player_captures[key] < game_manager.num_pieces // 2 + 1 and other_player_captures[key] < game_manager.num_pieces // 2 + 1:
                greedy_score = current_player_captures[key] - other_player_captures[key]
            else:
                greedy_score = -game_manager.num_pieces
            greedy_colour_order_array[key] = greedy_score

        greedy_colour_order = np.argsort(greedy_colour_order_array)

        max_distance_comparator = 1
        for greedy_colour_choice in greedy_colour_order:
            try:
                colour_state = game_state[greedy_colour_choice]
                connections = colour_state['connections']
                coordinates = colour_state['coordinates']
                colour_pieces = colour_state['pieces']
            except KeyError:
                continue

            selected_pieces = []
            valid_placements = []
            for index_i in range(connections.shape[0]):
                for index_j in range(connections.shape[1]):
                    if connections[index_i, index_j]:
                        x1, y1 = coordinates[index_i]
                        x2, y2 = coordinates[index_j]
                        distance_comparator = (x2 - x1) ** 2 + (y2 - y1) ** 2  # Note: no sqrt because we are just comparing the distances.
                        if distance_comparator < max_distance_comparator:
                            selected_pieces_temp = [colour_pieces[index_i], colour_pieces[index_j]]
                            valid_placements_temp = game_manager.get_valid_token_placements(selected_pieces_temp)
                            if valid_placements_temp:
                                max_distance_comparator = distance_comparator
                                selected_pieces = selected_pieces_temp.copy()
                                valid_placements = valid_placements_temp.copy()

            if valid_placements:
                return selected_pieces, valid_placements[0]

        # Fallback in case it returns no valid_placements somehow
        logging.info("MinDistanceWorstBot: Doing random move")
        return self.random_bot.make_move(game_manager)
