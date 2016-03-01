from random import choice
from time import time

from engines.server import global_vars
from engines.sound import Sound
from entities.constants import INVALID_ENTITY_INTHANDLE
from entities.entity import Entity
from entities.helpers import index_from_inthandle
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
STEP_SOUNDS = [
    'npc/combine_soldier/gear1.wav',
    'npc/combine_soldier/gear2.wav',
    'npc/combine_soldier/gear3.wav',
    'npc/combine_soldier/gear4.wav',
    'npc/combine_soldier/gear5.wav',
    'npc/combine_soldier/gear6.wav',
]
STEP_SOUND_INTERVAL = 0.3
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
        self.last_step = 0

        self._step_sounds = []
        for sound_path in STEP_SOUNDS:
            self._step_sounds.append(Sound(sound_path, player.index))

        player.gravity = DEFAULT_PLAYER_GRAVITY

    def ensure_speed(self, speed):
        if self.speed != speed:
            self.speed = speed
            self.player.speed = speed

    def step(self):
        cur_step = time()
        if cur_step - self.last_step >= STEP_SOUND_INTERVAL:
            choice(self._step_sounds).play()
            self.last_step = cur_step


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

                # Consume stamina
                stamina_player.consume(StaminaConsumers.SPRINT)

                # Cancel attacking
                usercmd.buttons &= ~PlayerButtons.ATTACK
                usercmd.buttons &= ~PlayerButtons.ATTACK2

                # Step sound
                sprinting_player.step()

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

        if sprinting_player.sprinting:
            inthandle = sprinting_player.player.active_weapon
            if inthandle == INVALID_ENTITY_INTHANDLE:
                continue

            entity = Entity(index_from_inthandle(inthandle))
            entity.next_attack = global_vars.current_time + 1
            entity.next_secondary_fire_attack = global_vars.current_time + 1


@Event('player_spawn')
def on_player_spawn(game_event):
    sprinting_player = player_manager[game_event.get_int('userid')]
    sprinting_player.speed = 0
