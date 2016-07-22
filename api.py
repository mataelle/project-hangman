import endpoints
from protorpc import remote, messages
from google.appengine.api import memcache
from google.appengine.api import taskqueue

from models import User, Game, Move, Score
from models import (StringMessage, NewGameForm,
                    GameForm, GamesForm, MakeMoveForm,
                    GameHistory, MoveForm,
                    UserRanksForm, UserRankForm, ScoreForms)

from utils import get_by_urlsafe
from game import (make_guess, form_new_word_template,
                  check_if_win)


CREATE_USER_REQUEST = endpoints.ResourceContainer(
    user_name=messages.StringField(1),
    email=messages.StringField(2))

NEW_GAME_REQUEST = endpoints.ResourceContainer(NewGameForm)
GET_GAME_REQUEST = endpoints.ResourceContainer(
    urlsafe_game_key=messages.StringField(1))
CANCEL_GAME_REQUEST = endpoints.ResourceContainer(
    urlsafe_game_key=messages.StringField(1))
GET_GAME_HISTORY_REQUEST = endpoints.ResourceContainer(
    urlsafe_game_key=messages.StringField(1))

GET_USER_GAMES_REQUEST = endpoints.ResourceContainer(
    user_name=messages.StringField(1))

MAKE_MOVE_REQUEST = endpoints.ResourceContainer(
    MakeMoveForm,
    urlsafe_game_key=messages.StringField(1))

GET_HIGH_SCORES_REQUEST = endpoints.ResourceContainer(
    number_of_results=messages.IntegerField(1, required=False))


@endpoints.api(name='hangman', version='v1')
class HangmanApi(remote.Service):
    """Hangman Game API"""

    @endpoints.method(request_message=CREATE_USER_REQUEST,
                      response_message=StringMessage,
                      path='user',
                      name='create_user',
                      http_method='POST')
    def create_user(self, request):
        """Create a User. Requires a unique username"""
        if User.query(User.name == request.user_name).get():
            raise endpoints.ConflictException(
                'A User with that name already exists!')
        user = User(name=request.user_name, email=request.email)
        user.put()
        return StringMessage(message='User {} created!'.format(
            request.user_name))

    @endpoints.method(request_message=NEW_GAME_REQUEST,
                      response_message=GameForm,
                      path='game',
                      name='new_game',
                      http_method='POST')
    def new_game(self, request):
        """Creates new game"""
        user = User.query(User.name == request.user_name).get()
        if not user:
            raise endpoints.NotFoundException(
                'A User with that name does not exist!')
        game = Game.new_game(user.key, request.attempts)

        # Use a task queue to update the average attempts remaining.
        # This operation is not needed to complete the creation of a new game
        # so it is performed out of sequence.
        taskqueue.add(url='/tasks/cache_average_attempts')
        return game.to_form('Let\'s play!')

    @endpoints.method(request_message=CANCEL_GAME_REQUEST,
                      response_message=GameForm,
                      path='game/{urlsafe_game_key}/cancel',
                      name='cancel_game',
                      http_method='POST')
    def cancel_game(self, request):
        """Cancels game"""
        game = get_by_urlsafe(request.urlsafe_game_key, Game)
        if game:
            game.cancel_game()
            return game.to_form('Successfully cancelled!')
        else:
            raise endpoints.NotFoundException('Game not found!')

    @endpoints.method(request_message=GET_GAME_REQUEST,
                      response_message=GameForm,
                      path='game/{urlsafe_game_key}',
                      name='get_game',
                      http_method='GET')
    def get_game(self, request):
        """Return the current game state."""
        game = get_by_urlsafe(request.urlsafe_game_key, Game)
        if game:
            return game.to_form('Over' if game.game_over else 'Cancelled'
                                if game.game_cancel else 'Not over')
        else:
            raise endpoints.NotFoundException('Game not found!')

    @endpoints.method(request_message=GET_USER_GAMES_REQUEST,
                      response_message=GamesForm,
                      path='user/games',
                      name='user_games',
                      http_method='GET')
    def get_user_games(self, request):
        """Return games created by user."""
        user = User.query(User.name == request.user_name).get()
        if not user:
            raise endpoints.NotFoundException(
                'A User with that name does not exist!')
        games = Game.query(ancestor=user.key).fetch()
        response = GamesForm()
        response.games = [game.to_form('') for game in games]
        return response

    @endpoints.method(request_message=GET_GAME_HISTORY_REQUEST,
                      response_message=GameHistory,
                      path='game/{urlsafe_game_key}/history',
                      name='game_history',
                      http_method='GET')
    def get_game_history(self, request):
        """Return game history."""
        game = get_by_urlsafe(request.urlsafe_game_key, Game)
        if game:
            moves = Move.query(Move.game == game.key).order(
                Move.move_id).fetch()
            response = GameHistory()

            def createMoveForm(move):
                form = MoveForm()
                form.id = move.move_id
                form.guess = move.guess
                form.verdict = 'Guess' if move.verdict else 'Miss'
                return form

            response.moves = [createMoveForm(move) for move in moves]
            response.current_status = 'Over' if game.game_over else 'Cancelled' \
                if game.game_cancel else 'Not over'
            return response
        else:
            raise endpoints.NotFoundException('Game not found!')

    @endpoints.method(request_message=MAKE_MOVE_REQUEST,
                      response_message=GameForm,
                      path='game/{urlsafe_game_key}/move',
                      name='make_move',
                      http_method='POST')
    def make_move(self, request):
        """Makes a move. Returns a game state with message"""

        # different checks
        game = get_by_urlsafe(request.urlsafe_game_key, Game)
        if game.game_over:
            return game.to_form('Game already over!')
        if game.game_cancel:
            return game.to_form('Game cancelled.')
        guess = request.guess.lower()
        if len(guess) != 1 or not guess.isalpha():
            return game.to_form('Guess a letter.')
        if len(Move.query(Move.game == game.key, Move.guess == guess).fetch()) > 0:
            return game.to_form('Guess another letter.')

        # game logic checks
        verdict = make_guess(guess, game.target_word)
        if verdict:
            game.word_status = form_new_word_template(guess,
                                                      game.target_word,
                                                      game.word_status)
        else:
            game.attempts_remaining -= 1
        game.current_move_number += 1
        game.put()
        move = Move(game=game.key,
                    guess=guess,
                    move_id=game.current_move_number - 1,
                    word_status=game.word_status,
                    verdict=verdict)
        move.put()
        # output verdicts
        if verdict and check_if_win(game.word_status):
            game.end_game(True)
            return game.to_form('You win!')

        if game.attempts_remaining < 1:
            game.end_game(False)
            return game.to_form('Game over!')
        else:
            return game.to_form('Guess' if verdict else 'Miss')

    @endpoints.method(request_message=GET_HIGH_SCORES_REQUEST,
                      response_message=ScoreForms,
                      path='scores',
                      name='high_scores',
                      http_method='GET')
    def get_high_scores(self, request):
        """Return high scores"""
        scores = Score.query().order(-Score.misses)
        if request.number_of_results is not None \
                and request.number_of_results > 0:
            scores = scores.fetch(request.number_of_results)
        return ScoreForms(items=[score.to_form() for score in scores])

    @endpoints.method(response_message=UserRanksForm,
                      path='users/ranking',
                      name='user_ranking',
                      http_method='GET')
    def get_user_rankings(self, request):
        """Return ranked users"""
        users = User.query().order(-User.win_loss_ratio).fetch()

        def createUserRankForm(user):
            form = UserRankForm()
            form.user_name = user.name
            form.win_loss_ratio = user.win_loss_ratio
            return form

        return UserRanksForm(users=[createUserRankForm(user) for user in users])


api = endpoints.api_server([HangmanApi])
