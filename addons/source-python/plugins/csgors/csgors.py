from filters.players import PlayerIter
from listeners import OnClientActive
from listeners import OnClientDisconnect
from listeners import OnLevelInit
from paths import CFG_PATH
from players.entity import Player
from stringtables.downloads import Downloadables

from .info import info


DOWNLOADLIST = CFG_PATH / info.basename / "downloadlist.txt"


def load_downloadables(filepath):
    downloadables = Downloadables()

    with open(filepath) as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            downloadables.add(line)

    return downloadables

downloadables_global = load_downloadables(DOWNLOADLIST)


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


@OnLevelInit
def listener_on_level_init(map_name):
    players_to_delete = []
    for managed_player in player_manager.values():
        players_to_delete.append(managed_player.player)

    for player in players_to_delete:
        player_manager.delete(player)


from .modules import *