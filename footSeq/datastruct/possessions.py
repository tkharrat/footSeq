# AUTOGENERATED! DO NOT EDIT! File to edit: 01_2_possessions_data_structure.ipynb (unless otherwise specified).

__all__ = ['Event', 'Possession', 'PossessionMetadata', 'ActionValues']

# Cell

import datetime

import mongoengine
import pandas as pd
from fastcore.basics import *

from ..config.localconfig import CONFIG


class Event(mongoengine.EmbeddedDocument):
    "Event mapping class to store event info stored in the `sequence` field"

    ## events
    event_id = mongoengine.IntField(db_field="event_id")
    orig_event_id = mongoengine.StringField(db_field="eventId")

    ## player
    player_id = mongoengine.IntField(db_field="player_id", required=False)
    player_name = mongoengine.StringField(
        db_field="player_name", required=False, default="Unknown"
    )

    ## team
    team_id = mongoengine.IntField(db_field="team_id")
    team_name = mongoengine.StringField(db_field="team_name")

    ## possession
    possession_id = mongoengine.IntField(db_field="poss_id", required=True)
    possession_name = mongoengine.StringField(db_field="possession_name", required=True)
    possession_team_id = mongoengine.IntField(
        db_field="possession_team_id", required=True
    )
    possession_number = mongoengine.IntField(
        db_field="possession_number", required=True
    )
    seconds_since_poss = mongoengine.FloatField(
        db_field="seconds_since_poss", min_value=0.0, required=True
    )
    standart_name = mongoengine.StringField(db_field="standart_name", required=True)

    ## time
    period_id = mongoengine.IntField(
        db_field="period_id", required=True, min_value=1, max_value=2
    )
    time_seconds = mongoengine.FloatField(db_field="time_seconds", required=True)

    ## attack types
    attack_status_name = mongoengine.StringField(
        db_field="attack_status_name", required=True
    )
    attack_type_name = mongoengine.StringField(
        db_field="attack_type_name", required=True
    )
    attack_team_id = mongoengine.StringField(db_field="attack_team_id", required=True)

    ## actions
    action_id = mongoengine.IntField(db_field="action_id", required=True)
    type_name = mongoengine.StringField(db_field="type_name", required=True)
    result_id = mongoengine.IntField(
        db_field="result_id", required=True, min_value=-1, max_value=1
    )
    result_name = mongoengine.StringField(db_field="result_name", required=True)
    generic_action_type_id = mongoengine.IntField(
        db_field="generic_action_type_id", required=True
    )
    generic_action_type_name = mongoengine.StringField(
        db_field="generic_action_type_name", required=True
    )
    action_subtype_name = mongoengine.StringField(
        db_field="action_subtype_name", required=True
    )
    touches = mongoengine.StringField(db_field="touches", required=True)
    shot_type = mongoengine.StringField(db_field="shot_type", required=True)
    shot_handling = mongoengine.StringField(db_field="shot_handling", required=True)

    ## extra info
    under_pressure = mongoengine.BooleanField(db_field="under_pressure", required=True)
    high_speed = mongoengine.BooleanField(db_field="high_speed", required=True)
    body_name = mongoengine.StringField(
        db_field="body_name", required=False, default="Unknown"
    )

    ## we allow extra meters to adjust pitch coordinates
    start_x = mongoengine.FloatField(db_field="start_x", min_value=-1, max_value=107)
    start_y = mongoengine.FloatField(db_field="start_y", min_value=-1, max_value=70)
    end_x = mongoengine.FloatField(db_field="end_x", min_value=-1, max_value=107)
    end_y = mongoengine.FloatField(db_field="end_y", min_value=-1, max_value=70)

    ## goal gate
    gate_x = mongoengine.FloatField(db_field="gate_x", required=False)
    gate_y = mongoengine.FloatField(db_field="gate_y", required=False)

    ## opponent
    opponent_position_id = mongoengine.IntField(
        db_field="opponent_position_id", required=False
    )
    opponent_id = mongoengine.IntField(db_field="opponent_id", required=False)
    opponent_team_name = mongoengine.StringField(
        db_field="opponent_team_name", required=False
    )
    opponent_team_id = mongoengine.IntField(db_field="opponent_team_id", required=False)
    opponent_name = mongoengine.StringField(db_field="opponent_name", required=False)

    ## binary flags
    is_poss_team = mongoengine.BooleanField(db_field="is_poss_team", required=True)
    is_att_team = mongoengine.BooleanField(db_field="is_att_team", required=True)


def _convert_event(eve: Event):
    return pd.DataFrame({x: eve[x] for x in eve}, index=[0])

# Cell


class Possession(mongoengine.Document):
    """
    Store the `Possession` document info

    Attributes
    ----------
    _id : str
        unique document identifier
    gameId : int
        game-identifier
    possNumber : int
        possession number
    target : str
        whether the possession ended up in a `goal` or `no-goal`
    "sequence": List[Event]
        list of event information

    """

    game_id = mongoengine.IntField(db_field="gameId", required=True)
    possession_number = mongoengine.IntField(db_field="possNumber", required=True)
    target = mongoengine.StringField(db_field="target", choices=("goal", "no-goal"))
    sequence = mongoengine.EmbeddedDocumentListField(Event)

    meta = {
        "db_alias": "inStat",
        "collection": CONFIG["connections"]["inStat"]["possessions"],
    }

    def _format_poss(_raw_obj):
        return pd.DataFrame(
            {
                "gameId": _raw_obj.game_id,
                "possessionNumber": _raw_obj.possession_number,
                "target": _raw_obj.target,
                "sequence": listify(
                    pd.concat([_convert_event(eve) for eve in _raw_obj.sequence])
                    .reset_index(drop=True)
                    .sort_values(["period_id", "time_seconds"])
                ),
            },
            index=[0],
        )

    @classmethod
    def get_game_poss(cls, gm_id: int, poss_nbr: int) -> pd.DataFrame:
        "extract information for a given possession in a game"
        return cls._format_poss(
            cls.objects(game_id=gm_id, possession_number=poss_nbr).first()
        )

    @classmethod
    def get_all_game_poss(cls, gm_id: int):
        "extract all possessions for a game"
        return (
            pd.concat(
                [cls._format_poss(_raw_obj) for _raw_obj in cls.objects(game_id=gm_id)]
            )
            .reset_index(drop=True)
            .sort_values(["possessionNumber"])
        )

# Cell


class PossessionMetadata(mongoengine.Document):
    """
    Store the `Possession` metadata document info

    Attributes
    ----------
    _id : str
        unique document identifier which is the same as the potential file name
    actionEnd, actionStart: int
        event id marking the start and end of the sequence
    gameId : int
        game-identifier
    possessionNumber : int
        possession number
    target : str
        whether the possession ended up in a `goal` or `no-goal`
    nSeq: int
        total number of time steps in the sequence
    attackType: str
        attack type label
    standartName: str
        playing type label

    """

    game_id = mongoengine.IntField(db_field="gameId", required=True)
    target = mongoengine.StringField(db_field="target", choices=("goal", "no-goal"))
    action_start = mongoengine.IntField(db_field="actionStart", required=True)
    action_end = mongoengine.IntField(db_field="actionEnd", required=True)

    n_seq = mongoengine.IntField(db_field="nSeq", required=True)

    possession_number = mongoengine.IntField(db_field="possessionNumber", required=True)
    attack_type = mongoengine.StringField(db_field="attackType")
    standart_name = mongoengine.StringField(db_field="standartName")

    file_id = mongoengine.StringField(db_field="_id", primary_key=True)

    meta = {
        "db_alias": "inStat",
        "collection": CONFIG["connections"]["inStat"]["possessionMeta"],
    }

    @classmethod
    def get_poss_meta(cls, n_total=None, **kwargs) -> pd.DataFrame:
        "extract information for all possessions in a game"
        if n_total is None:
            docs = cls.objects(**kwargs)
        else:
            docs = cls.objects(**kwargs).limit(n_total)

        return (
            pd.concat(
                [pd.DataFrame({x: obj[x] for x in obj}, index=[0]) for obj in docs]
            )
            .reset_index(drop=True)
            .sort_values(["possession_number", "action_start", "action_end"])
        )

# Cell


class ActionValues(mongoengine.Document):
    "Store the `ActionValue` document"
    ## event
    event_id = mongoengine.IntField(db_field="id")
    orig_event_id = mongoengine.StringField(db_field="eventId", primary_key=True)

    ## player
    player_id = mongoengine.IntField(db_field="player_id", required=False)
    player_name = mongoengine.StringField(
        db_field="player_name", required=False, default="Unknown"
    )

    ## opponent
    opponent_position_id = mongoengine.IntField(
        db_field="opponent_position_id", required=False
    )
    opponent_id = mongoengine.IntField(db_field="opponent_id", required=False)
    opponent_team_name = mongoengine.StringField(
        db_field="opponent_team_name", required=False
    )
    opponent_team_id = mongoengine.IntField(db_field="opponent_team_id", required=False)
    opponent_name = mongoengine.StringField(db_field="opponent_name", required=False)

    ## team
    team_id = mongoengine.IntField(db_field="team_id")
    team_name = mongoengine.StringField(db_field="team_name")

    ## possession
    possession_id = mongoengine.IntField(db_field="poss_id", required=True)
    possession_name = mongoengine.StringField(db_field="possession_name", required=True)
    possession_team_id = mongoengine.IntField(
        db_field="possession_team_id", required=True
    )
    possession_number = mongoengine.IntField(
        db_field="possession_number", required=True
    )
    seconds_since_poss = mongoengine.FloatField(
        db_field="seconds_since_poss", min_value=0.0, required=True
    )
    standart_name = mongoengine.StringField(db_field="standart_name", required=True)

    ## timing
    period_id = mongoengine.IntField(
        db_field="period_id", required=True, min_value=1, max_value=2
    )
    time_seconds = mongoengine.FloatField(db_field="time_seconds", required=True)
    minutes = mongoengine.IntField(
        db_field="min", required=True, min_value=0, max_value=130
    )
    sec = mongoengine.IntField(db_field="sec", required=True, min_value=0, max_value=59)

    ## attack
    attack_status_name = mongoengine.StringField(
        db_field="attack_status_name", required=True
    )
    attack_type_name = mongoengine.StringField(
        db_field="attack_type_name", required=True
    )
    attack_team_id = mongoengine.StringField(db_field="attack_team_id", required=True)

    ## actions
    action_id = mongoengine.IntField(db_field="action_id", required=True)
    type_name = mongoengine.StringField(db_field="type_name", required=True)
    result_id = mongoengine.IntField(
        db_field="result_id", required=True, min_value=-1, max_value=1
    )
    result_name = mongoengine.StringField(db_field="result_name", required=True)
    generic_action_type_id = mongoengine.IntField(
        db_field="generic_action_type_id", required=True
    )
    generic_action_type_name = mongoengine.StringField(
        db_field="generic_action_type_name", required=True
    )
    action_subtype_name = mongoengine.StringField(
        db_field="action_subtype_name", required=True
    )

    under_pressure = mongoengine.BooleanField(db_field="under_pressure", required=True)
    high_speed = mongoengine.BooleanField(db_field="high_speed", required=True)

    ## we allow extra meters to adjust pitch coordinates
    start_x = mongoengine.FloatField(db_field="start_x", min_value=-1, max_value=107)
    start_y = mongoengine.FloatField(db_field="start_y", min_value=-1, max_value=70)
    end_x = mongoengine.FloatField(db_field="end_x", min_value=-1, max_value=107)
    end_y = mongoengine.FloatField(db_field="end_y", min_value=-1, max_value=70)

    gate_x = mongoengine.FloatField(db_field="gate_x", required=False)
    gate_y = mongoengine.FloatField(db_field="gate_y", required=False)

    body_name = mongoengine.StringField(
        db_field="body_name", required=False, default="Unknown"
    )
    is_poss_team = mongoengine.BooleanField(db_field="is_poss_team", required=True)
    is_att_team = mongoengine.BooleanField(db_field="is_att_team", required=True)

    ## optional
    touches = mongoengine.StringField(db_field="touches", required=False)
    shot_type = mongoengine.StringField(db_field="shot_type", required=False)
    shot_handling = mongoengine.StringField(db_field="shot_handling", required=False)

    ## extra fields computed
    action_reference = mongoengine.StringField(
        db_field="action_reference", required=False
    )

    proba_goal = mongoengine.FloatField(
        db_field="proba_goal", required=True, min_value=0.0, max_value=1.0
    )
    proba_none = mongoengine.FloatField(
        db_field="proba_none", required=True, min_value=0.0, max_value=1.0
    )
    action_value = mongoengine.FloatField(
        db_field="action_value", required=False, min_value=-1.0, max_value=1.0
    )

    game_id = mongoengine.IntField(db_field="gameId", required=True)
    target = mongoengine.StringField(
        db_field="target", required=True, choices=("goal", "no-goal")
    )

    meta = {
        "db_alias": "inStat",
        "collection": CONFIG["connections"]["inStat"]["actionValues"],
    }