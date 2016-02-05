from engines.sound import Sound
from entities.hooks import EntityCondition, EntityPreHook
from events import Event
from listeners import OnTick
from memory import make_object
from players import UserCmd
from players.constants import PlayerButtons
from players.helpers import userid_from_index
from players.helpers import userid_from_pointer

from ...csgors import OnPlayerRegistered
from ...csgors import OnUseridUnregistered

from .stamina import player_manager as stamina_player_manager
from .stamina import StaminaConsumers


SPRINT_START_SOUND = Sound('player/suit_sprint.wav')
LOW_STAMINA_SOUND = Sound('player/suit_denydevice.wav')
DEFAULT_PLAYER_SPEED = 0.6
SPRINTING_PLAYER_SPEED = 1.75
AIRBORNE_PLAYER_SPEED = 1
DEFAULT_PLAYER_GRAVITY = 1.2


class SprintingPlayer:
    def __init__(self, player):
        self.player = player

        self.sprinting = False
        self.key_pressed = False
        self.speed = 0

        player.gravity = DEFAULT_PLAYER_GRAVITY

    def ensure_speed(self, speed):
        if self.speed != speed:
            self.speed = speed
            self.player.speed = speed


class PlayerManager(dict):
    def create(self, player):
        self[player.userid] = SprintingPlayer(player)

    def delete_by_userid(self, userid):
        del self[userid]

    def get_by_index(self, index):
        userid = userid_from_index(index)
        return self.get(userid)


player_manager = PlayerManager()


@OnPlayerRegistered
def callback_on_player_registered(player):
    player_manager.create(player)


@OnUseridUnregistered
def callback_on_userid_unregistered(userid):
    player_manager.delete_by_userid(userid)


@EntityPreHook(EntityCondition.is_human_player, 'run_command')
def pre_player_run_command(stack_data):
    userid = userid_from_pointer(stack_data[0])
    stamina_player = stamina_player_manager[userid]

    if stamina_player.player.isdead:
        return

    sprinting_player = player_manager[userid]

    usercmd = make_object(UserCmd, stack_data[1])

    if usercmd.buttons & PlayerButtons.SPEED:
        if sprinting_player.key_pressed and sprinting_player.sprinting:
            if stamina_player.has_stamina_for(StaminaConsumers.SPRINT):
                stamina_player.consume(StaminaConsumers.SPRINT)
            else:
                sprinting_player.sprinting = False
                LOW_STAMINA_SOUND.play(sprinting_player.player.index)

        elif (not sprinting_player.key_pressed and
                  not sprinting_player.sprinting):

            sprinting_player.sprinting = True
            sprinting_player.key_pressed = True
            SPRINT_START_SOUND.play(sprinting_player.player.index)

    else:
        sprinting_player.key_pressed = False
        sprinting_player.sprinting = False


@OnTick
def listener_on_tick():
    for sprinting_player in player_manager.values():
        if sprinting_player.player.ground_entity == -1:
            sprinting_player.ensure_speed(AIRBORNE_PLAYER_SPEED)
        else:
            if sprinting_player.sprinting:
                sprinting_player.ensure_speed(SPRINTING_PLAYER_SPEED)
            else:
                sprinting_player.ensure_speed(DEFAULT_PLAYER_SPEED)


@Event('player_spawn')
def on_player_spawn(game_event):
    sprinting_player = player_manager[game_event.get_int('userid')]
    sprinting_player.speed = 0
