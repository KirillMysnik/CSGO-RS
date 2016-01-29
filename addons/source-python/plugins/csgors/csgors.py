from events import Event
from filters.players import PlayerIter
from listeners import OnClientActive
from listeners import OnLevelInit
from paths import CFG_PATH
from players.entity import Player
from players.helpers import index_from_userid
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
        self._callbacks_on_userid_unregistered = []

    def create(self, player):
        self[player.userid] = player
        for callback in self._callbacks_on_player_registered:
            callback(player)

    def delete_by_userid(self, userid):
        del self[userid]
        for callback in self._callbacks_on_userid_unregistered:
            callback(userid)

    def register_player_registered_callback(self, callback):
        self._callbacks_on_player_registered.append(callback)

    def unregister_player_registered_callback(self, callback):
        self._callbacks_on_player_registered.remove(callback)

    def register_userid_unregistered_callback(self, callback):
        self._callbacks_on_userid_unregistered.append(callback)

    def unregister_userid_unregistered_callback(self, callback):
        self._callbacks_on_userid_unregistered.remove(callback)

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


class OnUseridUnregistered:
    def __init__(self, callback):
        self.callback = callback
        self.register()

    def __call__(self, *args, **kwargs):
        self.callback(*args, **kwargs)

    def register(self):
        player_manager.register_userid_unregistered_callback(self)

    def unregister(self):
        player_manager.unregister_userid_unregistered_callback(self)


def load():
    for player in PlayerIter():
        player_manager.create(player)


@OnClientActive
def listener_on_client_active(index):
    player = Player(index)
    player_manager.create(player)


@Event('player_disconnect')
def on_player_disconnect(game_event):
    player_manager.delete_by_userid(game_event.get_int('userid'))


@OnLevelInit
def listener_on_level_init(map_name):
    userids_to_delete = list(player_manager.keys())
    for userid in userids_to_delete:
        player_manager.delete_by_userid(userid)


from .modules import *