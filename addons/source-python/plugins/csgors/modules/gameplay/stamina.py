from colors import Color
from events import Event
from listeners import OnTick
from messages import HudMsg
from players.helpers import userid_from_index

from ...csgors import OnPlayerRegistered
from ...csgors import OnUseridUnregistered


INITIAL_STAMINA = 500
STAMINA_RESTORATION_RATE = 1
FAIL_JUMP_FORCE = -64

USE_OVERLAY = True
OVERLAY_PATH = "overlays/csgors/stamina-{}"

STAMINA_MSG_COLOR = Color(255, 206, 60)
STAMINA_MSG_X = 0.01
STAMINA_MSG_Y = 0.90
STAMINA_MSG_EFFECT = 0
STAMINA_MSG_FADEIN = 0
STAMINA_MSG_FADEOUT = 0
STAMINA_MSG_HOLDTIME = 5
STAMINA_MSG_FXTIME = 0
STAMINA_MSG_CHANNEL = 1
HUD_STRINGS = [
    "▯▯▯▯▯▯▯▯▯▯",
    "▮▯▯▯▯▯▯▯▯▯",
    "▮▮▯▯▯▯▯▯▯▯",
    "▮▮▮▯▯▯▯▯▯▯",
    "▮▮▮▮▯▯▯▯▯▯",
    "▮▮▮▮▮▯▯▯▯▯",
    "▮▮▮▮▮▮▯▯▯▯",
    "▮▮▮▮▮▮▮▯▯▯",
    "▮▮▮▮▮▮▮▮▯▯",
    "▮▮▮▮▮▮▮▮▮▯",
    "▮▮▮▮▮▮▮▮▮▮",
]


class StaminaConsumers:
    SPRINT = 2
    JUMP = 100


class StaminaPlayer:
    def __init__(self, player):
        self.player = player
        self.stamina = INITIAL_STAMINA
        self.stamina_ratio = 10

    def has_stamina_for(self, consumer):
        return self.stamina >= consumer

    def consume(self, consumer):
        self.stamina -= consumer

        self.hud_check()

    def empty(self):
        self.stamina = 0
        self.hud_check()

    def refill(self):
        self.stamina = INITIAL_STAMINA
        self.hud_check()

    def restore(self):
        if self.stamina < INITIAL_STAMINA:
            self.stamina = min(
                INITIAL_STAMINA, self.stamina + STAMINA_RESTORATION_RATE)

            self.hud_check()

    def hud_check(self):
        new_ratio = int((self.stamina / INITIAL_STAMINA) * 10)
        if new_ratio == self.stamina_ratio:
            return

        self.stamina_ratio = new_ratio

        if USE_OVERLAY:
            self.player.client_command(
                'r_screenoverlay {}'.format(OVERLAY_PATH.format(new_ratio)))

        else:
            hud_msg = HudMsg(
                HUD_STRINGS[new_ratio],
                color1=STAMINA_MSG_COLOR,
                x=STAMINA_MSG_X,
                y=STAMINA_MSG_Y,
                effect=STAMINA_MSG_EFFECT,
                fade_in=STAMINA_MSG_FADEIN,
                fade_out=STAMINA_MSG_FADEOUT,
                hold_time=STAMINA_MSG_HOLDTIME,
                fx_time=STAMINA_MSG_FXTIME,
                channel=STAMINA_MSG_CHANNEL
            )
            hud_msg.send(self.player.index)


class PlayerManager(dict):
    def create(self, player):
        self[player.userid] = StaminaPlayer(player)

    def delete_by_userid(self, userid):
        del self[userid]

    def get_by_index(self, index):
        userid = userid_from_index(index)
        return self.get(userid)


player_manager = PlayerManager()


@OnTick
def listener_on_tick():
    for stamina_player in player_manager.values():
        stamina_player.restore()


@OnPlayerRegistered
def callback_on_player_registered(player):
    player_manager.create(player)


@OnUseridUnregistered
def callback_on_userid_unregistered(userid):
    player_manager.delete_by_userid(userid)


@Event('player_jump')
def on_player_jump(game_event):
    stamina_player = player_manager.get(game_event.get_int('userid'))
    if stamina_player.has_stamina_for(StaminaConsumers.JUMP):
        stamina_player.consume(StaminaConsumers.JUMP)
    else:
        stamina_player.player.push(1, FAIL_JUMP_FORCE, vert_override=True)
        stamina_player.empty()


@Event('player_spawn')
def on_player_spawn(game_event):
    stamina_player = player_manager.get(game_event.get_int('userid'))
    stamina_player.refill()
