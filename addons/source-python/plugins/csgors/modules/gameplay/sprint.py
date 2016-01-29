from engines.sound import Sound
from entities.constants import INVALID_ENTITY_INTHANDLE
from entities.hooks import EntityCondition
from entities.hooks import EntityPreHook
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
DEFAULT_PLAYER_SPEED = 1.2
SPRINTING_PLAYER_SPEED = 1
AIRBORNE_PLAYER_SPEED = 0.8
DEFAULT_PLAYER_GRAVITY = 1.1


class SprintingPlayer:
    def __init__(self, player):
        self.player = player

        self.sprinting = False
        self.key_pressed = False

        player.gravity = DEFAULT_PLAYER_GRAVITY


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
                usercmd.buttons &= ~PlayerButtons.SPEED
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

        usercmd.buttons |= PlayerButtons.SPEED


@OnTick
def listener_on_tick():
    for sprinting_player in player_manager.values():
        if sprinting_player.player.ground_entity == INVALID_ENTITY_INTHANDLE:
            sprinting_player.player.speed = AIRBORNE_PLAYER_SPEED
        else:
            if sprinting_player.sprinting:
                sprinting_player.player.speed = SPRINTING_PLAYER_SPEED
            else:
                sprinting_player.player.speed = DEFAULT_PLAYER_SPEED
