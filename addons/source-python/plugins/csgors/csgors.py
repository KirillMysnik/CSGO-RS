from filters.players import PlayerIter
from listeners import OnClientActive
from listeners import OnClientDisconnect
from players.entity import Player


class PlayerManager(dict):
    def __init__(self):
        super().__init__()

        self._callbacks_on_player_registered = []
        self._callbacks_on_player_unregistered = []

    def create(self, player):
        self[player.userid] = player
        for callback in self._callbacks_on_player_registered:
            callback(player)

    def delete(self, player):
        del self[player.userid]
        for callback in self._callbacks_on_player_unregistered:
            callback(player)

    def register_player_registered_callback(self, callback):
        self._callbacks_on_player_registered.append(callback)

    def unregister_player_registered_callback(self, callback):
        self._callbacks_on_player_registered.remove(callback)

    def register_player_unregistered_callback(self, callback):
        self._callbacks_on_player_unregistered.append(callback)

    def unregister_player_unregistered_callback(self, callback):
        self._callbacks_on_player_unregistered.remove(callback)

player_manager = PlayerManager()


class OnPlayerRegistered:
    def __init__(self, callback):
        self.callback = callback
        self.register()

    def __call__(self, *args, **kwargs):
        self.callback(*args, **kwargs)

    def register(self):
        player_manager.register_player_registered_callback(self)

    def unregister(self):
        player_manager.unregister_player_registered_callback(self)


class OnPlayerUnregistered:
    def __init__(self, callback):
        self.callback = callback
        self.register()

    def __call__(self, *args, **kwargs):
        self.callback(*args, **kwargs)

    def register(self):
        player_manager.register_player_unregistered_callback(self)

    def unregister(self):
        player_manager.unregister_player_unregistered_callback(self)


def load():
    for player in PlayerIter():
        player_manager.create(player)


@OnClientActive
def listener_on_client_active(index):
    player = Player(index)
    player_manager.create(player)


@OnClientDisconnect
def listener_on_client_disconnect(index):
    player = Player(index)
    player_manager.delete(player)


from .modules import *