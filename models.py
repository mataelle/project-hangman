import random
from datetime import date
from protorpc import messages
import protorpc
from google.appengine.ext import ndb


class User(ndb.Model):
    """User profile"""
    name = ndb.StringProperty(required=True)
    email = ndb.StringProperty()
    win = ndb.IntegerProperty(required=True, default=0)
    loss = ndb.IntegerProperty(required=True, default=0)
    win_loss_ratio = ndb.FloatProperty(required=True, default=0)


class Game(ndb.Model):
    """Game object"""
    target_word = ndb.StringProperty(required=True)
    word_status = ndb.StringProperty(required=True)
    attempts_allowed = ndb.IntegerProperty(required=True, default=6)
    attempts_remaining = ndb.IntegerProperty(required=True, default=6)
    current_move_number = ndb.IntegerProperty(required=True, default=0)
    game_over = ndb.BooleanProperty(required=True, default=False)
    game_cancel = ndb.BooleanProperty(required=True, default=False)
    user = ndb.KeyProperty(required=True, kind='User')

    @classmethod
    def new_game(cls, user, attempts=6):
        """Creates and returns a new game"""
        words = open('list_of_words.txt', 'r').read().split('\n')
        target_word = words[random.choice(range(len(words) + 1))]

        game = cls(user=user,
                   target_word=target_word,
                   word_status=''.join('-' for i in range(len(target_word))),
                   attempts_allowed=attempts,
                   attempts_remaining=attempts,
                   parent=user)
        game.put()
        return game

    def to_form(self, message):
        """Returns a GameForm representation of the Game"""
        form = GameForm()
        form.urlsafe_key = self.key.urlsafe()
        form.user_name = self.user.get().name
        form.attempts_remaining = self.attempts_remaining
        form.game_over = self.game_over
        form.word_status = self.word_status
        form.message = message
        return form

    def end_game(self, won=False):
        """Ends the game - if won is True, the player won. - if won is False,
        the player lost."""
        self.game_over = True
        self.put()
        user = self.user.get()
        if won:
            user.win += 1
        else:
            user.loss += 1
        user.win_loss_ratio = 1. * user.win / \
            (user.loss if user.loss > 0 else 1)
        user.put()
        # Add the game to the score 'board'
        score = Score(user=self.user, date=date.today(), won=won,
                      misses=self.attempts_remaining - self.attempts_allowed)
        score.put()

    def cancel_game(self):
        """Cancel game"""
        if not self.game_over:
            self.game_over = True
            self.game_cancel = True
            self.put()


class Score(ndb.Model):
    """Score object"""
    user = ndb.KeyProperty(required=True, kind='User')
    date = ndb.DateProperty(required=True)
    won = ndb.BooleanProperty(required=True)
    misses = ndb.IntegerProperty(required=True)

    def to_form(self):
        return ScoreForm(user_name=self.user.get().name, won=self.won,
                         date=str(self.date), misses=-self.misses)


class Move(ndb.Model):
    """Move object"""
    move_id = ndb.IntegerProperty(required=True)
    game = ndb.KeyProperty(required=True, kind='Game')
    guess = ndb.StringProperty(required=True)
    word_status = ndb.StringProperty(required=True)
    verdict = ndb.BooleanProperty(required=True)


class GameForm(messages.Message):
    """GameForm for outbound game state information"""
    urlsafe_key = messages.StringField(1, required=True)
    attempts_remaining = messages.IntegerField(2, required=True)
    word_status = messages.StringField(4, required=True)
    game_over = messages.BooleanField(5, required=True)
    message = messages.StringField(6, required=True)
    user_name = messages.StringField(7, required=True)


class GamesForm(messages.Message):
    """To return all user games"""
    games = messages.MessageField(GameForm, 1, repeated=True)


class MoveForm(messages.Message):
    """To return move"""
    id = messages.IntegerField(1, required=True)
    guess = messages.StringField(2, required=True)
    verdict = messages.StringField(3, required=True)


class GameHistory(messages.Message):
    """To return history of game"""
    moves = messages.MessageField(MoveForm, 1, repeated=True)
    current_status = messages.StringField(2, required=True)


class NewGameForm(messages.Message):
    """Used to create a new game"""
    user_name = messages.StringField(1, required=True)
    attempts = messages.IntegerField(2, default=6)


class MakeMoveForm(messages.Message):
    """Used to make a move in an existing game"""
    guess = messages.StringField(1, required=True)


class UserRankForm(messages.Message):
    """Used to return ranked users"""
    user_name = messages.StringField(1, required=True)
    win_loss_ratio = messages.FloatField(2, required=True)


class UserRanksForm(messages.Message):
    """Returns multiple user ranks"""
    users = messages.MessageField(UserRankForm, 1, repeated=True)


class ScoreForm(messages.Message):
    """ScoreForm for outbound Score information"""
    user_name = messages.StringField(1, required=True)
    date = messages.StringField(2, required=True)
    won = messages.BooleanField(3, required=True)
    misses = messages.IntegerField(4, required=True)


class ScoreForms(messages.Message):
    """Return multiple ScoreForms"""
    items = messages.MessageField(ScoreForm, 1, repeated=True)


class StringMessage(messages.Message):
    """StringMessage-- outbound (single) string message"""
    message = messages.StringField(1, required=True)
