## Hangman endpoints

The word to guess is represented by a row of dashes, representing each letter of the word. In most variants, proper nouns, such as names, places, and brands, are not allowed. If the guessing player suggests a letter which occurs in the word, the other player writes it in all its correct positions. If the suggested letter or number does not occur in the word, the other player draws one element of a hanged man stick figure as a tally mark. [wikipedia](https://en.wikipedia.org/wiki/Hangman_(game))


## Set-Up Instructions:
1.  Update the value of application in app.yaml to the app ID you have registered
 in the App Engine admin console and would like to use to host your instance of this sample.
1.  To test API, you will have to launch google chrome using the console as follows:

 [path-to-Chrome] --user-data-dir=test --unsafely-treat-insecure-origin-as-secure=http://localhost:port

1.  Run the app with the devserver using dev_appserver.py DIR, and ensure it's
 running by visiting the API Explorer - by default localhost:8080/_ah/api/explorer.


##Endpoints Included:
 - **create_user**
    - Path: 'user'
    - Method: POST
    - Parameters: user_name, email (optional)
    - Returns: Message confirming creation of the User.
    - Description: Creates a new User. user_name provided must be unique. Will
    raise a ConflictException if a User with that user_name already exists.

 - **new_game**
    - Path: 'game'
    - Method: POST
    - Parameters: user_name, attempts(optional)
    - Returns: GameForm with initial game state.
    - Description: Creates a new Game. user_name provided must correspond to an
    existing user - will raise a NotFoundException if not. Min must be less than
    max. Also adds a task to a task queue to update the average moves remaining
    for active games.

 - **cancel_game**
    - Path: 'game/{urlsafe_game_key}/cancel'
    - Method: GET
    - Parameters: urlsafe_game_key
    - Returns: GameForm with current game state.
    - Description: Cancels a game. Returns the current state of a game.

 - **get_game**
    - Path: 'game/{urlsafe_game_key}'
    - Method: GET
    - Parameters: urlsafe_game_key
    - Returns: GameForm with current game state.
    - Description: Returns the current state of a game.

  - **get_user_games**
    - Path: 'user/games'
    - Method: GET
    - Parameters: user_name
    - Returns: GamesForm with all the games started by user. If user does not exist,
    NotFoundException is raised.
    - Description: Returns the list of games started by the user.

  - **get_game_history**
    - Path: 'game/{urlsafe_game_key}/history'
    - Method: GET
    - Parameters: urlsafe_game_key
    - Returns: GameHistory - form with all the moves made in the game and the current
    status.
    - Description: Returns the history of the game.

 - **make_move**
    - Path: 'game/{urlsafe_game_key}/move'
    - Method: POST
    - Parameters: urlsafe_game_key, guess
    - Returns: GameForm with new game state.
    - Description: Accepts a 'guess' and returns the updated state of the game.
    If this causes a game to end, a corresponding Score entity will be created.

 - **get_high_scores**
    - Path: 'scores'
    - Method: GET
    - Parameters: number_of_results(optional)
    - Returns: ScoreForms.
    - Description: Returns all Scores in the database if number_of_results is not given.
    In the other case returns top number_of_results.

 - **get_user_rankings**
    - Path: 'users/ranking'
    - Method: GET
    - Parameters: None
    - Returns: UserRanksForms.
    - Description: Returns users ranked by win/loss ratio.


##Models Included:
 - **User**
    - Stores unique user_name and (optional) email address.
    - Stores win count, loss count and their ratio.

 - **Game**
    - Stores unique game states. Associated with User model via KeyProperty.

 - **Move**
    - Records move. Associated with Game model via KeyProperty.

 - **Score**
    - Records completed games. Associated with Users model via KeyProperty.

##Forms Included:
 - **GameForm**
    - Representation of a Game's state (urlsafe_key, attempts_remaining,
    word_status, game_over flag, message, user_name).
 - **GamesForm**
    - Multiple GameForm container.
 - **MoveForm**
    - Representation of a Move (id, guess - character, verdict - 'Guess' or 'Miss').
 - **GameHistory**
    - Multiple MoveForm container and current game status - 'Over', 'Cancelled', 'Not over'
 - **NewGameForm**
    - Used to create a new game (user_name, min, max, attempts)
 - **MakeMoveForm**
    - Inbound make move form (guess).
- **UserRankForm**
    - Represents ranked user with user_name and win_loss_ratio.
- **UserRanksForm**
    - Multiple UserRankForm container.
 - **ScoreForm**
    - Representation of a completed game's Score (user_name, date, won flag,
    misses).
 - **ScoreForms**
    - Multiple ScoreForm container.
 - **StringMessage**
    - General purpose String container.