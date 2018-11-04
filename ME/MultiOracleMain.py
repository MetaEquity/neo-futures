#!/usr/bin/env python
"""
    NEO Futures Smart Contract Adapted for Meta-Equity 

    Provides a Multi-Oracle Consensus Approach to receiving and confirming external 'facts' onto the Blockchain
    Specifically, it implements a heartbeat approach to getting regular timeseries data

    Author: ~wy
    additions: OmarSalah
    Copyright (c) 2018 Wing Yung Chan

    License: MIT License
"""

from boa.blockchain.vm.System.ExecutionEngine import GetScriptContainer,GetExecutingScriptHash
from boa.blockchain.vm.Neo.Runtime import Log, Notify, GetTrigger, CheckWitness
#from boa.blockchain.vm.Neo.Action import RegisterAction
from boa.blockchain.vm.Neo.Transaction import *
from boa.blockchain.vm.Neo.TriggerType import Application, Verification
from boa.blockchain.vm.Neo.Storage import GetContext, Get, Put, Delete
from boa.blockchain.vm.Neo.Output import GetScriptHash,GetValue,GetAssetId
from boa.code.builtins import concat,take, substr, range, list
from boa.blockchain.vm.Neo.Blockchain import GetHeight, GetHeader
from boa.blockchain.vm.Neo.Header import GetTimestamp, GetNextConsensus
from collections import defaultdict
import weakref
import requests
import json
from time import sleep
from Game import Game

# key prefixes used to add structure to the Context data store
key_prefix_game_type = "game_type::"
key_prefix_game_instance = "game_instance::"
key_prefix_game_instance_prediction = "prediction::"
key_prefix_game_instance_judged = "judged::"
key_prefix_game_instance_max = "max::"
key_prefix_game_instance_index = "index::"
key_prefix_game_instance_count = "count::"
key_prefix_game_instance_correct_count = "correct_count::"
key_prefix_game_instance_oracle = "oracle::"
key_prefix_oracle = "oracle_address::"
key_prefix_agent_available_balance = "agent_available_balance::"
key_prefix_agent_locked_balance = "agent_locked_balance::"



version = "0.0.5.13"


@staticmethod
class Game_rules:
    def __init__():
        Game_rules.starting_timestamp = 1519544672 # 2018-02-25 7:44:32 AM
        Game_rules.collateral_requirement = 5 # 5 NEO-GAS
        Game_rules.timestep = 480 # Deadline in seconds
        Game_rules.owner = b'z]\x16\x10\xad\xce\xc3Q\x1a&Fv\xfa\x1as\xa4E\xa03\xef'
        Game_rules.GAS_ASSET_ID = b'\xe7\x2d\x28\x69\x79\xee\x6c\xb1\xb7\xe6\x5d\xfd\xdf\xb2\xe3\x84\x10\x0b\x8d\x14\x8e\x77\x58\xde\x42\xe4\x16\x8b\x71\x79\x2c\x60'

def Main(operation, args):
    """
    :param operation
    :param args: optional arguments (up to 3 max)
    :return: Object: Bool (success or failure) or Prediction
    """

    Log("NEO-FUTURES - Oracle Judge Smart Contract")
    trigger = GetTrigger()
    arg_len = len(args)
    if arg_len > 5:
        # Only 5 args max
        return False

    if trigger == Verification():
        Log("trigger: Verification")
        is_owner = CheckWitness(Game_rules.owner)
        if is_owner:
            return True
    elif trigger == Application():
        Log("trigger: Application")
        Log(operation)

        # create_new_game {{client}} {{game_type}}
        if operation == 'create_new_game':
            if arg_len != 2:
                Log("Wrong arg length")
                return False
            client_hash = args[0]
            game_type = args[1]
            if not CheckWitness(client_hash):
                Log("Unauthorised hash")
                return False
            return CreateNewGame(client_hash, game_type)

        # submit_prediction {{oracle}} {{game_type}} {{instance_ts}} {{prediction}} {{gas-submission}}
        if operation == 'submit_prediction':
            if arg_len != 5:
                Log("Wrong arg length")
                return False
            oracle = args[0]
            game_type = args[1]
            instance_ts = args[2]
            prediction = args[3]
            gas_submission = args[4]
            if not CheckWitness(oracle):
                Log("Unauthorised hash")
                return False

            # Check instance_ts is correctly timestepped
            if not CheckTimestamp(instance_ts):
                Log("Not correct timestamp format")
                return False
            return client_hash.SubmitPrediction(oracle, game_type, instance_ts, prediction, gas_submission)

        # judge_instance {{game_type}} {{instance_ts}}
        if operation == 'judge_instance':
            if arg_len != 2:
                Log("Wrong arg length")
                return False
            game_type = args[0]
            instance_ts = args[1]
            if client_hash.isGameInstanceJudged(game_type, instance_ts):
                Log("Already Judged")
                return False
            return client_hash.JudgeInstance(game_type, instance_ts)

        # get_prediction {{game_type}} {{instance_ts}}
        if operation == 'get_prediction':
            if arg_len != 2:
                Log("Wrong arg length")
                return False
            game_type = args[0]
            instance_ts = args[1]
            # Try judging to make sure judged
            client_hash.JudgeInstance(game_type, instance_ts)
            return client_hash.GetPrediction(game_type, instance_ts)

        # get_available_balance_oracle {{oracle}}
        if operation == 'get_available_balance_oracle':
            if arg_len != 1:
                Log("Wrong arg length")
                return False
            oracle = args[0]
            return client_hash.GetOracleBalance(oracle)

        # get_correct_oracles_for_instance {{game_type}} {{instance_ts}}
        if operation == 'get_correct_oracles_for_instance':
            if arg_len != 2:
                Log("Wrong arg length")
                return False
            game_type = args[0]
            instance_ts = args[1]
            # Try judging to make sure judged
            client_hash.JudgeInstance(game_type, instance_ts)
            return client_hash.GetCorrectOracleCountForInstance(game_type, instance_ts)

        # debug_get_value {{key}}
        if operation == 'debug_get_value':
            if arg_len != 1:
                Log("Wrong arg length")
                return False
            key = args[0]
            context = GetContext()
            return Get(context, key)
        else:
            Log("unknown op")
            return False
        
def CreateNewGame(client_hash, game_type):
    if client_hash.isGameTypeLive(game_type):
        return "Game is Already Live"
    else:
        client_hash=Game(client_hash,Game_rules.starting_timestamp)
        key = concat(key_prefix_game_type,game_type)
        context = GetContext()
        Put(context, key, client_hash)
    return "Success"
        
class KeepRefs(object):
    __refs__ = defaultdict(list)
    def __init__(self):
        self.__refs__[self.__class__].append(weakref.ref(self))

    @classmethod
    def get_instances(cls):
        for inst_ref in cls.__refs__[cls]:
            inst = inst_ref()
            if inst is not None:
                yield inst
                
 


def CheckTimestamp(timestamp_normalised):
    # Check that T_n is M*timestep + T_0 for some non-negative integer M
    if timestamp_normalised < Game_rules.starting_timestamp:
        return False
    else:
        Mtimestep = timestamp_normalised - Game_rules.starting_timestamp
        mod = Mtimestep % Game_rules.timestep
        if mod == 0:
            return True # Legitimate T_n
        else:
            return False # Not Legitimate T_n

def CheckTiming(timestamp_normalised):
    # Check T_n relative to current TS()
    height = GetHeight()
    hdr = GetHeader(height)
    ts = GetTimestamp(hdr)
    Log(ts)
    t_n_plus_one = timestamp_normalised + Game_rules.timestep
    Log(t_n_plus_one)
    Log(timestamp_normalised)
    if ts > t_n_plus_one:
        return 1 # expired
    elif ts < timestamp_normalised:
        return 2 # too early to submit, ignore
    else:
        return 0 # all good
