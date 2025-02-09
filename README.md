# What is Lacuna?
_"[Lacuna](https://www.cmyk.games/products/lacuna) is a game for 2 players about collecting flowers on a pond at night. Draw an imaginary line between two flowers, place your pawn, and collect both flowers. Win by collecting the most flowers in the most colors!"_

Lacuna is a wonderfully tactile game, and it greatly benefits from the weighty feel of its player tokens, stunning game mat, and beautiful pieces. The game shines in its ability to shift from casual to tense. From heated debates over whether there's an unobstructed line between pieces, to the players trying to keep their hands steady as they measure which token is fractionally closer to that one critical piece upon which the whole game will be decided.

This implementation of Lacuna spits in the face of all of the above. So, if you have the chance to play the real board game yourself, it cannot be recommended enough.

## The Rules of The Game
The rules of Lacuna can be read [here](https://drive.google.com/file/d/1YvaCmRYpXe0IMFNaYPqVYfQIytIa-hDK/view), or watched in [this 1-minute video](https://www.youtube.com/watch?v=c69xeb9GRDc).

## The Goal of LacunaBots
The purpose of this project is not simply to destroy everything that makes Lacuna wonderful. The goal is simple: **can we create a program that is good at Lacuna?**

# Setup
Create a virtual environment of your choice and install the libraries in requirements.txt. E.g.,
```
python -m venv lacuna_env
lacuna_env/Scripts/activate (or, for Windows: lacuna_env\Scripts\activate.bat)
pip install -r requirements.txt
```

# Usage
```run_game.py``` runs a single game of Lacuna between two players (human and/or AI, as defined in the players list).

```run_tournament.py``` runs a round-robin tournament of matches between all the given players. Each match consists of two games, one where each player goes first. A player needs to win both games to win the overall
match (if both players win one game each, the match is a draw).

# Creating a Bot
Bots should be a subclass of the "Bot" class (in bot_classes.py). They must implement a make_move function that takes in a "GameManager" object.
The make_move function should return a tuple (selected_pieces, token_position), where selected_pieces is a tuple containing references to the two selected pieces and token_position is the normalized position of where the player token should be placed.
## Useful Functions / Attributes
### GameManager.get_normalized_game_state()
Returns most of the information that a bot will need to make its moves, including: which pieces have an unobstructed line between them, the normalized coordinates of all pieces, and references to the piece objects. These are all grouped by colour. Additionally, it returns the normalized positions of player tokens, and the current piece capture counts for each player.
Refer to get_normalized_game_state()'s docstring for more details.

### GameManager.get_valid_token_placements()
Given (a list containing) two pieces, get_valid_token_placements() will return a list of normalized (x, y) coordinates of valid placements for a player token (on the line between the two given pieces). A "resolution" argument can also be supplied to set how many points along the line between the two pieces should be sampled.

### GameManager.unnormalize_coordinates() / GameManager.normalize_coordinates()
Convert between normalised and unnormalized (pixel space) coordinates.

### GameManager.current_player_index
Returns which player (0 or 1) is the current active player.

### GameManager.num_colours
Returns the number of different colours being used in the game (default of 7).

### GameManager.num_pieces
Returns the number of pieces of each colour that are being used in the game (default of 7).