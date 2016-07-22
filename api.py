import endpoints
from protorpc import remote, messages
from google.appengine.api import memcache
from google.appengine.api import taskqueue


@endpoints.api(name='hangman', version='v1')
class HangmanApi(remote.Service):
    """Hangman Game API"""
    pass




api = endpoints.api_server([HangmanApi])
