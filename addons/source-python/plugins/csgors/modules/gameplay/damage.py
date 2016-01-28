from entities import TakeDamageInfo
from entities.constants import DamageTypes
from entities.hooks import EntityCondition
from entities.hooks import EntityPreHook
from memory import make_object
from players.constants import HitGroup
from players.entity import Player


HEADSHOT_DMG_MULTIPLIER = 5     # Damage done to head
CHEST_DMG_MULTIPLIER = 2.5      # Damage done to chest or stomach
BASE_DMG_MULTIPLIER = 1.5       # Other hitgroups


@EntityPreHook(EntityCondition.is_player, 'on_take_damage')
def on_take_damage(args):
    info = make_object(TakeDamageInfo, args[1])
    if info.type & DamageTypes.HEADSHOT:
        info.damage *= HEADSHOT_DMG_MULTIPLIER

    else:
        victim = make_object(Player, args[0])
        if victim.hitgroup in (HitGroup.CHEST, HitGroup.STOMACH):
            info.damage *= CHEST_DMG_MULTIPLIER
        else:
            info.damage *= BASE_DMG_MULTIPLIER
