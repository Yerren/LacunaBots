"""
This file implements a strategic board game where two players take turns placing tokens
and collecting coloured pieces. Players must connect same-coloured pieces with their tokens
to capture them. The game ends when all tokens are placed, followed by an end-game phase
where remaining pieces are collected based on proximity to placed tokens.

"""
from typing import List, Tuple, Dict, Optional, Union
import pygame
import random
import math
import numpy as np
from collections import defaultdict
from enum import Enum
# from bot_classes import Bot


class Piece:
    """
    Represents a game piece on the board.

    Attributes:
        x (float): X-coordinate of the piece
        y (float): Y-coordinate of the piece
        colour (Tuple[int, int, int]): RGB colour tuple of the piece
        colour_index (int): Index of the piece's colour (relative to game_manager.piece_colours)
        radius (int): Radius of the piece in pixels
        closest_token (Optional[PlayerToken]): Reference to the closest player token
        closest_distance (float): Distance to the closest token
    """

    def __init__(self, x: float, y: float, colour: Tuple[int, int, int], colour_index: int, radius: int) -> None:
        """
        Initializes a new Piece object.

        Args:
            x (float): X-coordinate of the piece
            y (float): Y-coordinate of the piece
            colour (Tuple[int, int, int]): RGB colour tuple of the piece
            colour_index (int): Index of the piece's colour (relative to game_manager.piece_colours)
            radius (int): Radius of the piece in pixels
        """
        self.x = x
        self.y = y
        self.colour = colour
        self.colour_index = colour_index
        self.radius = radius
        self.closest_token = None
        self.closest_distance = float('inf')

    def draw(self, screen: pygame.Surface, draw_closest_token_markers: bool) -> None:
        """
        Draw the piece on the screen.

        Args:
            screen (pygame.Surface): Pygame surface to draw on
            draw_closest_token_markers (bool): Whether to draw markers indicating the closest player token to this piece
        """
        pygame.draw.circle(screen, self.colour, (int(self.x), int(self.y)), self.radius)
        if draw_closest_token_markers and self.closest_token is not None:
            pygame.draw.circle(screen, self.closest_token.colour, (int(self.x), int(self.y)),
                               self.radius + 2, 2)
            pygame.draw.line(screen, self.closest_token.colour,
                             (self.x, self.y), (self.closest_token.x, self.closest_token.y), 1)

    def overlaps(self, other: 'Piece') -> bool:
        """
        Check if this piece overlaps with another piece.

        Args:
            other: Another Piece object to check for overlap

        Returns:
            bool: True if pieces overlap, False otherwise
        """
        dx = self.x - other.x
        dy = self.y - other.y
        distance = math.sqrt(dx * dx + dy * dy)
        return distance < 2 * self.radius

    def __str__(self):
        return f"{self.x:.2f}x_{self.y:.2f}y_{self.colour_index}c"


class PlayerToken:
    """
    Represents a token placed by a player.

    Attributes:
        x (float): X-coordinate of the token
        y (float): Y-coordinate of the token
        colour (Tuple[int, int, int]): RGB colour tuple of the token
        player_token_border_colour (Tuple[int, int, int]): RGB colour tuple for token border
        player_token_radius (int): Radius of the token in pixels
        player_token_border_width (int): Width of the token border in pixels
        radius (int): Total radius including border
        player_index (int): The index of the player (relative to game_manager.players) who placed this token
    """

    def __init__(self, x: float, y: float, colour: Tuple[int, int, int],
                 player_token_border_colour: Tuple[int, int, int],
                 player_token_radius: int, player_token_border_width: int,
                 player_index: int):
        """
        Initialize a new player token.

        Args:
            x (float): X-coordinate of the token
            y (float): Y-coordinate of the token
            colour (Tuple[int, int, int]): RGB colour tuple of the token
            player_token_border_colour (Tuple[int, int, int]): RGB colour tuple for token border
            player_token_radius (int): Radius of the token in pixels
            player_token_border_width (int): Width of the token border in pixels
            player_index (int): The index of the player (relative to game_manager.players) who placed this token
        """
        self.x = x
        self.y = y
        self.player_token_border_colour = player_token_border_colour
        self.player_token_radius = player_token_radius
        self.player_token_border_width = player_token_border_width
        self.radius = self.player_token_radius + self.player_token_border_width
        self.colour = colour
        self.player_index = player_index

    def draw(self, screen: pygame.Surface) -> None:
        """
        Draw the token on the screen with a border.

        Args:
            screen: Pygame surface to draw on
        """
        pygame.draw.circle(screen, self.player_token_border_colour, (int(self.x), int(self.y)),
                           self.player_token_radius + self.player_token_border_width)
        pygame.draw.circle(screen, self.colour, (int(self.x), int(self.y)), self.player_token_radius)

    def overlaps_with_object(self, other_object: Union['Piece', 'PlayerToken']) -> bool:
        """
        Check if this token overlaps with a game piece.

        Args:
            other_object (Piece or PlayerToken): The piece to check for overlap

        Returns:
            bool: True if token overlaps with the piece, False otherwise
        """
        dx = self.x - other_object.x
        dy = self.y - other_object.y
        distance = math.sqrt(dx * dx + dy * dy)
        return distance < (self.radius + other_object.radius)

    def __str__(self):
        return f"{self.x:.2f}x_{self.y:.2f}y_{self.player_index}p"


class PlayerType(Enum):
    """Enumeration of player types."""
    HUMAN = 1
    AI = 2


class Player:
    """
    Represents a player in the game.

    Attributes:
        colour (Tuple[int, int, int]): RGB colour tuple for the player
        name (str): Player's name
        player_type (PlayerType): Type of player (HUMAN or AI)
        player_token_border_colour (Tuple[int, int, int]): RGB colour for token borders
        player_token_radius (int): Radius of player token in pixels
        player_token_border_width (int): Width of token borders in pixels
        num_player_tokens (int): Number of tokens available to the player
        num_colours (int): Number of different colours in the game
        collected_pieces (List[Piece]): List of pieces collected by the player
        tokens (List[PlayerToken]): List of all tokens owned by the player
        placed_tokens (List[PlayerToken]): List of tokens placed on the board
        collected_by_colour (Dict[int, int]): Count of collected pieces by colour
        player_index (int): The index of this player (relative to game_manager.players)
        bot_class (Optional[object]): AI bot class for AI players
    """

    def __init__(self, colour: Tuple[int, int, int], name: str, player_type: PlayerType,
                 player_token_border_colour: Tuple[int, int, int], player_token_radius: int,
                 player_token_border_width: int, num_player_tokens: int, num_colours: int,
                 bot_class: 'Bot' = None):
        """
        Initialize a new player.

        Args:
            colour (Tuple[int, int, int]): RGB colour tuple for the player
            name (str): Player's name
            player_type (PlayerType): Type of player (HUMAN or AI)
            player_token_border_colour (Tuple[int, int, int]): RGB colour for token borders
            player_token_radius (int): Radius of player token in pixels
            player_token_border_width (int): Width of token border in pixels
            num_player_tokens (int): Number of tokens available to the player
            num_colours (int): Number of different colours in the game
            bot_class (Optional[Bot]): AI bot class for AI players
        """
        self.colour = colour
        self.name = name
        self.player_type = player_type
        self.player_token_border_colour = player_token_border_colour
        self.player_token_radius = player_token_radius
        self.player_token_border_width = player_token_border_width
        self.num_player_tokens = num_player_tokens
        self.num_colours = num_colours
        self.collected_pieces = []
        self.tokens = []
        self.placed_tokens = []
        self.collected_by_colour = {i: 0 for i in range(self.num_colours)}
        self.player_index = -1
        self.bot_class = bot_class
        self.reset_player()

    def make_move(self, game_manager: 'GameManager') -> Tuple[Optional[List[Piece]], Optional[Tuple[float, float]]]:
        """
        Make a move in the game.

        Args:
            game_manager (GameManager): Current game state manager

        Returns:
            Tuple[Optional[List[Piece]], Optional[Tuple[float, float]]]: Selected pieces and token position for AI,
            or (None, None) for human players
        """
        if self.player_type == PlayerType.AI:
            return self.bot_class.make_move(game_manager)
        return None, None  # Human moves are handled in the event loop

    def reset_player(self) -> None:
        """Reset the player's state to initial conditions."""
        self.collected_pieces = []
        self.tokens = []
        self.placed_tokens = []
        self.collected_by_colour = {i: 0 for i in range(self.num_colours)}
        self.tokens = [PlayerToken(-100, -100, self.colour, self.player_token_border_colour, self.player_token_radius,
                                   self.player_token_border_width, self.player_index) for _ in range(self.num_player_tokens)]


class GameManager:
    """
    Manages the current state of the game including players, pieces, and game phase.

    Attributes:
        players (List[Player]): List of players in the game
        current_player_index (int): Index of the current player
        pieces (List[Piece]): List of game pieces on the board
        selected_pieces (List[Piece]): Currently selected pieces
        hover_piece (Optional[Piece]): Piece currently being hovered over
        game_phase (str): Current phase of the game ("playing", "end_game", or "game_over")
        ai_move_ready (bool): Whether AI move is ready to be executed
        ai_selected_pieces (List[Piece]): Pieces selected by AI for current move
        ai_token_position (Optional[Tuple[float, float]]): Position where AI will place token
    """

    def __init__(self, num_colours: int = 7, num_pieces: int = 7, num_player_tokens: int = 6, display_game: bool = True) -> None:
        """
        Initialize a new game state manager.

        Args:
            num_colours (int): Number of different colors in the game (1-7)
            num_pieces (int): Number of pieces per color
            num_player_tokens (int): Number of tokens each player gets
            display_game (bool): Whether to show the game visually using Pygame
        """

        self.num_colours = num_colours
        assert 0 < self.num_colours <= 7

        self.num_pieces = num_pieces
        assert 0 < self.num_pieces

        self.num_player_tokens = num_player_tokens
        assert 0 < self.num_player_tokens

        self.board_radius = 450
        self.piece_radius = 14
        self.player_token_radius = 10
        self.player_token_border_width = 3
        self.effective_player_token_radius = self.player_token_radius + self.player_token_border_width
        self.window_size = (2 * self.board_radius + 800, 2 * self.board_radius + 100)
        self.display_game = display_game

        # colours
        self.background_colour = (255, 255, 255)
        self.board_colour = (25, 25, 25)
        self.player_token_border_colour = (255, 255, 255)
        self.piece_selection_border_colour = (200, 200, 200)
        self.piece_colours = [
            (230, 25, 75),  # Red
            (60, 180, 75),  # Green
            (0, 130, 200),  # Blue
            (255, 255, 25),  # Yellow
            (245, 130, 48),  # Orange
            (240, 50, 230),  # Magenta
            (70, 240, 240)  # Cyan
        ]

        self.players = None
        self.current_player_index = 0
        self.pieces = []
        self.selected_pieces = []
        self.hover_piece = None
        self.game_phase = "playing"
        self.ai_move_ready = False
        self.ai_selected_pieces = []
        self.ai_token_position = None

        if self.display_game:
            self.screen = pygame.display.set_mode(self.window_size)
            pygame.display.set_caption("Lacuna")

    def export_current_state(self) -> Tuple[List[Dict], List[Piece], int, str]:
        """
        Exports the current state of the game (locations of pieces, tokens, status of captures, etc.) in a form that can
        be loaded by import_state().

        Returns: a tuple containing the current state of the game.
        """
        player_details = [
            {"collected_pieces": self.players[0].collected_pieces.copy(),
             "placed_tokens": self.players[0].placed_tokens.copy(),
             "collected_by_colour": self.players[0].collected_by_colour.copy(),
             },
            {"collected_pieces": self.players[1].collected_pieces.copy(),
             "placed_tokens": self.players[1].placed_tokens.copy(),
             "collected_by_colour": self.players[1].collected_by_colour.copy(),
             }
        ]

        return player_details, self.pieces.copy(), self.current_player_index, self.game_phase

    def import_state(self, input_state: Tuple[List[Dict], List[Piece], int, str]) -> None:
        """
        Sets the current state of the game to provided input_state, which should be a tuple created by
        export_current_state().

        Args:
            input_state: the tuple provided by export_current_state().
        """
        player_details, pieces, self.current_player_index, game_phase = input_state
        self.pieces = pieces.copy()

        self.players[0].collected_pieces = player_details[0]["collected_pieces"].copy()
        self.players[0].placed_tokens = player_details[0]["placed_tokens"].copy()
        self.players[0].collected_by_colour = player_details[0]["collected_by_colour"].copy()

        self.players[1].collected_pieces = player_details[1]["collected_pieces"].copy()
        self.players[1].placed_tokens = player_details[1]["placed_tokens"].copy()
        self.players[1].collected_by_colour = player_details[1]["collected_by_colour"].copy()
        self.game_phase = game_phase
        self.update()

    def reset_and_setup_game(self) -> None:
        """
        Reset the game state and set up a new game, including resetting players and randomly capturing an initial piece
        for the first player.
        """

        for player in self.players:
            player.reset_player()

        self.current_player_index = 0
        self.pieces = self.generate_pieces()
        self.selected_pieces = []
        self.hover_piece = None
        self.game_phase = "playing"

        # Capture a random piece for the first player
        random_piece = random.choice(self.pieces)
        self.pieces.remove(random_piece)
        self.current_player.collected_pieces.append(random_piece)
        self.current_player.collected_by_colour[random_piece.colour_index] += 1

    def set_players(self, players: List['Player']) -> None:
        """
        Set the players participating in the game.

        Args:
            players (List[Player]): List of Player objects
        """
        for i, player in enumerate(players):
            player.player_index = i
        self.players = players

    @property
    def current_player(self):
        return self.players[self.current_player_index]

    def set_next_player(self) -> None:
        """Set the current_player_index to the next player."""
        self.current_player_index = (self.current_player_index + 1) % 2

    def handle_click(self, mouse_pos: Tuple[int, int] = (0, 0)) -> None:
        """
        Handle click events for both human and AI players. For human players, this handles general input. For AI
        players, it just progresses their turn.

        Args:
            mouse_pos (Tuple[int, int]): X,Y coordinates of the mouse click
        """
        if self.current_player.player_type == PlayerType.HUMAN:
            clicked_piece = self.get_clicked_piece(mouse_pos)
            if len(self.selected_pieces) == 2:
                self.handle_token_placement(mouse_pos, clicked_piece)
            else:
                self.handle_piece_selection(clicked_piece)
        elif self.current_player.player_type == PlayerType.AI:
            if self.ai_move_ready:
                self.execute_ai_move()
            else:
                self.get_ai_move()

    def get_clicked_piece(self, mouse_pos: Tuple[int, int]) -> Optional[Piece]:
        """
        Determine if a piece was clicked based on mouse position.

        Args:
            mouse_pos (Tuple[int, int]): X,Y coordinates of the mouse click

        Returns:
            Optional[Piece]: The clicked piece or None if no piece was clicked

        """
        mouse_x, mouse_y = mouse_pos
        for piece in self.pieces:
            dx = mouse_x - piece.x
            dy = mouse_y - piece.y
            if math.sqrt(dx * dx + dy * dy) < self.piece_radius:
                return piece
        return None

    def handle_token_placement(self, mouse_pos: Tuple[int, int], clicked_piece: Optional[Piece]) -> None:
        """
        Handle the placement of a token between two selected pieces.

        Args:
            mouse_pos (Tuple[int, int]): X,Y coordinates of the mouse click
            clicked_piece (Optional[Piece]): The piece that was clicked, if any

        Returns:

        """
        mouse_x, mouse_y = mouse_pos
        line_point = self.get_point_on_line(self.selected_pieces[0], self.selected_pieces[1], (mouse_x, mouse_y))
        dx = line_point[0] - mouse_x
        dy = line_point[1] - mouse_y
        if math.sqrt(dx * dx + dy * dy) < self.effective_player_token_radius:
            result = self.place_player_token(self.selected_pieces, (mouse_x, mouse_y), is_normalized=False)
            if result:
                self.set_next_player()
                self.selected_pieces = []
        else:
            if clicked_piece:
                self.selected_pieces = [clicked_piece]
            else:
                self.selected_pieces = []

    def handle_piece_selection(self, clicked_piece: Optional[Piece]) -> None:
        """
        Handle the selection of pieces by a human player.

        Args:
            clicked_piece (Optional[Piece]): The piece that was clicked, if any
        """
        if clicked_piece:
            if len(self.selected_pieces) == 0:
                self.selected_pieces.append(clicked_piece)
            elif len(self.selected_pieces) == 1:
                if clicked_piece.colour_index == self.selected_pieces[0].colour_index and clicked_piece != \
                        self.selected_pieces[0]:
                    if not self.check_line_intersection(self.selected_pieces[0], clicked_piece,
                                                        [self.selected_pieces[0], clicked_piece]):
                        self.selected_pieces.append(clicked_piece)
                else:
                    self.selected_pieces = [clicked_piece]
        else:
            self.selected_pieces = []

    def get_ai_move(self) -> None:
        """Request and store the AI player's next move."""
        self.ai_selected_pieces, self.ai_token_position = self.current_player.make_move(self)
        self.ai_move_ready = True

    def manual_apply_move(self, selected_pieces: Tuple[Piece, Piece], token_position: Tuple[float, float]) -> None:
        """Manually executes a move. Useful for implementing search trees."""
        self.ai_selected_pieces = selected_pieces
        self.ai_token_position = token_position
        result = self.place_player_token(selected_pieces, token_position, is_normalized=True)
        if result:
            self.set_next_player()
        self.update()

    def execute_ai_move(self) -> None:
        """Execute the stored AI move, and advance to the next player if successful."""
        result = self.place_player_token(self.ai_selected_pieces, self.ai_token_position, is_normalized=True)
        if result:
            self.set_next_player()
        self.ai_selected_pieces = []
        self.ai_token_position = None
        self.ai_move_ready = False

    def update(self) -> None:
        """Update the game state, checking for game-phase transitions and updating piece-token relationships."""
        if self.game_phase == "playing" and all(len(player.placed_tokens) == self.num_player_tokens for player in self.players):
            self.game_phase = "end_game"

        # Set the closest player token for each piece
        for piece in self.pieces:
            piece.closest_distance = float('inf')
            piece.closest_token = None

            for player in self.players:
                for token in player.placed_tokens:
                    dx = piece.x - token.x
                    dy = piece.y - token.y
                    distance = math.sqrt(dx * dx + dy * dy)

                    if distance < piece.closest_distance:
                        piece.closest_distance = distance
                        piece.closest_token = token

    def draw(self) -> None:
        """Draw the current game state to the screen, including board, pieces, tokens, and UI elements."""
        self.screen.fill(self.background_colour)

        center_x, center_y = self.window_size[0] // 2, self.window_size[1] // 2

        pygame.draw.circle(self.screen, self.board_colour, (center_x, center_y), self.board_radius)

        if self.game_phase == "playing":
            self.draw_move_preview()

        for piece in self.pieces:
            # piece.draw(self.screen, True)
            piece.draw(self.screen, self.game_phase == "end_game")
            if piece in self.selected_pieces and self.current_player.player_type == PlayerType.HUMAN:
                pygame.draw.circle(self.screen, self.piece_selection_border_colour,
                                   (int(piece.x), int(piece.y)), self.piece_radius + 2, 2)

        for player in self.players:
            for token in player.placed_tokens:
                token.draw(self.screen)

        self.draw_scoreboard()

        if self.game_phase == "playing":
            current_x = 20 if self.current_player_index == 0 else self.window_size[0] - 380
            pygame.draw.circle(self.screen, self.current_player.colour, (current_x, 25), 15)

    def draw_move_preview(self) -> None:
        """Draw a preview of the current move being considered."""
        if self.current_player.player_type == PlayerType.AI and self.ai_move_ready:
            center_x, center_y = self.window_size[0] // 2, self.window_size[1] // 2
            self.draw_line_between_pieces(self.ai_selected_pieces[0], self.ai_selected_pieces[1])
            preview_x = (self.ai_token_position[0] * 2 * self.board_radius) + (center_x - self.board_radius)
            preview_y = (self.ai_token_position[1] * 2 * self.board_radius) + (center_y - self.board_radius)
            preview_token = PlayerToken(preview_x, preview_y, self.current_player.colour,
                                        self.player_token_border_colour, self.player_token_radius,
                                        self.player_token_border_width, self.current_player_index)
            preview_token.draw(self.screen)
            for piece in self.ai_selected_pieces:
                pygame.draw.circle(self.screen, self.piece_selection_border_colour,
                                   (int(piece.x), int(piece.y)), self.piece_radius + 2, 2)
        elif self.current_player.player_type == PlayerType.HUMAN:
            if len(self.selected_pieces) == 1 and self.hover_piece and self.hover_piece != self.selected_pieces[0]:
                if self.hover_piece.colour_index == self.selected_pieces[0].colour_index:
                    if not self.check_line_intersection(self.selected_pieces[0], self.hover_piece,
                                                        [self.selected_pieces[0], self.hover_piece]):
                        self.draw_line_between_pieces(self.selected_pieces[0], self.hover_piece,
                                                 colour=(0, 255, 0, 128), width=1)
                    else:
                        self.draw_line_between_pieces(self.selected_pieces[0], self.hover_piece,
                                                 colour=(255, 0, 0, 128), width=1)

            if len(self.selected_pieces) == 2:
                self.draw_line_between_pieces(self.selected_pieces[0], self.selected_pieces[1])
                mouse_x, mouse_y = pygame.mouse.get_pos()
                line_point = self.get_point_on_line(self.selected_pieces[0], self.selected_pieces[1], (mouse_x, mouse_y))
                dx = line_point[0] - mouse_x
                dy = line_point[1] - mouse_y
                if math.sqrt(dx * dx + dy * dy) < 10:
                    if self.check_token_placement(line_point[0], line_point[1], self.selected_pieces):
                        preview_token = PlayerToken(line_point[0], line_point[1], self.current_player.colour,
                                                    self.player_token_border_colour, self.player_token_radius,
                                                    self.player_token_border_width, self.current_player_index)
                        preview_token.draw(self.screen)

    def collect_end_game_pieces(self) -> None:
        """Collect remaining pieces at the end of the game based on proximity to tokens."""
        for piece in self.pieces:
            if piece.closest_token:
                for player in self.players:
                    if any(token.colour == piece.closest_token.colour for token in player.placed_tokens):
                        player.collected_pieces.append(piece)
                        # Update the colour count
                        player.collected_by_colour[piece.colour_index] += 1
                        break
        self.pieces.clear()

    def place_player_token(self, selected_pieces: Union[Tuple[Piece, Piece], List[Piece]], position: Tuple[float, float], is_normalized: bool = False) -> bool:
        """
        Attempts to place a player token based on selected pieces and position.
        Args:
            selected_pieces (List[Piece]): List of two pieces to connect
            position (Tuple[float, float]): Position to place the token
            is_normalized (bool): Whether the position coordinates are normalized

        Returns:
            bool: True if token was successfully placed, False otherwise
        """
        if len(selected_pieces) != 2:
            return False

        if len(self.current_player.placed_tokens) >= self.num_player_tokens:
            return False

        # Convert normalized coordinates to screen coordinates if necessary
        if is_normalized:
            screen_x, screen_y = self.unnormalize_coordinates(position)
        else:
            screen_x, screen_y = position

        # Find the closest point on the line between selected pieces
        start, end = selected_pieces
        line_point = self.get_point_on_line(start, end, (screen_x, screen_y))

        # Check if the position is close enough to the line
        dx = line_point[0] - screen_x
        dy = line_point[1] - screen_y
        if math.sqrt(dx * dx + dy * dy) > 10:  # 10 pixels tolerance
            return False

        # Check if the token can be placed at this position
        if not self.check_token_placement(line_point[0], line_point[1], selected_pieces):
            return False

        # Create and place the token
        new_token = PlayerToken(line_point[0], line_point[1], self.current_player.colour,
                                self.player_token_border_colour, self.player_token_radius,
                                self.player_token_border_width, self.current_player_index)
        self.current_player.placed_tokens.append(new_token)

        # Collect the selected pieces
        for piece in selected_pieces:
            self.pieces.remove(piece)
            self.current_player.collected_pieces.append(piece)
            self.current_player.collected_by_colour[piece.colour_index] += 1

        return True

    def unnormalize_coordinates(self, position: Tuple[float, float]) -> Tuple[float, float]:
        center_x = self.window_size[0] // 2
        center_y = self.window_size[1] // 2
        screen_x = (position[0] * 2 * self.board_radius) + (center_x - self.board_radius)
        screen_y = (position[1] * 2 * self.board_radius) + (center_y - self.board_radius)

        return screen_x, screen_y

    def normalize_coordinates(self, position: Tuple[float, float]) -> Tuple[float, float]:
        center_x = self.window_size[0] // 2
        center_y = self.window_size[1] // 2
        norm_x = (position[0] - (center_x - self.board_radius)) / (2 * self.board_radius)
        norm_y = (position[1] - (center_y - self.board_radius)) / (2 * self.board_radius)
        return norm_x, norm_y


    def draw_scoreboard(self) -> None:
        """
        Draw the scoreboard showing player information and scores.
        """
        for i, player in enumerate(self.players):
            # Determine x position based on player index
            x_offset = self.window_size[0] - 350 if i == 1 else 50  # Right side for player 2, left side for player 1
            y_offset = 50  # Both scoreboards start at the same height

            # Player name and remaining tokens
            pygame.draw.rect(self.screen, player.colour, (x_offset, y_offset, 300, 150))
            font = pygame.font.Font(None, 36)
            name_text = font.render(f"{player.name}", True, (0, 0, 0))
            tokens_text = font.render(f"Tokens: {self.num_player_tokens - len(player.placed_tokens)}", True, (0, 0, 0))
            self.screen.blit(name_text, (x_offset + 10, y_offset + 10))
            self.screen.blit(tokens_text, (x_offset + 10, y_offset + 40))

            # Draw collected pieces by colour
            for colour_index in range(self.num_colours):
                x = x_offset + 10 + (colour_index * 40)
                y = y_offset + 80

                # Draw colour circle
                pygame.draw.circle(self.screen, self.piece_colours[colour_index], (x + 15, y), 15)

                # Draw count below the circle
                count = player.collected_by_colour[colour_index]
                count_text = font.render(str(count), True, (0, 0, 0))
                count_rect = count_text.get_rect(center=(x + 15, y + 25))
                self.screen.blit(count_text, count_rect)

    def check_token_placement(self, x: float, y: float, selected_pieces: List[Piece]) -> bool:
        """
        Check if a token can be placed at the given coordinates.

        Args:
            x (float): X coordinate for token placement
            y (float): Y coordinate for token placement
            selected_pieces (List[Piece]): List of pieces being connected by the token

        Returns:
            bool: True if the token can be placed, False otherwise
        """
        test_token = PlayerToken(x, y, (0, 0, 0), self.player_token_border_colour, self.player_token_radius,
                                 self.player_token_border_width, self.current_player_index)  # colour doesn't matter for testing

        # Check overlap with existing pieces
        for piece in self.pieces:
            if piece not in selected_pieces and test_token.overlaps_with_object(piece):
                return False

        # Check overlap with selected pieces
        for piece in selected_pieces:
            if test_token.overlaps_with_object(piece):
                return False

        # Check overlap with existing tokens
        for player in self.players:
            for token in player.placed_tokens:
                if test_token.overlaps_with_object(token):
                    return False

        return True

    def get_normalized_game_state(self) -> Tuple[Dict[int, Dict[str, Union[np.ndarray, List[Piece]]]], List[np.ndarray], List[Dict[int, int]]]:
        """
        Provides a normalized representation of the game state for AI agents.

        Returns:
            Tuple containing:
                - A dict, with one item for each colour of piece, keyed with their colour_index. Each item is a
                dictionary containing:
                    - connections: a numpy array of shape (num_pieces, num_pieces), the value indicates whether there is
                      an unobstructed line between pieces i and j.
                    - coordinates: a numpy array of shape (num_pieces, 2) containing normalised coordinates of the piece
                      at the given index.
                    - pieces: a list containing references to all the remaining pieces.
                - List of numpy arrays containing normalized player token positions
                - List of dictionaries containing captured piece counts by colour
        """
        # Group pieces by colour
        pieces_by_colour = defaultdict(list)
        for piece in self.pieces:
            pieces_by_colour[piece.colour_index].append(piece)

        # Center coordinates
        center_x = self.window_size[0] // 2
        center_y = self.window_size[1] // 2

        game_state = {}

        for colour_index, colour_pieces in pieces_by_colour.items():
            num_pieces = len(colour_pieces)

            # Initialize arrays
            connections = np.zeros((num_pieces, num_pieces))
            coordinates = np.zeros((num_pieces, 2))
            piece_references = colour_pieces

            # Fill coordinates array
            for i, piece in enumerate(colour_pieces):
                # Normalize coordinates to [0, 1]
                coordinates[i] = self.normalize_coordinates((piece.x, piece.y))

            # Fill connections array
            for i, piece1 in enumerate(colour_pieces):
                for j, piece2 in enumerate(colour_pieces):
                    if i != j:
                        # Check if line is unobstructed
                        if not self.check_line_intersection(piece1, piece2, [piece1, piece2]):
                            connections[i, j] = 1

                            # # Calculate normalized vector from piece1 to piece2
                            # dx = piece2.x - piece1.x
                            # dy = piece2.y - piece1.y
                            # # distance = math.sqrt(dx * dx + dy * dy)
                            #
                            # # Normalize vector
                            # connections[i, j, 1] = dx / (2 * self.board_radius)
                            # connections[i, j, 2] = dy / (2 * self.board_radius)

            game_state[colour_index] = {
                'connections': connections,
                'coordinates': coordinates,
                'pieces': piece_references
            }

        placed_player_tokens = []
        captured_game_pieces = []
        for player in self.players:
            # Get normalised player token locations
            placed_player_token_inner = np.zeros((len(player.placed_tokens), 2))
            for i, placed_token in enumerate(player.placed_tokens):
                placed_player_token_inner[i, 0] = (placed_token.x - (center_x - self.board_radius)) / (
                            2 * self.board_radius)
                placed_player_token_inner[i, 1] = (placed_token.y - (center_y - self.board_radius)) / (
                            2 * self.board_radius)
            placed_player_tokens.append(placed_player_token_inner)

            # Get current pieces captured by each player
            captured_game_pieces.append(player.collected_by_colour)

        return game_state, placed_player_tokens, captured_game_pieces,

    def perform_game_step(self, wait_for_click: bool = True) -> Dict[str, Optional[Player]]:
        """
        Process a single game step with optional user input.

        Args:
            wait_for_click: If True, waits for user click before processing

        Returns:
            Dict containing "game_status" ("quit", "finished", or "in_progress") and the "winner" player (if the game
            is finished).
        """
        if wait_for_click and self.display_game:
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    return {
                        "game_status": "quit",
                        "winner": None
                    }
                elif event.type == pygame.MOUSEBUTTONDOWN:
                    if self.game_inner_step(event):
                        return {
                            "game_status": "finished",
                            "winner": self.determine_winner()
                        }
        else:
            if self.game_inner_step():
                return {
                    "game_status": "finished",
                    "winner": self.determine_winner()
                }

        self.update()

        if self.display_game:
            self.draw()
            pygame.display.flip()

        # Update hover piece for human player
        if self.current_player.player_type == PlayerType.HUMAN:
            mouse_pos = pygame.mouse.get_pos()
            self.hover_piece = self.get_clicked_piece(mouse_pos)

        return {
            "game_status": "in_progress",
            "winner": None
        }

    def count_collected_colour_wins(self) -> Tuple[int, int]:
        """Counts the number of colours that each player has currently won."""
        player1_collected = np.fromiter(self.players[0].collected_by_colour.values(), dtype=int)
        player2_collected = np.fromiter(self.players[1].collected_by_colour.values(), dtype=int)

        player_1_win_count = np.count_nonzero(player1_collected > self.num_pieces // 2)
        player_2_win_count = np.count_nonzero(player2_collected > self.num_pieces // 2)

        return player_1_win_count, player_2_win_count


    def determine_winner(self) -> Player:
        """Determine the winner of the game based on collected pieces.

        Returns:
            Player: The winning player
        """
        player_1_win_count, player_2_win_count = self.count_collected_colour_wins()

        if player_1_win_count > player_2_win_count:
            return self.players[0]
        else:
            return self.players[1]

    def game_inner_step(self, event: Optional[pygame.event.Event] = None) -> bool:
        """
        Process a single step of game logic.

        Args:
            event: (Optional[pygame.event.Event]): Optional Pygame event to process

        Returns:
            bool: True if the game is over, False otherwise
        """
        if self.game_phase == "game_over":
            return True
        elif self.game_phase == "end_game":
            self.collect_end_game_pieces()
            self.game_phase = "game_over"
        else:
            if event:
                self.handle_click(event.pos)
            else:
                self.handle_click()
        return False

    def get_valid_token_placements(self, selected_pieces: List[Piece], resolution: int = 100) -> List[Tuple[float, float]]:
        """
        Returns a list of normalized coordinates where tokens can be validly placed.

        Args:
            selected_pieces(List[Piece]): List of two selected pieces to connect
            resolution (int): The number of points along the line to sample

        Returns:
            List[Tuple[float, float]]: List of normalized (x,y) coordinates where tokens can be placed
        """
        valid_placements = []

        if len(selected_pieces) != 2:
            return valid_placements

        # Sample points along the line between selected pieces
        start, end = selected_pieces
        dx = end.x - start.x
        dy = end.y - start.y
        # distance = math.sqrt(dx * dx + dy * dy)

        # Sample 101 points along the line
        for t in np.linspace(0, 1, resolution):
            x = start.x + t * dx
            y = start.y + t * dy

            if self.check_token_placement(x, y, selected_pieces):
                # Normalize coordinates
                valid_placements.append(self.normalize_coordinates((x, y)))

        return valid_placements

    def generate_pieces(self) -> List[Piece]:
        """
        Generate and return a list of randomly placed game pieces.

        Creates self.num_pieces pieces for each colour in self.num_colours, ensuring no pieces overlap
        and all pieces are within the board boundaries.

        Returns:
            List[Piece]: List of randomly placed game pieces
        """
        pieces = []
        center_x = self.window_size[0] // 2
        center_y = self.window_size[1] // 2

        for colour_index in range(self.num_colours):
            for _ in range(self.num_pieces):
                while True:
                    angle = random.uniform(0, 2 * math.pi)
                    radius = random.uniform(0, self.board_radius - self.piece_radius)
                    x = center_x + radius * math.cos(angle)
                    y = center_y + radius * math.sin(angle)

                    new_piece = Piece(x, y, self.piece_colours[colour_index], colour_index, self.piece_radius)
                    overlaps = any(new_piece.overlaps(existing_piece) for existing_piece in pieces)

                    if not overlaps:
                        pieces.append(new_piece)
                        break

        return pieces

    def check_line_intersection(self, start: Piece, end: Piece, selected_pieces: List[Piece]) -> bool:
        """
        Check if a line between two pieces intersects with any other pieces or tokens.

        Args:
            start (Piece): Starting piece for the line
            end (Piece): Ending piece for the line
            selected_pieces (List[Piece]): List of pieces to exclude from intersection check (i.e., the start and end
                pieces)

        Returns:
            bool: True if there's an intersection, False otherwise
        """
        for piece in self.pieces:
            if piece in selected_pieces:
                continue
            x, y = self.get_point_on_line(start, end, (piece.x, piece.y))
            dx = x - piece.x
            dy = y - piece.y
            distance = math.sqrt(dx * dx + dy * dy)

            if distance < self.piece_radius:
                return True

        # Check intersection with player tokens
        for player in self.players:
            for token in player.placed_tokens:
                x, y = self.get_point_on_line(start, end, (token.x, token.y))
                dx = x - token.x
                dy = y - token.y
                distance = math.sqrt(dx * dx + dy * dy)

                if distance < self.effective_player_token_radius:
                    return True

        return False

    def create_player(self, colour: Tuple[int, int, int], name: str, player_type: PlayerType, bot_class: Optional['Bot'] = None) -> Player:
        """
        Create a new player with the specified parameters.

        Args:
            colour (Tuple[int, int, int]): RGB colour tuple for the player pieces
            name (str): Player's name
            player_type (PlayerType): Type of player (HUMAN or AI)
            bot_class (Optional[Bot]): AI bot class for AI players

        Returns:
            Player: Newly created Player object

        """
        return Player(colour, name, player_type, self.player_token_border_colour, self.player_token_radius,
                      self.player_token_border_width, self.num_player_tokens, self.num_colours, bot_class=bot_class)

    def draw_line_between_pieces(self, start: Piece, end: Piece, colour: Tuple[int, int, int, int] = (100, 100, 100, 100), width: int = 2) -> None:
        """
        Draw a line between two pieces on the screen.

        Args:
            start (Piece): Starting piece
            end (Piece): Ending piece
            colour (Tuple[int, int, int, int]): RGBA colour tuple for the line
            width (int): Width of the line in pixels
        """
        pygame.draw.line(self.screen, colour, (start.x, start.y), (end.x, end.y), width)

    def get_point_on_line(self, start: Piece, end: Piece, point: Tuple[float, float]) -> Tuple[float, float]:
        """
        Get the closest point on a line between two pieces to a given point.

        Args:
            start (Piece): Starting piece defining the line
            end (Piece): Ending piece defining the line
            point (Tuple[float, float]): Point to find the closest position to. An (x, y) tuple.

        Returns:
            Tuple[float, float]: (x, y) coordinates of the closest point on the line
        """
        x1, y1 = start.x, start.y
        x2, y2 = end.x, end.y
        x3, y3 = point

        px = x2 - x1
        py = y2 - y1
        u = ((x3 - x1) * px + (y3 - y1) * py) / (px * px + py * py)

        if u > 1:
            u = 1
        elif u < 0:
            u = 0

        x = x1 + u * px
        y = y1 + u * py

        return x, y
