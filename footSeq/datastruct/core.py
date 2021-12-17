# AUTOGENERATED! DO NOT EDIT! File to edit: 01_1_seq_data_structure.ipynb (unless otherwise specified).

__all__ = ['SeqenceData', 'TargetData', 'FilesPath', 'Tfms', 'parse_file_info', 'pick_files', 'read_sequence_play',
           'get_sequence_len', 'goal_splitter', 'FootSeqTuple', 'FootSeqTransform', 'FootSeqToTensor', 'Pad_Seq',
           'pad_seq']

# Cell

import os
import pickle
import warnings
from pathlib import Path
from random import random, sample
from typing import List, Tuple

import numpy as np
import pandas as pd
from fastai.tabular.all import *
from fastai.text.all import *
from fastai.vision.all import *
from fastcore.basics import *
from fastcore.foundation import *
from fastcore.xtras import load_pickle, save_pickle
from progressbar import progressbar

from ..plots import plot_actions

SeqenceData = dict[str, pd.DataFrame]
TargetData = dict[str, str]
FilesPath = List[Path]
Tfms = List[Transform]

# Cell


def parse_file_info(file_path, sep="___") -> pd.DataFrame:
    "Parse file information from file-name"
    game_id, poss_nbr, start_id, end_id, target = file_path.stem.split(sep)
    _id = game_id + "_" + start_id + "-" + end_id
    dico = {
        "id": _id,
        "gameId": int(game_id),
        "possNumber": int(poss_nbr),
        "startId": int(start_id),
        "endId": int(end_id),
        "target": target,
        "file": file_path,
        "nSteps": pd.read_csv(file_path).shape[0],
    }
    return pd.DataFrame(dico, index=[0])

# Cell


def pick_files(
    files: FilesPath, goal_prop=0.95, no_goal_prop=0.05, sep="___"
) -> pd.DataFrame:
    """
    Loops over all files and select some for training  and leave the rest for testing

    Parameters
    ----------
    files: List[Path]
        list of all files path available
    goal_prop, no_goal_prop: float in [0, 1]
        proportion of goal and no-goal files to keep

    Returns
    -------
    dict:
        Dictionary with 3 keys:
            - `train_goals`: pd.DataFrame giving training files info with `goal` target
            - `test_goals`: pd.DataFrame giving test files info with `goal` target
            - `no_goals`: selection of files with `no-goal` target

    """
    train_goals = []
    test_goals = []
    no_goals = []

    for _file in progressbar(files):
        _, _, _, _, _target = _file.stem.split(sep)
        _random_toss = random.random()
        if _target == "goal":
            _file_info = parse_file_info(_file, sep)
            if _random_toss < goal_prop:
                train_goals.append(_file_info)
            else:
                test_goals.append(_file_info)
        else:
            if _random_toss < no_goal_prop:
                no_goals.append(parse_file_info(_file, sep))

    return (
        pd.concat(train_goals, axis=0).convert_dtypes().reset_index(drop=True),
        pd.concat(test_goals, axis=0).convert_dtypes().reset_index(drop=True),
        pd.concat(no_goals, axis=0).convert_dtypes().reset_index(drop=True),
    )

# Cell


def read_sequence_play(file):
    "Read a sequence of Playing"
    df = pd.read_csv(file)
    ## add a unique key to identify the events
    df["key"] = (
        df["_id"].str.split("___").map(lambda x: x[0])
        + "_"
        + df["event_id"].astype("str")
    )

    ## remove rows with NA on key columns + replace NA on other columns
    df = df.dropna(
        subset=[
            "team_id",
            "attack_team_id",
            "is_poss_team",
            "is_att_team",
            "start_x",
            "start_y",
        ]
    ).fillna({"possession_name": "Undefined"})

    return df


def get_sequence_len(file):
    return read_sequence_play(file).shape[0]

# Cell


def goal_splitter(
    files_info_df: pd.DataFrame,
    no_goal_prop: float = 1.5,
    valid_pct: float = 0.2,
    seed=None,
):
    "Create function that splits `files` between train/valid with `valid_pct` randomly"
    ## get goal indices
    goal_indices = L(files_info_df[files_info_df.target == "goal"].index.tolist())
    all_no_goal_indices = L(
        files_info_df[files_info_df.target != "goal"].index.tolist()
    )
    no_goal_indices = sample(all_no_goal_indices, int(len(goal_indices) * no_goal_prop))

    # now create validation index
    n_sample_goals = int(valid_pct * len(goal_indices))
    n_sample_no_goals = int(valid_pct * len(no_goal_indices))

    val_idx_goals = np.random.choice(
        goal_indices, size=n_sample_goals, replace=False
    ).tolist()
    val_idx_no_goals = np.random.choice(
        no_goal_indices, size=n_sample_no_goals, replace=False
    ).tolist()

    # compute the left indices
    train_goal_idx = [idx for idx in goal_indices if not idx in val_idx_goals]
    train_no_goal_idx = [idx for idx in no_goal_indices if not idx in val_idx_no_goals]

    return (
        L(train_goal_idx + train_no_goal_idx).unique().shuffle(),
        L(val_idx_goals + val_idx_no_goals).unique().shuffle(),
    )

# Cell


def _nice_time(row) -> str:
    minute = int((row.period_id - 1) * 45 + row.time_seconds // 60)
    second = int(row.time_seconds % 60)
    return f"{minute}m{second}s"


class FootSeqTuple(fastuple):
    def show(self, ctx=None, title=None, **kwargs):
        play_sequence, target = self
        ## remove na
        play_sequence.dropna(inplace=True)
        ## reduce size
        play_sequence = play_sequence.tail(10).copy()
        play_sequence["nice_time"] = play_sequence.apply(_nice_time, axis=1)
        labels = play_sequence[
            [
                "nice_time",
                "type_name",
                "player_name",
                "team_id",
                "result_name",
                "possession_name",
                "attack_type_name",
                "event_id",
            ]
        ]

        ctx = plot_actions(
            location=play_sequence[["start_x", "start_y", "end_x", "end_y"]],
            action_type=play_sequence.type_name,
            team=play_sequence.team_id,
            result=play_sequence.result_name,
            label=labels,
            labeltitle=[
                "time",
                "action",
                "player",
                "teamId",
                "result",
                "possession_type",
                "attack_type",
                "event_id",
            ],
            zoom=False,
            ax=ctx,
            return_fig=False,
            **kwargs,
        )
        if title is None:
            title = target
        ctx.set_title(title)

        return ctx

# Cell


@delegates(TabularPandas)
class FootSeqTransform(ItemTransform):
    """
    Produce a processed sequence of play and a target
    """

    def __init__(
        self,
        files: List[Path],
        splits: List[int] = None,
        labels: List[str] = None,
        procs: Tfms = None,
        cat_names: List[str] = None,
        cont_names: List[str] = None,
        **kwargs
    ):
        ## store different attributes
        store_attr(but="labels")

        self.train_files = self.files[splits[0]]
        self.valid_files = self.files[splits[1]]

        ## map target labels to integers
        self.target_vocab, self.target_o2i = uniqueify(labels, sort=True, bidir=True)

        ## store kwargs
        self.to_kwargs = kwargs

    def setups(self, items):

        ## keep only items from the training set
        setup_files = L(set(items) & set(self.train_files))

        ## compute dataframe used to create the tabularPandas
        self.setup_df = (
            pd.concat(
                [read_sequence_play(file) for file in progressbar(setup_files)], axis=0
            )
            .convert_dtypes()
            .drop_duplicates("key")
            .dropna()
            .drop(["key"], axis="columns")
            .reset_index(drop=True)
        )

        self.to = TabularPandas(
            df=self.setup_df,
            procs=self.procs,
            cat_names=self.cat_names,
            cont_names=self.cont_names,
            do_setup=True,
            **self.to_kwargs
        )

    def encodes(self, file: Path):
        to_tst = self.to.new(read_sequence_play(file))
        to_tst.process()
        return (
            to_tst.items,
            self.target_o2i[parse_file_info(file)["target"].values[0]],
        )

    def decodes(self, x):
        return FootSeqTuple(
            x[0].apply(self.to.decode_row, axis=1), self.target_vocab[x[1]]
        )

# Cell


class FootSeqToTensor(ItemTransform):
    "Transform Tuple of pd.DataFrame and integer to appropriate tensors. Note that the first dimension is only useful for decoding"
    order = 10

    def __init__(
        self,
        cat_names,
        cont_names,
        labels,
        base_path,
        feats_first=True,
        max_len=None,
        meta_col="_id",
        sep="___",
    ):
        store_attr(but="labels")
        self.target_vocab, self.target_o2i = uniqueify(labels, sort=True, bidir=True)

    def encodes(self, x):
        ## keep metadata columns
        df, tgt = x

        ## reduce sequence length is needed
        if (self.max_len is not None) and (type(self.max_len) == int):
            df = df.tail(self.max_len)

        all_cols = df.columns.tolist()
        value_cols = self.cat_names + self.cont_names
        self.meta_cols = [col for col in all_cols if not col in value_cols]

        ## prepare info for metadata
        gm_id, poss_number, start_id, end_id, _ = (
            df[self.meta_col].values[0].split(self.sep)
        )

        if self.feats_first:
            return (
                tensor(
                    [int(gm_id), int(poss_number), int(start_id), int(end_id)]
                ).long(),
                tensor(df[self.cat_names].values).long(),
                tensor(df[self.cont_names].values).float(),
                TensorCategory(tgt),
            )
        else:
            return (
                tensor(
                    [int(gm_id), int(poss_number), int(start_id), int(end_id)]
                ).long(),
                tensor(df[self.cat_names].values).long().transpose(1, 0),
                tensor(df[self.cont_names].values).float().transpose(1, 0),
                TensorCategory(tgt),
            )

    def decodes(self, x):
        meta, cats, conts, tgt = x
        if self.feats_first:
            cats_df = pd.DataFrame(cats.numpy(), columns=self.cat_names)
            conts_df = pd.DataFrame(conts.numpy(), columns=self.cont_names)
        else:
            cats_df = pd.DataFrame(cats.transpose(1, 0).numpy(), columns=self.cat_names)
            conts_df = pd.DataFrame(
                conts.transpose(1, 0).numpy(), columns=self.cont_names
            )

        ## retrieve meta
        tgt_name = self.target_vocab[tgt]
        meta_file_name = self.sep.join(str(x) for x in meta.numpy())
        file_name = meta_file_name + self.sep + tgt_name + ".csv"
        file_path = self.base_path / file_name
        if not os.path.isfile(file_path):
            ## change target name
            tgt_name = np.delete(self.target_vocab, tgt)
            file_name = meta_file_name + self.sep + tgt_name[0] + ".csv"
            file_path = self.base_path / file_name

        meta_df = read_sequence_play(file_path)
        if (self.max_len is not None) and (type(self.max_len) == int):
            meta_df = meta_df.tail(self.max_len)

        df = pd.concat(
            [meta_df[self.meta_cols].reset_index(drop=True), cats_df, conts_df],
            axis="columns",
        ).reset_index(drop=True)

        return (df, tgt)

# Cell
class Pad_Seq(ItemTransform):
    def encodes(
        self, samples, pad_idx=0, pad_fields=[1, 2], pad_first=False, backwards=False
    ):
        "Function that collect `samples` and adds padding"
        self.pad_idx = pad_idx
        pad_fields = L(pad_fields)
        max_len_l = pad_fields.map(lambda f: max([len(s[f]) for s in samples]))
        if backwards:
            pad_first = not pad_first

        def _f(field_idx, x):
            if field_idx not in pad_fields:
                return x
            idx = pad_fields.items.index(
                field_idx
            )  # TODO: remove items if L.index is fixed
            sl = slice(-len(x), sys.maxsize) if pad_first else slice(0, len(x))
            pad = x.new_zeros((max_len_l[idx] - x.shape[0], x.shape[1])) + pad_idx
            x1 = torch.cat([pad, x] if pad_first else [x, pad], dim=0)
            if backwards:
                x1 = x1.flip(0)
            return retain_type(x1, x)

        return [tuple(map(lambda idxx: _f(*idxx), enumerate(s))) for s in samples]

    def decodes(self, t):
        pad_idx = self.pad_idx if hasattr(self, "pad_idx") else 1

        def _decode(o):
            def _f(tsr):
                return (tsr.shape[0] == 1) and (tsr.tolist()[0] == pad_idx)

            return o[np.where([not _f(torch.unique(t)) for t in torch.unbind(o)])]

        return (t[0], _decode(t[1]), _decode(t[2]), t[3])


pad_seq = Pad_Seq()