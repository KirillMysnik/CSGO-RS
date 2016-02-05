from entities.hooks import EntityCondition, EntityPreHook
from memory import make_object
from players import UserCmd
from players.constants import PlayerButtons


@EntityPreHook(EntityCondition.is_human_player, 'run_command')
def pre_player_run_command(stack_data):
    usercmd = make_object(UserCmd, stack_data[1])

    usercmd.buttons &= ~PlayerButtons.JUMP
