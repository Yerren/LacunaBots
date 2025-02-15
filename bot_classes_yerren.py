import numpy as np
from game_resources import GameManager, PlayerType, Piece
import logging
from bot_classes import Bot, RandomBot
import math
import time
from typing import Tuple


class MaxClosestPiecesBot(Bot):
    """
    A bot that
    """
    def __init__(self, resolution=15):
        self.random_bot = RandomBot()
        self.resolution = resolution

    def make_move(self, game_manager: 'GameManager'):
        game_state, placed_player_tokens, game_pieces_captured_by_colour = game_manager.get_normalized_game_state()
        current_player_index = game_manager.current_player_index

        # Only consider colours where:
        # 1. Neither player has more than NUM_PIECES // 2 + 1
        current_player_captures = game_pieces_captured_by_colour[current_player_index]
        other_player_captures = game_pieces_captured_by_colour[1 - current_player_index]

        colour_indices_to_consider = []
        for key in current_player_captures.keys():
            if current_player_captures[key] < game_manager.num_pieces // 2 + 1 and other_player_captures[key] < game_manager.num_pieces // 2 + 1:
                colour_indices_to_consider.append(key)

        max_number_of_closest_pieces = -float('inf')
        selected_pieces = []
        selected_placement = None
        for colour_index, colour_state in game_state.items():

            colour_state = game_state[colour_index]
            connections = colour_state['connections']
            coordinates = colour_state['coordinates']
            colour_pieces = colour_state['pieces']

            for index_i in range(connections.shape[0]):
                for index_j in range(connections.shape[1]):
                    if connections[index_i, index_j]:
                        temp_selected_pieces = [colour_pieces[index_i], colour_pieces[index_j]]
                        temp_placements = game_manager.get_valid_token_placements(temp_selected_pieces, resolution=self.resolution)
                        if not temp_placements:
                            continue

                        for temp_placement in temp_placements:
                            # temp_placement = temp_placements[len(temp_placements) // 2]

                            closest_pieces_comparator = 0
                            for piece in game_manager.pieces:
                                if piece.colour_index not in colour_indices_to_consider:
                                    continue

                                if piece.closest_token is not None and piece.closest_token.player_index == current_player_index:
                                    continue

                                if piece in selected_pieces:
                                    continue

                                temp_placement_screen_space = game_manager.unnormalize_coordinates(temp_placement)

                                dx = piece.x - temp_placement_screen_space[0]
                                dy = piece.y - temp_placement_screen_space[1]
                                distance = math.sqrt(dx * dx + dy * dy)
                                if len(placed_player_tokens[0]) + len(placed_player_tokens[1]) == 0:
                                    # This is the first move of the game. Just try to minimize distance to all pieces.
                                    closest_pieces_comparator -= distance
                                else:
                                    # Normal behaviour
                                    if distance < piece.closest_distance:
                                        closest_pieces_comparator += 1

                            if closest_pieces_comparator > max_number_of_closest_pieces:
                                max_number_of_closest_pieces = closest_pieces_comparator
                                selected_pieces = [colour_pieces[index_i], colour_pieces[index_j]]
                                selected_placement = temp_placement

        if selected_pieces:
            return tuple(selected_pieces), selected_placement

        # Fallback in case it returns no valid_placements somehow
        logging.info("MaxClosestPiecesBot: Doing random move")
        return self.random_bot.make_move(game_manager)


class MinimaxBot(Bot):
    """
    A bot that performs minimax search... to some extent.
    """
    def __init__(self, resolution=15, max_depth=2, order_moves=True, one_step_lookahead=True):
        self.resolution = resolution
        self.max_depth = max_depth
        self.num_nodes = 0
        self.previous_scores = {}
        self.order_moves = order_moves
        self.one_step_lookahead = one_step_lookahead

    def evaluate_position(self, game_manager: 'GameManager', target_player_index: int, game_reward: int = 100, colour_reward: int = 10, possible_colour_reward: int = 5):
        previous_game_state = game_manager.export_current_state()
        score = 0
        # If game is finished, +/-game_reward for winning/losing
        if game_manager.game_phase == "end_game":
            game_manager.collect_end_game_pieces()
            winner = game_manager.determine_winner()

            game_manager.import_state(previous_game_state)

            if game_manager.players.index(winner) == target_player_index:
                score += game_reward
            else:
                score -= game_reward

        # +/-colour_reward for each completed set of tokens
        player_1_win_count, player_2_win_count = game_manager.count_collected_colour_wins()
        if target_player_index == 0:
            score += colour_reward * player_1_win_count
            score -= colour_reward * player_2_win_count
        else:
            score -= colour_reward * player_1_win_count
            score += colour_reward * player_2_win_count

        # Plus +/-5 for each set of tokens that would be won based on the current closest pieces. Note this does
        # double count based on the previous step, which is fine.
        game_manager.collect_end_game_pieces()
        player_1_win_count, player_2_win_count = game_manager.count_collected_colour_wins()
        if target_player_index == 0:
            score += possible_colour_reward * player_1_win_count
            score -= possible_colour_reward * player_2_win_count
        else:
            score -= possible_colour_reward * player_1_win_count
            score += possible_colour_reward * player_2_win_count

        game_manager.import_state(previous_game_state)
        return score


    def get_possible_placements(self, game_manager: 'GameManager'):
        game_state, placed_player_tokens, game_pieces_captured_by_colour = game_manager.get_normalized_game_state()
        current_player_index = game_manager.current_player_index

        # Only consider colours where:
        # 1. Neither player has more than NUM_PIECES // 2 + 1
        current_player_captures = game_pieces_captured_by_colour[current_player_index]
        other_player_captures = game_pieces_captured_by_colour[1 - current_player_index]

        colour_indices_to_consider = []
        for key in current_player_captures.keys():
            if (current_player_captures[key] < game_manager.num_pieces // 2 + 1 and
                    other_player_captures[key] < game_manager.num_pieces // 2 + 1):
                colour_indices_to_consider.append(key)

        output_list = []
        for colour_index, colour_state in game_state.items():

            colour_state = game_state[colour_index]
            connections = colour_state['connections']
            # coordinates = colour_state['coordinates']
            colour_pieces = colour_state['pieces']

            for index_i in range(connections.shape[0]):
                for index_j in range(connections.shape[1]):
                    if connections[index_i, index_j]:
                        temp_selected_pieces = [colour_pieces[index_i], colour_pieces[index_j]]
                        temp_placements = game_manager.get_valid_token_placements(temp_selected_pieces,
                                                                                  resolution=self.resolution)
                        if not temp_placements:
                            continue

                        output_list.append((tuple(temp_selected_pieces), temp_placements))

        return output_list

    def get_score_for_ordering(self, move_in, game_manager: 'GameManager', take_max_score: bool):
        hash_str = self.create_hash(game_manager, move_in[0], move_in[1])

        try:
            return self.previous_scores[hash_str]
        except KeyError:
            if take_max_score:
                return -1e10
            return 1e10

    def create_hash(self, game_manager: 'GameManager', selected_pieces, token_position):
        player_details, pieces, current_player_index, _ = game_manager.export_current_state()

        hash_str = ""
        for player_detail in player_details:
            for piece in player_detail["collected_pieces"]:
                hash_str += str(piece)
            for token in player_detail["placed_tokens"]:
                hash_str += str(token)

        for piece in pieces:
            hash_str += str(piece)

        hash_str += str(current_player_index)

        hash_str += f"{selected_pieces[0]} {selected_pieces[1]} {token_position[0]:.2f} {token_position[1]:.2f}"

        return hash_str


    def recursive_step(self, game_manager: 'GameManager', depth: int, target_player_index: int, take_max_score=True, alpha=-1e10, beta=1e10):
        self.num_nodes += 1
        if depth == 0 or game_manager.game_phase == "end_game":
            return None, None, self.evaluate_position(game_manager, target_player_index)

        possibilities_list = self.get_possible_placements(game_manager)

        if take_max_score:
            best_score = -1e10
        else:
            best_score = 1e10

        flattened_possibilities_list = []
        for possibility in possibilities_list:
            for token_position in possibility[1]:
                flattened_possibilities_list.append((possibility[0], token_position))

        if self.order_moves:
            # Do move ordering
            flattened_possibilities_list = sorted(flattened_possibilities_list, key=lambda move: self.get_score_for_ordering(move, game_manager, take_max_score), reverse=take_max_score)
        elif self.one_step_lookahead and depth > 1:
            score_list = []
            for selected_pieces, token_position in flattened_possibilities_list:
                previous_game_state = game_manager.export_current_state()
                game_manager.manual_apply_move(selected_pieces, token_position)
                _, _, score = self.recursive_step(game_manager, 0, target_player_index,
                                                  take_max_score=not take_max_score, alpha=alpha, beta=beta)
                game_manager.import_state(previous_game_state)
                score_list.append(score)

            flattened_possibilities_list = [x for _, x in sorted(zip(score_list, flattened_possibilities_list), key=lambda pair: pair[0], reverse=take_max_score)]


        best_pieces = None
        best_placement = None
        for selected_pieces, token_position in flattened_possibilities_list:
            previous_game_state = game_manager.export_current_state()
            if self.order_moves:
                move_hash = self.create_hash(game_manager, selected_pieces, token_position)
            game_manager.manual_apply_move(selected_pieces, token_position)
            _, _, score = self.recursive_step(game_manager, depth - 1, target_player_index, take_max_score=not take_max_score, alpha=alpha, beta=beta)

            if self.order_moves:
                self.previous_scores[move_hash] = score

            if take_max_score:
                alpha = max(alpha, score)
                if score > best_score:
                    best_score = score
                    best_pieces = selected_pieces
                    best_placement = token_position
            else:
                beta = min(beta, score)
                if score < best_score:
                    best_score = score
                    best_pieces = selected_pieces
                    best_placement = token_position

            game_manager.import_state(previous_game_state)

            if beta <= alpha:
                break

        # print(f"Returning. Depth: {depth}, Best score: {score}")
        return best_pieces, best_placement, best_score


    def make_move(self, game_manager: 'GameManager'):
        initial_game_state = game_manager.export_current_state()
        internal_game_manager = GameManager(num_colours=game_manager.num_colours,
                                            num_pieces=game_manager.num_pieces,
                                            num_player_tokens=game_manager.num_player_tokens,
                                            display_game=False)
        players = [
            game_manager.create_player(game_manager.players[0].colour, game_manager.players[0].name, PlayerType.AI, bot_class=RandomBot()),
            game_manager.create_player(game_manager.players[1].colour, game_manager.players[0].name, PlayerType.AI, bot_class=RandomBot())
        ]
        internal_game_manager.set_players(players)
        internal_game_manager.reset_and_setup_game()

        internal_game_manager.import_state(initial_game_state)
        self.num_nodes = 0
        start_time = time.time()


        if self.order_moves:
            current_depth = 1
        else:
            current_depth = self.max_depth
        while current_depth <= self.max_depth:
            best_pieces, best_placement, best_score = self.recursive_step(internal_game_manager, current_depth, game_manager.current_player_index)
            current_depth += 1

        # best_pieces, best_placement, best_score = self.recursive_step(internal_game_manager, self.max_depth,
        #                                                               game_manager.current_player_index)

        end_time = time.time()
        total_time = end_time - start_time
        print(f"Final best score: {best_score}. {self.num_nodes} nodes visited. Duration: {int(total_time)} seconds.")
        return tuple(best_pieces), best_placement