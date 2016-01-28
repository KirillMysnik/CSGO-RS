from engines.sound import Sound
from events.hooks import EventAction
from events.hooks import PreEvent

from ...csgors import player_manager


SOUND_WIN_CT = None
SOUND_WIN_T = None


@PreEvent('round_end')
def on_round_end(game_event):
    winner = game_event.get_int('winner')
    if winner == 2:
        if SOUND_WIN_T is not None:
            SOUND_WIN_T.play(
                *[player.index for player in player_manager.values()])

        return EventAction.STOP_BROADCAST

    elif winner == 3:
        if SOUND_WIN_CT is not None:
            SOUND_WIN_CT.play(
                *[player.index for player in player_manager.values()])

        return EventAction.STOP_BROADCAST

    return EventAction.CONTINUE
